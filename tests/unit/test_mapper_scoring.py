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


# --- the no-fit case (M01 q1, 2026-11-04): rank the least bad fingering and say so ---

import logging

from gtrsnipe.core.types import MusicalEvent


def unison_g3():
    """Asturias v1's doubled unison: G3 on two strings never fits 4 frets (G0 with D5, A10 or E15)."""
    return [[MusicalEvent(0.0, 55, 1.0, 90), MusicalEvent(0.0, 55, 1.0, 90)]]


def test_no_fit_chord_is_ranked_not_arbitrary():
    mapper = GuitarMapper(MapperConfig())
    out = mapper.map_multi_string(unison_g3())
    frets = sorted((ev.string, ev.fret) for ev in out)
    assert frets == [(2, 0), (3, 5)]          # G0 D5, span 5: the least bad, not G0 A10
    span = mapper._chord_span(tuple(FretPosition(s, f) for s, f in frets))
    assert span > mapper.config.unplayable_fret_span


@pytest.mark.parametrize("optimizer", ["viterbi", "greedy"])
def test_no_fit_chord_is_reported(optimizer, caplog):
    mapper = GuitarMapper(MapperConfig(optimizer=optimizer))
    with caplog.at_level(logging.WARNING, logger="gtrsnipe.guitar.mapper"):
        if optimizer == "greedy":
            mapper._map_multi_string_greedy(unison_g3())
        else:
            mapper.map_multi_string(unison_g3())
    msgs = [r.message for r in caplog.records if "fits within" in r.message]
    assert len(msgs) == 1
    assert "G3 G3" in msgs[0] and "span 5" in msgs[0] and "beat 0" in msgs[0]


def test_fitting_chord_is_not_reported(caplog):
    mapper = GuitarMapper(MapperConfig())
    with caplog.at_level(logging.WARNING, logger="gtrsnipe.guitar.mapper"):
        mapper.map_multi_string([[MusicalEvent(0.0, 64, 1.0, 90), MusicalEvent(0.0, 71, 1.0, 90)]])
    assert not [r for r in caplog.records if "fits within" in r.message]


# --- both mappers report a path score under the one objective (M02) ---

def test_greedy_reports_a_path_score_equal_to_its_choices():
    groups = [[MusicalEvent(t * 0.5, p, 0.5, 90)] for t, p in enumerate((64, 71, 64, 69, 64, 71, 67))]
    mapper = GuitarMapper(MapperConfig(optimizer="greedy"))
    out = mapper._map_multi_string_greedy(groups)
    assert mapper.last_path_score is not None
    fings = [(FretPosition(ev.string, ev.fret),) for ev in out]
    total, prev, pp = 0.0, None, None
    for f in fings:
        total += mapper._score_fingering(f, prev, pp)
        pp, prev = prev, f
    assert mapper.last_path_score == pytest.approx(total)
    # the global optimum is never below the greedy path on the same objective
    viterbi = GuitarMapper(MapperConfig())
    viterbi.map_multi_string([[MusicalEvent(t * 0.5, p, 0.5, 90)] for t, p in enumerate((64, 71, 64, 69, 64, 71, 67))])
    assert viterbi.last_path_score >= mapper.last_path_score - 1e-9
