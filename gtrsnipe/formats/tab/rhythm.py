"""Rhythm in a tab (F08): the dash-count table, note-length letters, and the legend line.

Shared by the tab generator and the tab parser, so that what one writes the other reads.
See docs/app/DESIGN-tab-rhythm.md.

**Dash count.** The dashes after a note name its length, in *base* notes: one dash for the
base note, two more for each doubling, one more for a dot.

    length   1   1.5   2   3   4   6   8   12   16   24   32 ...
    dashes   1    2    3   4   5   6   7    8    9   10   11 ...

**Letters.** W H q e s t x (whole, half, quarter, eighth, sixteenth, 32nd, 64th): long notes
in capitals, short ones lowercase; a dot adds half; ``+`` ties two lengths (``q+s``).
Read in either case.

Lengths are in beats (quarter notes) throughout; the base is a power-of-two note value.
"""
import re
from fractions import Fraction
from typing import Dict, Iterable, List, Optional

LAYOUTS = ("dashes", "columns", "loose")
ODD_BARS = ("columns", "nearest", "error")
MAX_DASHES = 15
MAX_SLOTS = 64                # a bar finer than this isn't on any grid worth drawing

# letter -> beats
_LETTER_BEATS = {"W": Fraction(4), "H": Fraction(2), "q": Fraction(1), "e": Fraction(1, 2),
                 "s": Fraction(1, 4), "t": Fraction(1, 8), "x": Fraction(1, 16)}
_BEATS_LETTER = {v: k for k, v in _LETTER_BEATS.items()}
_BY_ANY_CASE = {k.lower(): v for k, v in _LETTER_BEATS.items()}
_LETTER_TOKEN = re.compile(r"^[WHQESTXwhqestx]\.?(\+[WHQESTXwhqestx]\.?)*$")


def exact(beats) -> Fraction:
    """A length or time in beats as an exact fraction (floats arrive a hair off)."""
    return Fraction(beats).limit_denominator(960)


# -- the dash-count table ------------------------------------------------------------------

def _multiple(dashes: int) -> Fraction:
    """Length in base notes named by ``dashes`` (1 -> 1, 2 -> 1.5, 3 -> 2, 4 -> 3, ...)."""
    doublings, dotted = divmod(dashes - 1, 2)
    return Fraction(2) ** doublings * (Fraction(3, 2) if dotted else 1)


_DASHES_FOR = {_multiple(n): n for n in range(1, MAX_DASHES + 1)}


def dashes_for(length, base) -> Optional[int]:
    """How many dashes name ``length`` (beats) with this ``base``, or None if the table
    doesn't hold it."""
    return _DASHES_FOR.get(exact(length) / exact(base))


def length_for(dashes: int, base) -> Optional[Fraction]:
    """The length (beats) that ``dashes`` name, or None past the end of the table."""
    return _multiple(dashes) * exact(base) if 1 <= dashes <= MAX_DASHES else None


def nearest_dashes(length, base) -> int:
    """The table entry closest to ``length`` (for --tab-odd-bars nearest)."""
    want = exact(length) / exact(base)
    return min(_DASHES_FOR.items(), key=lambda kv: (abs(kv[0] - want), kv[1]))[1]


def pick_base(gaps: Iterable) -> Fraction:
    """The base for a tune: the longest plain note value (whole, half, quarter, ...) no
    longer than its shortest gap. A sixteenth if there are no gaps."""
    gaps = [exact(g) for g in gaps if g > 0]
    if not gaps:
        return Fraction(1, 4)
    shortest, base = min(gaps), Fraction(4)
    while base > shortest and base > Fraction(1, 32):
        base /= 2
    return base


def base_name(base) -> str:
    """A base in beats as a note value: 0.25 -> '1/16'."""
    whole = Fraction(4) / exact(base)
    return f"1/{whole}" if whole.denominator == 1 else f"{exact(base) / 4}"


def parse_base(text: str) -> Fraction:
    """'1/16' -> 1/4 beat. Raises ValueError for anything that isn't a note value."""
    m = re.fullmatch(r"\s*1\s*/\s*(\d+)\s*", text or "")
    if not m or int(m.group(1)) not in (1, 2, 4, 8, 16, 32, 64, 128):
        raise ValueError(f"not a note value: {text!r} (1/4, 1/8, 1/16, ...)")
    return Fraction(4, int(m.group(1)))


# -- letters -------------------------------------------------------------------------------

