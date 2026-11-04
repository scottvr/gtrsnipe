"""Pins scoring intent in `_score_fingering` that the sweep notes (docs/dev/NOTES-playability.md,
M01) record as deliberate, so it survives the next refactor."""
import pytest

from gtrsnipe.core.config import MapperConfig
from gtrsnipe.core.types import FretPosition
from gtrsnipe.guitar.mapper import GuitarMapper


def shape(*frets_low_to_high):
    """Six-string chord shape low E -> high E; None = string not played. String 0 is high E."""
    return tuple(FretPosition(string=5 - i, fret=f)
                 for i, f in enumerate(frets_low_to_high) if f is not None)


A_BARRE_5 = shape(5, 7, 7, 6, 5, 5)        # average 5.83
OPEN_E = shape(0, 2, 2, 1, 0, 0)           # average 0.83
OPEN_ASUS4 = shape(None, 0, 2, 2, 3, 0)    # average 1.4


def movement_cost(mapper, fingering, prev):
    return mapper._score_fingering(fingering, None, None) - mapper._score_fingering(fingering, prev, None)


def test_open_strings_pull_the_average_toward_an_open_shape():
    # scottvr's intent (2026-11-04): a jump to an open shape costs less the more strings the
    # previous chord already played open, because open strings count as fret 0 in the average.
    mapper = GuitarMapper(MapperConfig(string_switch_penalty=0))
    from_barre = movement_cost(mapper, OPEN_E, A_BARRE_5)
    from_open_sus = movement_cost(mapper, OPEN_E, OPEN_ASUS4)
    assert from_barre == pytest.approx(5.0 * 3)       # 5.83 -> 0.83, movement_penalty 3
    assert from_open_sus == pytest.approx(0.5667 * 3, abs=0.01)
    assert from_barre > 8 * from_open_sus


def test_single_note_to_open_string_is_charged_the_full_distance():
    # The cost of the same rule on a line: open E then fret 7 is seven frets each way.
    mapper = GuitarMapper(MapperConfig(string_switch_penalty=0))
    open_e = (FretPosition(string=0, fret=0),)
    fret_7 = (FretPosition(string=0, fret=7),)
    assert movement_cost(mapper, fret_7, open_e) == pytest.approx(7 * 3)
    assert movement_cost(mapper, open_e, fret_7) == pytest.approx(7 * 3)
