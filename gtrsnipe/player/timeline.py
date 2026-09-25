"""Build a timeline of :class:`Frame`s from fretboard-mapped events.

This is the load-bearing, pure layer of the player. It takes the events a
:class:`~gtrsnipe.guitar.mapper.GuitarMapper` has already assigned strings and
frets to, groups them by onset (the same quantization the mapper/tab generator
use), and computes the auto-follow viewport that tracks where the playing is.

No timing, no I/O, no rendering — just Song-shaped data in, ``Frame`` list out.
"""
from itertools import groupby
from typing import List, Optional, Sequence

from ..core.config import MapperConfig
from ..core.types import FretPosition, MusicalEvent, Song
from .frame import Frame

# Frets visible in the auto-follow window. A guitarist's hand covers ~4 frets;
# 5 gives a little breathing room and matches the user's "5-fret window".
DEFAULT_WINDOW_SIZE = 5


class TimelineBuilder:
    """Turns mapped :class:`MusicalEvent`s into a list of :class:`Frame`s."""

    def __init__(self, config: Optional[MapperConfig] = None,
                 window_size: int = DEFAULT_WINDOW_SIZE):
        self.config = config or MapperConfig()
        if window_size < 1:
            raise ValueError("window_size must be >= 1")
        self.window_size = window_size

    # -- public API ---------------------------------------------------------

    def build(self, mapped_events: Sequence[MusicalEvent]) -> List[Frame]:
        """Build frames from a flat list of already-mapped events.

        Events without a string/fret assignment (dead-ends the mapper could not
        place) are skipped. Frames are ordered by onset; each frame's duration
        spans the gap to the next frame so the frames tile the timeline.
        """
        events = [e for e in mapped_events
                  if e.string is not None and e.fret is not None]
        if not events:
            return []

        qr = self.config.quantization_resolution
        quantize = lambda t: round(t / qr) * qr
        events.sort(key=lambda e: e.time)

        frames: List[Frame] = []
        group_durations: List[float] = []
        for gtime, group in groupby(events, key=lambda e: quantize(e.time)):
            group = list(group)
            positions = tuple(sorted(
                {FretPosition(e.string, e.fret) for e in group}
            ))
            pitches = tuple(sorted({e.pitch for e in group}))
            frames.append(Frame(time=gtime, duration=0.0,
                                positions=positions,
                                window=(1, self.window_size),
                                pitches=pitches))
            # Fallback duration for the final frame: the longest note in the
            # group (never below the quantization grid).
            group_durations.append(max((e.duration for e in group), default=qr))

        self._assign_durations(frames, group_durations, qr)
        self._assign_windows(frames)
        return frames

    def build_from_song(self, song: Song) -> List[Frame]:
        """Build frames from a mapped Song, merging all tracks onto one neck."""
        events: List[MusicalEvent] = []
        for track in song.tracks:
            events.extend(track.events)
        return self.build(events)

    # -- internals ----------------------------------------------------------

    @staticmethod
    def _assign_durations(frames: List[Frame], group_durations: List[float],
                          qr: float) -> None:
        """Duration of a frame = gap to the next onset; last = its note length."""
        for i in range(len(frames) - 1):
            gap = frames[i + 1].time - frames[i].time
            frames[i].duration = gap if gap > 0 else qr
        if frames:
            frames[-1].duration = max(group_durations[-1], qr)

    def _assign_windows(self, frames: List[Frame]) -> None:
        """Slide a fixed-width window to keep fretted notes in view.

        Hysteresis: the window only moves when a note falls outside it, and then
        by the minimum needed to re-contain it. A brief high note that exceeds
        the window width anchors the window at that note's fret rather than
        thrashing. Open strings (fret 0) never move the window.
        """
        size = self.window_size
        lo = 1
        hi = lo + size - 1
        for frame in frames:
            fretted = [p.fret for p in frame.positions if p.fret > 0]
            if fretted:
                fmin, fmax = min(fretted), max(fretted)
                if fmax - fmin >= size:
                    lo = fmin            # wider than the window: anchor low
                elif fmin < lo:
                    lo = fmin            # slid off the bottom: follow down
                elif fmax > hi:
                    lo = fmax - size + 1  # slid off the top: follow up
                hi = lo + size - 1
            frame.window = (lo, hi)