def letter_for(length) -> Optional[str]:
    """A length in beats as letters: 1 -> 'q', 0.75 -> 'e.', 1.25 -> 'q+s'. None for a
    length the letters can't state exactly (a triplet's note, say): a bar holding one
    gets no letters rather than nearly-right ones."""
    left, parts = exact(length), []
    for beats in sorted(_BEATS_LETTER, reverse=True):
        for value, mark in ((beats * 3 / 2, "."), (beats, "")):
            while left >= value and len(parts) < 4:
                parts.append(_BEATS_LETTER[beats] + mark)
                left -= value
    return "+".join(parts) if parts and not left else None


def letters_length(token: str) -> Optional[Fraction]:
    """'q.', 'Q+s', 'h' ... -> beats; None if it isn't a length."""
    if not _LETTER_TOKEN.match(token):
        return None
    total = Fraction(0)
    for part in token.split("+"):
        beats = _BY_ANY_CASE[part[0].lower()]
        total += beats * 3 / 2 if part.endswith(".") else beats
    return total


# -- the header lines ----------------------------------------------------------------------

LETTERS_LINE = ("Lengths: W H q e s t over each note (a dot adds half; + ties two; "
                "a letter with nothing under it is a rest)")


def _bars(numbers: Iterable[int], what: str) -> str:
    """[3, 4, 5, 9], 'in columns' -> '; bars 3-5, 9 in columns' ('' for no bars)."""
    numbers = sorted(set(numbers))
    if not numbers:
        return ""
    runs = []
    for n in numbers:
        if runs and n == runs[-1][1] + 1:
            runs[-1][1] = n
        else:
            runs.append([n, n])
    listed = ", ".join(str(a) if a == b else f"{a}-{b}" for a, b in runs)
    return f"; bar{'s' if len(numbers) > 1 else ''} {listed} {what}"


def _read_bars(text: str, what: str) -> set:
    """The bar numbers a legend lists before ``what`` ('bars 3-5, 9 in columns')."""
    listed = re.search(r"bars?\s+([\d,\s-]+?)\s+" + what, text, re.IGNORECASE)
    out = set()
    for a, b in re.findall(r"(\d+)(?:\s*-\s*(\d+))?", listed.group(1) if listed else ""):
        out.update(range(int(a), int(b or a) + 1))
    return out


def legend(layout: str, base=None, in_columns: List[int] = (), approximate: List[int] = ()) -> Optional[str]:
    """The ``Rhythm:`` header line for a layout (without the comment marks); None for
    'loose', which states no rhythm."""
    if layout == "columns":
        return (f"Rhythm: columns{_bars(approximate, 'approximate')}"
                "   (a note's column across its bar is its time)")
    if layout == "dashes":
        named = [(letter_for(_multiple(n) * exact(base)), n) for n in range(1, MAX_DASHES + 1)
                 if _multiple(n) * exact(base) <= 4]
        table = " ".join(f"{name}={n}" for name, n in named if name and "+" not in name)
        return (f"Rhythm: dash-count, base {base_name(base)}{_bars(in_columns, 'in columns')}"
                f"{_bars(approximate, 'approximate')}   ({table})")
    return None


def read_legend(tab_string: str) -> Dict:
    """What a tab's header says about its rhythm: ``layout`` ('dashes', 'columns' or None),
    ``base`` (beats), ``in_columns`` and ``approximate`` (1-based numbers of the bars
    written with columns as time, or with lengths that are only the nearest), and
    ``letters`` (True when a line of note lengths runs over each row)."""
    out = {"layout": None, "base": None, "in_columns": set(), "approximate": set(), "letters": False}
    m = re.search(r"^\s*//\s*Rhythm:\s*(.+)$", tab_string, re.MULTILINE | re.IGNORECASE)
    if m:
        text = m.group(1).split("(")[0]
        if text.strip().lower().startswith("columns"):
            out["layout"] = "columns"
            out["approximate"] = _read_bars(text, "approximate")
        elif text.strip().lower().startswith("dash-count"):
            base = re.search(r"base\s+(1\s*/\s*\d+)", text, re.IGNORECASE)
            try:
                out["base"] = parse_base(base.group(1)) if base else None
            except ValueError:
                out["base"] = None
            if out["base"] is not None:
                out["layout"] = "dashes"
                out["in_columns"] = _read_bars(text, "in columns")
                out["approximate"] = _read_bars(text, "approximate")
    out["letters"] = bool(re.search(r"^\s*//\s*Lengths:", tab_string, re.MULTILINE | re.IGNORECASE))
    return out
