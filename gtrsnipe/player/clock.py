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
    """At-tempo playback: each frame lasts its own duration in beats."""

    def schedule(self, timeline: Sequence[Frame], tempo_bpm: float) -> Schedule:
        out: Schedule = []
        n = len(timeline)
        for i, frame in enumerate(timeline):
            delay = None if i == n - 1 else _beats_to_seconds(frame.duration, tempo_bpm)
            out.append((frame, delay))
        return out


class MetronomeClock:
    """Steady grid: every frame gets the same interval, real durations ignored.

    ``grid_beats`` is the metronomic step (default 0.5 = an eighth note in 4/4).
    """

    def __init__(self, grid_beats: float = 0.5):
        if grid_beats <= 0:
            raise ValueError("grid_beats must be positive")
        self.grid_beats = grid_beats

    def schedule(self, timeline: Sequence[Frame], tempo_bpm: float) -> Schedule:
        interval = _beats_to_seconds(self.grid_beats, tempo_bpm)
        out: Schedule = []
        n = len(timeline)
        for i, frame in enumerate(timeline):
            delay = None if i == n - 1 else interval
            out.append((frame, delay))
        return out


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
