"""Horizontally-scrolling ASCII tab — a "7-bit terminal Guitar Hero".

Unlike the fretboard renderer (which paints a single instant), this renderer
shows a *time window* of the whole piece: a tab staff that scrolls right-to-left
under a fixed playhead as the clock advances. Notes flow in from the right,
cross the playhead at their moment, and exit left.

It consumes the whole timeline (not one frame), so it exposes the uniform
``paint(timeline, index)`` entry point the player loop calls.
"""
import re
from typing import List, Optional, Sequence

from ...core.config import MapperConfig
from ...core.types import Tuning
from ..frame import Frame, _bar_beat_footer, total_bars

DEFAULT_WIDTH = 48          # viewport columns (excluding the string-label gutter)
DEFAULT_COLS_PER_BEAT = 4   # horizontal density: chars per quarter-note beat
PLAYHEAD = "|"
FILL = "-"


class ScrollingTabRenderer:
    """Render a scrolling tab viewport of a timeline at a given playhead index."""

    def __init__(self, config: Optional[MapperConfig] = None,
                 width: int = DEFAULT_WIDTH,
                 cols_per_beat: int = DEFAULT_COLS_PER_BEAT):
        if width < 4:
            raise ValueError("width must be >= 4")
        if cols_per_beat < 1:
            raise ValueError("cols_per_beat must be >= 1")
        self.config = config or MapperConfig()
        self.width = width
        self.cols_per_beat = cols_per_beat
        self.beats_per_measure = 4.0   # set by the player from the song's meter
        self.labels = self._string_labels()
        self._strip: Optional[List[List[str]]] = None
        self._strip_key = None

    def _string_labels(self) -> List[str]:
        n = self.config.num_strings
        if getattr(self.config, "custom_tuning", None):
            names = list(self.config.custom_tuning)
        else:
            try:
                names = list(Tuning[self.config.tuning.upper()].value)
            except KeyError:
                names = []
        if len(names) == n:
            return [re.sub(r"-?\d+$", "", name) for name in names]
        return [str(i + 1) for i in range(n)]

    def _column_of(self, beat: float) -> int:
        return round(beat * self.cols_per_beat)

    def _build_strip(self, timeline: Sequence[Frame]) -> List[List[str]]:
        """Lay the whole piece out as one long unwrapped tab, one row per string.

        Cached per timeline identity so repeated frames during playback don't
        rebuild it.
        """
        key = (id(timeline), len(timeline))
        if self._strip is not None and self._strip_key == key:
            return self._strip

        n = len(self.labels)
        if not timeline:
            self._strip, self._strip_key = [[] for _ in range(n)], key
            return self._strip

        last_col = max(self._column_of(f.time) for f in timeline)
        length = last_col + 4  # margin for multi-digit frets at the end
        strip = [[FILL] * length for _ in range(n)]
        # Earliest free column per string, so a fret's digits never overwrite an
        # earlier note's digits (which produced phantom frets like 12+3 -> "13").
        # Dense high-fret runs drift a column right rather than corrupt a number.
        next_free = [0] * n
        for frame in timeline:  # timeline is time-sorted
            base = self._column_of(frame.time)
            for pos in frame.positions:
                s = pos.string
                if not (0 <= s < n):
                    continue
                text = str(pos.fret)
                col = max(base, next_free[s])
                end = col + len(text)
                if end > len(strip[s]):
                    strip[s].extend([FILL] * (end - len(strip[s])))
                for k, ch in enumerate(text):
                    strip[s][col + k] = ch
                next_free[s] = end + 1  # keep at least one gap before the next
        self._strip, self._strip_key = strip, key
        return strip

    def paint(self, timeline: Sequence[Frame], index: int) -> str:
        """Uniform player entry point: viewport at frame ``index``'s time."""
        if not timeline:
            return "(empty)"
        index = max(0, min(index, len(timeline) - 1))
        return self.render_at(timeline, timeline[index].time)

    # Back-compat alias for older index-based callers/tests.
    def render(self, timeline: Sequence[Frame], index: int) -> str:
        return self.paint(timeline, index)

    def render_at(self, timeline: Sequence[Frame], beat_time: float) -> str:
        """Viewport centered on a continuous ``beat_time`` (enables smooth scroll)."""
        n = len(self.labels)
        label_w = max((len(s) for s in self.labels), default=1)
        gutter = label_w + 2  # "e |"
        anchor = self.width // 3  # playhead sits 1/3 from the left

        if not timeline:
            return "(empty)"
        strip = self._build_strip(timeline)
        center = self._column_of(beat_time)
        start = center - anchor

        # Playhead marker line, aligned over the viewport (after the gutter).
        head = " " * (gutter + anchor) + "v"

        rows = [head]
        for s in range(n):
            row_chars = strip[s]
            window = []
            for c in range(start, start + self.width):
                window.append(row_chars[c] if 0 <= c < len(row_chars) else FILL)
            # Draw the playhead column as a bar unless a fret digit sits there.
            if window[anchor] == FILL:
                window[anchor] = PLAYHEAD
            label = self.labels[s].rjust(label_w)
            rows.append(f"{label} |{''.join(window)}")

        rows.append(_bar_beat_footer(beat_time, self.beats_per_measure,
                                     total_bars(timeline, self.beats_per_measure)))
        return "\n".join(rows)
