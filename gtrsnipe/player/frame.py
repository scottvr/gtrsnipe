"""The ``Frame`` — the contract shared by the timeline, clock, and renderers.

A frame is a snapshot of the fretboard at one moment: which positions are
sounding, for how long, and which slice of the neck the auto-follow viewport is
showing. It carries no I/O and no rendering concerns; it is pure data that every
layer of the player consumes.
"""
import math
from dataclasses import dataclass
from typing import Tuple

from ..core.types import FretPosition


def bar_beat(beat_time: float, beats_per_measure: float) -> Tuple[int, float]:
    """Convert an absolute beat time to (1-indexed bar, 1-indexed beat)."""
    if beats_per_measure <= 0:
        beats_per_measure = 4.0
    measure = math.floor(beat_time / beats_per_measure)
    beat_in = beat_time - measure * beats_per_measure
    return measure + 1, beat_in + 1.0


def _bar_beat_footer(beat_time: float, beats_per_measure: float) -> str:
    """A status line the renderers share: bar/beat plus the raw beat time.

    Because it advances continuously, it doubles as a liveness indicator — a
    moving readout tells the user the player isn't hung during a long rest.
    """
    bar, beat = bar_beat(beat_time, beats_per_measure)
    return f"bar {bar}  beat {beat:.1f}  (t={beat_time:.2f})"


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
        pitches: The sounding MIDI pitches during this frame. Presentation
            layers (renderers) ignore this; the audio sink uses it to emit
            note-on/off. Defaults to empty so diagram-only callers need not set it.
    """
    time: float
    duration: float
    positions: Tuple[FretPosition, ...]
    window: Tuple[int, int]
    pitches: Tuple[int, ...] = ()

    @property
    def window_low(self) -> int:
        return self.window[0]

    @property
    def window_high(self) -> int:
        return self.window[1]
