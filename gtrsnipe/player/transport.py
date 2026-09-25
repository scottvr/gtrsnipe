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

Runtime controls (media-player + pager convention):

* ``space`` — pause / resume (toggle)
* ``.`` / ``,`` — step forward / back (while paused)
* ``left`` / ``right`` — seek back / forward one bar
* ``[`` / ``]`` — tempo down / up
* ``g`` / ``home`` / ``end`` — jump to start / start / end
* ``h`` / ``?`` — help overlay
* ``q`` — quit

The Transport is decoupled from I/O via a **driver** (``render(beat)``,
``fire(frames)``, ``silence()``, ``read_key(blocking)``, and optionally
``show(text)`` for the help overlay), so it is fully testable with an injected
clock + scripted keys.
"""
import bisect
import time
from typing import List, Optional, Sequence

from .frame import Frame

INF = float("inf")
MIN_TEMPO = 20.0
MAX_TEMPO = 400.0
TEMPO_STEP = 1.12  # multiplicative tempo nudge per keypress

HELP_TEXT = """\
gtrsnipe player — keys

  space    pause / resume
  . / ,    step forward / back   (while paused)
  <- / ->  seek back / forward one bar
  [ / ]    tempo down / up
  g / end  jump to start / end
  h / ?    this help
  q        quit

(space resumes)"""


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
                 beats_per_measure: float = 4.0,
                 now=time.monotonic, sleep=time.sleep):
        self.timeline = list(timeline)
        self.tempo = tempo_bpm
        self.fps = fps if fps and fps > 0 else 12.0
        self.paused = not playing
        self.beats_per_measure = beats_per_measure if beats_per_measure > 0 else 4.0
        self._now = now
        self._sleep = sleep
        self._times = [f.time for f in self.timeline]
        self.start = self.timeline[0].time if self.timeline else 0.0
        self.beat_time = self.start
        self.end = (self.timeline[-1].time + max(self.timeline[-1].duration, 0.0)
                    if self.timeline else 0.0)
        self._onset_i = 0        # index of the next un-fired frame
        self._quit = False
        self._anchor = 0.0
        self._anchor_beat = self.start

    # -- helpers ------------------------------------------------------------

    @property
    def _fps_beats(self) -> float:
        return self.tempo / (60.0 * self.fps)

    def _reanchor(self) -> None:
        self._anchor = self._now()
        self._anchor_beat = self.beat_time

    def _next_onset_time(self) -> float:
        return (self._times[self._onset_i] if self._onset_i < len(self._times) else INF)

    def _fire_due(self, driver) -> None:
        due = []
        while (self._onset_i < len(self.timeline)
               and self._times[self._onset_i] <= self.beat_time + 1e-9):
            due.append(self.timeline[self._onset_i])
            self._onset_i += 1
        if due:
            driver.fire(due)

    def _held_frame(self) -> Optional[Frame]:
        i = bisect.bisect_right(self._times, self.beat_time + 1e-9) - 1
        return self.timeline[i] if i >= 0 else None

    def _fire_held(self, driver) -> None:
        held = self._held_frame()
        if held is not None:
            driver.fire([held])

    # -- navigation ---------------------------------------------------------

    def _seek_to(self, beat: float, driver) -> None:
        self.beat_time = max(self.start, min(beat, self.end))
        # future onsets = frames strictly after the landing beat
        self._onset_i = bisect.bisect_right(self._times, self.beat_time + 1e-9)
        driver.silence()
        self._reanchor()
        driver.render(self.beat_time)
        if self.paused:
            self._fire_held(driver)  # audible scrub feedback while paused

    def _adjust_tempo(self, factor: float, driver) -> None:
        self.tempo = max(MIN_TEMPO, min(self.tempo * factor, MAX_TEMPO))
        self._reanchor()
        driver.render(self.beat_time)

    def _step(self, driver, direction: int = 1) -> None:
        """Advance/retreat one frame, fire+render it, remain paused."""
        if direction > 0:
            if self._onset_i >= len(self.timeline):
                self._quit = True
                return
            self.beat_time = self._times[self._onset_i]
            self._fire_due(driver)
        else:
            i = bisect.bisect_left(self._times, self.beat_time - 1e-9) - 1
            if i < 0:
                self.beat_time = self.start
            else:
                self.beat_time = self._times[i]
            self._onset_i = bisect.bisect_right(self._times, self.beat_time + 1e-9)
            driver.silence()
            self._fire_held(driver)
        driver.render(self.beat_time)

    def _resume(self, driver) -> None:
        self.paused = False
        self._fire_held(driver)  # re-articulate the held frame on resume
        self._reanchor()

    # -- key handling -------------------------------------------------------

    def _handle_key(self, key: Optional[str], driver) -> None:
        if key is None:
            if self.paused:      # exhausted blocking input -> stop
                self._quit = True
            return
        if key == "<resize>":
            driver.render(self.beat_time)
            return
        k = key.lower()
        if k == "q":
            self._quit = True
        elif k in (" ", "\n", "\r", "p"):
            # Toggle play/pause. Resuming just clears the flag; the run loop's
            # paused branch then calls _resume (re-articulate + re-anchor).
            if self.paused:
                self.paused = False
            else:
                self.paused = True
                driver.silence()
        elif k == "." and self.paused:
            self._step(driver, +1)
        elif k == "," and self.paused:
            self._step(driver, -1)
        elif k == "left":
            self._seek_to(self.beat_time - self.beats_per_measure, driver)
        elif k == "right":
            self._seek_to(self.beat_time + self.beats_per_measure, driver)
        elif k == "[":
            self._adjust_tempo(1.0 / TEMPO_STEP, driver)
        elif k == "]":
            self._adjust_tempo(TEMPO_STEP, driver)
        elif k in ("g", "home"):
            self._seek_to(self.start, driver)
        elif k == "end":
            self._seek_to(self.end, driver)
        elif k in ("h", "?"):
            # Pause so the overlay persists (a live render would repaint over it).
            self.paused = True
            driver.silence()
            if hasattr(driver, "show"):
                driver.show(HELP_TEXT)

    # -- main loop ----------------------------------------------------------

    def run(self, driver) -> None:
        if not self.timeline:
            return
        driver.render(self.beat_time)
        self._fire_due(driver)  # sound the first frame
        self._reanchor()

        while not self._quit and self.beat_time < self.end - 1e-9:
            if self.paused:
                self._handle_key(driver.read_key(True), driver)
                if not self.paused and not self._quit:
                    self._resume(driver)
                continue

            t = min(self._next_onset_time(), self.beat_time + self._fps_beats, self.end)
            target_wall = self._anchor + _beats_to_seconds(t - self._anchor_beat, self.tempo)
            dt = target_wall - self._now()
            if dt > 0:
                self._sleep(dt)

            key = driver.read_key(False)
            if key is not None:
                self._handle_key(key, driver)
                if self._quit:
                    break
                # Re-evaluate from the new state after ANY key (a seek/jump/tempo
                # handler moved beat_time/_onset_i/anchor); do NOT fall through to
                # `self.beat_time = t`, which was computed before the key.
                continue

            self.beat_time = t
            self._fire_due(driver)
            driver.render(self.beat_time)

        if not self._quit:
            self.beat_time = self.end
            driver.render(self.beat_time)
