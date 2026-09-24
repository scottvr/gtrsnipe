"""ASCII fretboard renderer — the MVP render target.

Paints a single :class:`~gtrsnipe.player.frame.Frame` as a text fretboard. The
board's *shape* is a presentation choice made here; the timeline and clock know
nothing about it:

* ``orientation="horizontal"`` (default) — one row per string (highest-pitched
  on top, tab convention), frets as columns, a nut column for open strings.
* ``orientation="vertical"`` — frets run top-to-bottom (lowest fret at the top),
  strings as columns, chord-diagram style.
* ``handed="right"`` (default) / ``"left"`` — mirrors the neck for left-handed
  players (horizontal: nut moves to the right; vertical: string order flips).

:meth:`render` returns a string so it is trivially testable; the app loop prints
it.
"""
import re
from typing import List, Optional

from ...core.config import MapperConfig
from ...core.types import Tuning
from ..frame import Frame

ACTIVE = "O"       # a sounding position
EMPTY = "."        # nothing on this string/fret
NUT = "|"          # the nut, when the open string is silent
CELL_W = 4         # width of each grid column
GUTTER_W = 3       # width of the fret-number gutter (vertical layout)

ORIENTATIONS = ("horizontal", "vertical")
HANDS = ("right", "left")


class AsciiFretboardRenderer:
    """Render frames as an ASCII fretboard grid."""

    def __init__(self, config: Optional[MapperConfig] = None,
                 orientation: str = "horizontal", handed: str = "right"):
        if orientation not in ORIENTATIONS:
            raise ValueError(f"orientation must be one of {ORIENTATIONS}")
        if handed not in HANDS:
            raise ValueError(f"handed must be one of {HANDS}")
        self.config = config or MapperConfig()
        self.orientation = orientation
        self.handed = handed
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
        active = {(p.string, p.fret) for p in frame.positions}
        if self.orientation == "vertical":
            return self._render_vertical(lo, hi, active)
        return self._render_horizontal(lo, hi, active)

    # -- horizontal ---------------------------------------------------------

    def _render_horizontal(self, lo: int, hi: int, active: set) -> str:
        """Strings as rows (high on top); frets as columns.

        Right-handed: nut on the left, frets ascend rightward.
        Left-handed: mirror — nut on the right, frets ascend leftward.
        """
        frets = list(range(lo, hi + 1))
        if self.handed == "left":
            frets = frets[::-1]
        label_w = max((len(s) for s in self.labels), default=1)

        fret_cols = "".join(f"{f:>{CELL_W}}" for f in frets)
        rows: List[str] = []
        if self.handed == "left":
            # label | cells | nut   (nut on the right)
            rows.append(" " * label_w + fret_cols + " ")
            for s, label in enumerate(self.labels):
                nut = ACTIVE if (s, 0) in active else NUT
                cells = self._cells(s, frets, active)
                rows.append(f"{label:>{label_w}}{cells}{nut}")
        else:
            # label | nut | cells   (nut on the left)
            rows.append(" " * (label_w + 1) + fret_cols)
            for s, label in enumerate(self.labels):
                nut = ACTIVE if (s, 0) in active else NUT
                cells = self._cells(s, frets, active)
                rows.append(f"{label:>{label_w}}{nut}{cells}")
        return "\n".join(rows)

    @staticmethod
    def _cells(string: int, frets: List[int], active: set) -> str:
        return "".join(
            f"{(ACTIVE if (string, f) in active else EMPTY):>{CELL_W}}"
            for f in frets
        )

    # -- vertical -----------------------------------------------------------

    def _render_vertical(self, lo: int, hi: int, active: set) -> str:
        """Frets as rows (lowest at top); strings as columns (chord-diagram).

        Right-handed: low string on the left, high string on the right.
        Left-handed: mirror — high string on the left.
        """
        n = self.config.num_strings
        if self.handed == "left":
            order = list(range(n))            # high (0) left -> low right
        else:
            order = list(range(n - 1, -1, -1))  # low left -> high (0) right
        labels = [self.labels[s] for s in order]

        header = " " * GUTTER_W + "".join(f"{lab:>{CELL_W}}" for lab in labels)
        open_row = f"{'o':>{GUTTER_W}}" + "".join(
            f"{(ACTIVE if (s, 0) in active else EMPTY):>{CELL_W}}" for s in order
        )
        width = GUTTER_W + CELL_W * len(order)
        # A solid nut line when the window touches fret 1, else a light divider.
        divider = ("=" if lo == 1 else "-") * width

        rows = [header, open_row, divider]
        for f in range(lo, hi + 1):
            cells = "".join(
                f"{(ACTIVE if (s, f) in active else EMPTY):>{CELL_W}}"
                for s in order
            )
            rows.append(f"{f:>{GUTTER_W}}{cells}")
        return "\n".join(rows)

    # -- status footer ------------------------------------------------------

    def render_with_status(self, frame: Frame, index: int, total: int) -> str:
        """Fretboard plus a one-line status footer (position/time)."""
        board = self.render(frame)
        footer = (f"[{index + 1}/{total}]  beat {frame.time:.2f}  "
                  f"frets {frame.window[0]}-{frame.window[1]}")
        return f"{board}\n{footer}"
