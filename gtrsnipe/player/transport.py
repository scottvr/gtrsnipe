"""The Transport — an event-driven playback clock (replaces ``clock.py``).

A single Transport drives a run of timed targets. Its loop advances to *whichever
comes first* — the next note onset or the next scheduled redraw — so:

* **Audio fires at true onset times**, independent of the display refresh rate
  (`fps`); no note-timing jitter quantized to the frame rate.
* **Rendering is throttled to `fps`** and keeps moving during long rests (the
  playhead scrolls even with no notes), so the display never looks hung.
* Wall-clock is **anchored** (via an injected monotonic `now`) so cumulative
  sleep error doesn't drift the tempo.

`step` vs `tempo` is just the initial state (`paused` vs `playing`); `space`
toggles at runtime. Metronome is not a Transport mode — it is a re-timed timeline
(:func:`metronome_timeline`) played at tempo.

The Transport is decoupled from I/O via a **driver** with four methods
(``render(beat)``, ``fire(frames)``, ``silence()``, ``read_key(blocking)``), so
it is fully testable with an injected clock + scripted keys.
"""
import time
from typing import List, Optional, Sequence

from .frame import Frame

INF = float("inf")


def _beats_to_seconds(beats: float, tempo_bpm: float) -> float:
    if tempo_bpm <= 0:
        raise ValueError("tempo must be positive")
    return beats * (60.0 / tempo_bpm)


def metronome_timeline(timeline: Sequence[Frame], grid_beats: float = 0.5) -> List[Frame]:
    """Re-time a timeline to an even grid: frame i at ``i*grid_beats`` for a
    steady practice metronome. Positions/windows/pitches are preserved."""
    if grid_beats <= 0:
        raise ValueError("grid_beats must be positive")
    out: List[Frame] = []
    for i, f in enumerate(timeline):
        out.append(Frame(time=i * grid_beats, duration=grid_beats,
                         positions=f.positions, window=f.window, pitches=f.pitches))
    return out


class Transport:
    """Event-driven playback over a timeline, driving one I/O driver."""

    def __init__(self, timeline: Sequence[Frame], tempo_bpm: float, *,
                 fps: float = 12.0, playing: bool = True,
                 now=time.monotonic, sleep=time.sleep):
        self.timeline = list(timeline)
        self.tempo = tempo_bpm
        self.fps = fps if fps and fps > 0 else 12.0
        self.paused = not playing
        self._now = now
        self._sleep = sleep
        self.beat_time = self.timeline[0].time if self.timeline else 0.0
        self.end = (self.timeline[-1].time + max(self.timeline[-1].duration, 0.0)
                    if self.timeline else 0.0)
        self._onset_i = 0        # index of the next un-fired frame
        self._quit = False

    # -- helpers ------------------------------------------------------------

    @property
    def _fps_beats(self) -> float:
        return self.tempo / (60.0 * self.fps)

    def _next_onset_time(self) -> float:
        return (self.timeline[self._onset_i].time
                if self._onset_i < len(self.timeline) else INF)

    def _fire_due(self, driver) -> None:
        """Fire every onset frame at or before the current beat."""
        due = []
        while (self._onset_i < len(self.timeline)
               and self.timeline[self._onset_i].time <= self.beat_time + 1e-9):
            due.append(self.timeline[self._onset_i])
            self._onset_i += 1
        if due:
            driver.fire(due)

    def _held_frame(self) -> Optional[Frame]:
        """The frame sounding at the current beat (last onset at/before it)."""
        held = None
        for f in self.timeline:
            if f.time <= self.beat_time + 1e-9:
                held = f
            else:
                break
        return held

    # -- key handling (P1: pause/step/quit; extended in P4) -----------------

    def _handle_key(self, key: Optional[str], driver) -> None:
        if key is None:
            # Exhausted/None from a blocking read means "no more input" -> stop.
            if self.paused:
                self._quit = True
            return
        if key == "<resize>":
            driver.render(self.beat_time)  # re-layout at the new terminal size
            return
        k = key.lower()
        if k == "q":
            self._quit = True
        elif k in (" ", "\n", "\r", "p"):
            if self.paused:
                # step one frame forward, stay paused
                self._step(driver)
            else:
                self.paused = True
                driver.silence()
        elif k == ".":
            if self.paused:
                self._step(driver)

    def _step(self, driver) -> None:
        """Advance to the next onset (frame), fire+render it, remain paused."""
        if self._onset_i >= len(self.timeline):
            self._quit = True
            return
        self.beat_time = self.timeline[self._onset_i].time
        self._fire_due(driver)
        driver.render(self.beat_time)

    def _resume(self, driver) -> None:
        self.paused = False
        held = self._held_frame()
        if held is not None:
            driver.fire([held])  # re-articulate the held frame on resume

    # -- main loop ----------------------------------------------------------

    def run(self, driver) -> None:
        if not self.timeline:
            return
        driver.render(self.beat_time)
        self._fire_due(driver)  # sound the first frame

        anchor = self._now()
        anchor_beat = self.beat_time

        while not self._quit and self.beat_time < self.end - 1e-9:
            if self.paused:
                self._handle_key(driver_key := driver.read_key(True), driver)
                if not self.paused and not self._quit:
                    self._resume(driver)
                    anchor, anchor_beat = self._now(), self.beat_time
                continue

            t = min(self._next_onset_time(), self.beat_time + self._fps_beats, self.end)
            target_wall = anchor + _beats_to_seconds(t - anchor_beat, self.tempo)
            dt = target_wall - self._now()
            if dt > 0:
                self._sleep(dt)

            key = driver.read_key(False)
            if key is not None:
                self._handle_key(key, driver)
                if self._quit:
                    break
                if self.paused:
                    continue  # entered pause; loop will block on next iteration

            self.beat_time = t
            self._fire_due(driver)
            driver.render(self.beat_time)

        if not self._quit:
            self.beat_time = self.end
            driver.render(self.beat_time)
