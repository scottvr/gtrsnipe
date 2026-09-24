"""ASCII fretboard renderer — the MVP render target.

Paints a single :class:`~gtrsnipe.player.frame.Frame` as a text fretboard: one
row per string (highest-pitched on top, matching tab convention), a nut column
for open strings, and a fret-numbered window that the timeline's auto-follow
viewport has already chosen. :meth:`render` returns a string so it is trivially
testable; the app loop is what actually prints it.
"""
import re
from typing import List, Optional

from ...core.config import MapperConfig
from ...core.types import Tuning
from ..frame import Frame

ACTIVE = "O"       # a sounding position
EMPTY = "."        # nothing on this string/fret
NUT = "|"          # the nut, when the open string is silent
CELL_W = 4         # width of each fret column


class AsciiFretboardRenderer:
    """Render frames as an ASCII fretboard grid."""

    def __init__(self, config: Optional[MapperConfig] = None):
        self.config = config or MapperConfig()
        self.labels = self._string_labels()

    def _string_labels(self) -> List[str]:
        """String note-letters (high to low), or 1..n if the tuning is unknown."""
        n = self.config.num_strings
        try:
            names = list(Tuning[self.config.tuning.upper()].value)
        except KeyError:
            names = []
        if len(names) == n:
            # Drop the octave (and any sign) so "E4" -> "E", "Bb3" -> "Bb".
            return [re.sub(r"-?\d+$", "", name) for name in names]
        return [str(i + 1) for i in range(n)]

    def render(self, frame: Frame) -> str:
        """Return the fretboard for ``frame`` as a multi-line string."""
        lo, hi = frame.window
        frets = list(range(lo, hi + 1))
        active = {(p.string, p.fret) for p in frame.positions}
        label_w = max((len(s) for s in self.labels), default=1)

        pad = " " * (label_w + 1)  # label column + nut column
        header = pad + "".join(f"{f:>{CELL_W}}" for f in frets)

        rows = [header]
        for s, label in enumerate(self.labels):
            nut = ACTIVE if (s, 0) in active else NUT
            cells = "".join(
                f"{(ACTIVE if (s, f) in active else EMPTY):>{CELL_W}}"
                for f in frets
            )
            rows.append(f"{label:>{label_w}}{nut}{cells}")
        return "\n".join(rows)

    def render_with_status(self, frame: Frame, index: int, total: int) -> str:
        """Fretboard plus a one-line status footer (position/time)."""
        board = self.render(frame)
        footer = (f"[{index + 1}/{total}]  beat {frame.time:.2f}  "
                  f"frets {frame.window[0]}-{frame.window[1]}")
        return f"{board}\n{footer}"
