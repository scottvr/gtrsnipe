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
import heapq
import itertools
import time
from typing import List, Optional, Sequence

from .frame import Frame

INF = float("inf")
MIN_TEMPO = 20.0
MAX_TEMPO = 400.0
TEMPO_STEP = 1.12  # multiplicative tempo nudge per keypress

HELP_TEXT = """\
gtrsnipe player — keys

  space    pause / resume   (also enter, p)
  . / ,    step forward / back   (while paused)
  <- / ->  seek back / forward one bar
  [ / ]    tempo down / up
  g / end  jump to start / end   (also home)
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
        t = i * grid_beats
        out.append(Frame(time=t, duration=grid_beats,
                         positions=f.positions, window=f.window, pitches=f.pitches,
                         ends=tuple(t + grid_beats for _ in f.pitches) if f.ends else ()))
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
        # A note written longer than the rest of the piece still gets to finish.
        self.end = max([self.end] + [e for f in self.timeline for e in f.ends])
        # Note releases (when frames carry note ends and the driver can release):
        # a heap of (beat, seq, pitch, generation). Re-striking a pitch bumps its
        # generation, so a stale release can't cut the new note short.
        self._releases: list = []
        self._gen: dict = {}
        self._seq = itertools.count()
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

    def _next_release_time(self) -> float:
        return self._releases[0][0] if self._releases else INF

    def _schedule(self, frames, driver) -> None:
        if not hasattr(driver, "release"):
            return
        for f in frames:
            for p, end in zip(f.pitches, f.ends):
                g = self._gen[p] = self._gen.get(p, 0) + 1
                heapq.heappush(self._releases, (end, next(self._seq), p, g))

    def _release_due(self, driver) -> None:
        done = []
        while self._releases and self._releases[0][0] <= self.beat_time + 1e-9:
            _, _, p, g = heapq.heappop(self._releases)
            if self._gen.get(p) == g:
                done.append(p)
        if done:
            driver.release(done)

    def _silence(self, driver) -> None:
        driver.silence()
        self._releases.clear()

    def _fire_due(self, driver) -> None:
        due = []
        while (self._onset_i < len(self.timeline)
               and self._times[self._onset_i] <= self.beat_time + 1e-9):
            due.append(self.timeline[self._onset_i])
            self._onset_i += 1
        if due:
            driver.fire(due)
            self._schedule(due, driver)

    def _held_frame(self) -> Optional[Frame]:
        i = bisect.bisect_right(self._times, self.beat_time + 1e-9) - 1
        return self.timeline[i] if i >= 0 else None

    def _fire_held(self, driver) -> None:
        held = self._held_frame()
        if held is None:
            return
        if held.ends:                       # only the notes still ringing now
            keep = [(p, e) for p, e in zip(held.pitches, held.ends)
                    if e > self.beat_time + 1e-9]
            if not keep:
                return                      # paused in a rest: stay silent
            held = Frame(time=held.time, duration=held.duration, positions=held.positions,
                         window=held.window, pitches=tuple(p for p, _ in keep),
                         ends=tuple(e for _, e in keep))
        driver.fire([held])
        self._schedule([held], driver)

    # -- navigation ---------------------------------------------------------

    def _seek_to(self, beat: float, driver) -> None:
        self.beat_time = max(self.start, min(beat, self.end))
        # future onsets = frames strictly after the landing beat
        self._onset_i = bisect.bisect_right(self._times, self.beat_time + 1e-9)
        self._silence(driver)
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
            self._silence(driver)    # stepping: each frame sounds on its own
            self._fire_due(driver)
        else:
            i = bisect.bisect_left(self._times, self.beat_time - 1e-9) - 1
            if i < 0:
                self.beat_time = self.start
            else:
                self.beat_time = self._times[i]
            self._onset_i = bisect.bisect_right(self._times, self.beat_time + 1e-9)
            self._silence(driver)
            self._fire_held(driver)
        driver.render(self.beat_time)

    def _resume(self, driver) -> None:
        self.paused = False
        self._fire_held(driver)  # re-articulate the held frame on resume
        self._reanchor()

    # -- key handling -------------------------------------------------------

    def _handle_key(self, key: Optional[str], driver) -> bool:
        """Handle a key; return True if it acted (so the playing loop re-evaluates
        rather than falling through to `beat_time = t`). No-op/unbound keys return
        False so a burst of them doesn't stall the playhead."""
        if key is None:
            if self.paused:      # exhausted blocking input -> stop
                self._quit = True
            return True
        if key == "<resize>":
            driver.render(self.beat_time)
            return True
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
                self._silence(driver)
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
            self._silence(driver)
            if hasattr(driver, "show"):
                driver.show(HELP_TEXT)
        else:
            return False   # unbound key: ignore, let the playhead keep advancing
        return True

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

            t = min(self._next_onset_time(), self._next_release_time(),
                    self.beat_time + self._fps_beats, self.end)
            target_wall = self._anchor + _beats_to_seconds(t - self._anchor_beat, self.tempo)
            dt = target_wall - self._now()
            if dt > 0:
                self._sleep(dt)

            key = driver.read_key(False)
            if key is not None:
                acted = self._handle_key(key, driver)
                if self._quit:
                    break
                if acted:
                    # A seek/jump/tempo/pause handler moved state; re-evaluate
                    # rather than falling through to `self.beat_time = t` (stale).
                    continue
                # No-op/unbound key: fall through so the playhead keeps advancing
                # (a burst of such keys must not stall it).

            self.beat_time = t
            self._release_due(driver)
            self._fire_due(driver)
            driver.render(self.beat_time)

        if not self._quit:
            self.beat_time = self.end
            driver.render(self.beat_time)
