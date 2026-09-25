"""Inverse tuning solver: given a target melody, find a tuning under which an
'innocuous' all-open-string tab produces it.

Each distinct target pitch is assigned to its own open string, so the tab shows
only open strings (fret 0) yet — decoded through the solved tuning — sounds the
melody. This is the constructive extreme of the (tab, tuning) decomposition: all
of the "expression" lives in the tuning key, none in the tab. (Also a genuinely
useful alternate-tuning finder.)
"""
from typing import List, Tuple


def solve_open_string_tuning(target_pitches: List[int], max_strings: int = 12
                             ) -> Tuple[List[int], List[int]]:
    """Return (open_string_pitches high->low, per-note string assignment).

    Distinct pitches map to distinct open strings; each note is then played open
    on its string. Raises ValueError if the melody has more distinct pitches than
    ``max_strings`` (an all-open solution needs one string per distinct pitch).
    """
    if not target_pitches:
        raise ValueError("no target pitches to solve for")
    distinct = sorted(set(target_pitches), reverse=True)  # high -> low
    if len(distinct) > max_strings:
        raise ValueError(
            f"{len(distinct)} distinct pitches need {len(distinct)} open strings "
            f"(max {max_strings}); shorten the melody or raise --max-strings.")
    index = {p: i for i, p in enumerate(distinct)}
    assignment = [index[p] for p in target_pitches]
    return distinct, assignment


def format_open_string_tab(open_pitch_names: List[str], assignment: List[int],
                           cols: int = 4) -> str:
    """A plain ASCII tab of all-open-string plucks (fret 0), one row per string
    (high->low). Reveals none of the melody — that's the point."""
    n = len(open_pitch_names)
    import re
    labels = [re.sub(r"-?\d+$", "", nm) for nm in open_pitch_names]
    label_w = max((len(x) for x in labels), default=1)
    rows = []
    for s in range(n):
        cells = "".join(("0" if a == s else "-") + "-" * (cols - 1) for a in assignment)
        rows.append(f"{labels[s]:>{label_w}}|{cells}")
    return "\n".join(rows)
