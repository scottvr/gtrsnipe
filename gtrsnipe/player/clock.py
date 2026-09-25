"""Clocks decide *when* the player advances from one frame to the next.

A clock is pure: given a timeline and a tempo, :meth:`Clock.schedule` returns
``(frame, delay)`` pairs, where ``delay`` is the wall-clock seconds to wait
before the *next* frame (``None`` means "wait for the user to advance"). The app
loop owns the actual sleeping / keypress reading, which keeps the timing policy
here fully unit-testable.

Three policies:

* :class:`RealtimeClock` — honour each frame's real duration (at-tempo playback).
* :class:`MetronomeClock` — give every frame the same fixed grid interval,
  ignoring real note lengths (a steady practice metronome).
* :class:`StepClock` — never auto-advance; the user steps with the spacebar.
"""
from typing import List, Optional, Sequence, Tuple

from .frame import Frame

Schedule = List[Tuple[Frame, Optional[float]]]


def _beats_to_seconds(beats: float, tempo_bpm: float) -> float:
    """Convert a duration in beats to seconds at a given tempo (BPM)."""
    if tempo_bpm <= 0:
        raise ValueError("tempo must be positive")
    return beats * (60.0 / tempo_bpm)


class RealtimeClock:
    """At-tempo playback: the player dwells on each frame for its own duration.

    ``delay`` is the *dwell* time on a frame (its note length), including the
    final frame — so the last note is held for its duration rather than being
    cut off the instant playback ends.
    """

    def schedule(self, timeline: Sequence[Frame], tempo_bpm: float) -> Schedule:
        return [(f, _beats_to_seconds(f.duration, tempo_bpm)) for f in timeline]


class MetronomeClock:
    """Steady grid: the player dwells on every frame for the same interval.

    ``grid_beats`` is the metronomic step (default 0.5 = an eighth note in 4/4).
    The final frame gets a dwell too, so its note isn't cut off.
    """

    def __init__(self, grid_beats: float = 0.5):
        if grid_beats <= 0:
            raise ValueError("grid_beats must be positive")
        self.grid_beats = grid_beats

    def schedule(self, timeline: Sequence[Frame], tempo_bpm: float) -> Schedule:
        interval = _beats_to_seconds(self.grid_beats, tempo_bpm)
        return [(f, interval) for f in timeline]


class StepClock:
    """Manual advance: the user drives every transition (spacebar)."""

    def schedule(self, timeline: Sequence[Frame], tempo_bpm: float) -> Schedule:
        return [(frame, None) for frame in timeline]


CLOCKS = {
    "tempo": RealtimeClock,
    "metronome": MetronomeClock,
    "step": StepClock,
}


def make_clock(name: str, grid_beats: float = 0.5):
    """Factory used by the CLI: map a ``--clock`` choice to a clock instance."""
    if name not in CLOCKS:
        raise ValueError(f"unknown clock {name!r}; choose from {sorted(CLOCKS)}")
    if name == "metronome":
        return MetronomeClock(grid_beats=grid_beats)
    return CLOCKS[name]()
