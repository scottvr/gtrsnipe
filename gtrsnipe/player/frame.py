"""The ``Frame`` — the contract shared by the timeline, clock, and renderers.

A frame is a snapshot of the fretboard at one moment: which positions are
sounding, for how long, and which slice of the neck the auto-follow viewport is
showing. It carries no I/O and no rendering concerns; it is pure data that every
layer of the player consumes.
"""
from dataclasses import dataclass
from typing import Tuple

from ..core.types import FretPosition


@dataclass
class Frame:
    """Fretboard state at a single instant.

    Attributes:
        time: Onset of this frame, in beats.
        duration: Beats until the next frame's onset (the last frame uses its
            own note duration). This is what a real-time clock converts to
            wall-clock seconds; a metronome clock ignores it.
        positions: The fret positions sounding during this frame. Deduplicated
            and sorted (by string, then fret) for deterministic rendering.
        window: The inclusive ``(low_fret, high_fret)`` slice of the neck the
            auto-follow viewport is showing. Open strings (fret 0) are always
            rendered regardless of the window, so this range covers only
            *fretted* notes and never dips below fret 1.
    """
    time: float
    duration: float
    positions: Tuple[FretPosition, ...]
    window: Tuple[int, int]

    @property
    def window_low(self) -> int:
        return self.window[0]

    @property
    def window_high(self) -> int:
        return self.window[1]
