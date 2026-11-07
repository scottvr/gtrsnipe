"""M08: the time-scaled movement cost in the scorer."""
import math

from gtrsnipe.core.config import MapperConfig
from gtrsnipe.core.types import FretPosition, MusicalEvent
from gtrsnipe.guitar.mapper import GuitarMapper


def _m(**kw):
    return GuitarMapper(MapperConfig(**kw))


def test_time_blind_by_default():
    m = _m()
    a, b = [FretPosition(0, 5)], [FretPosition(0, 7)]
    assert m._movement_factor(0.01) == 1.0
    assert m._score_fingering(b, a, None, 0.01) == m._score_fingering(b, a, None, None)


def test_factor_is_reference_over_gap_with_a_floor():
    m = _m(movement_time_base="onset", movement_reference_seconds=0.5, min_gap_seconds=0.05)
    assert math.isclose(m._movement_factor(0.5), 1.0)
    assert math.isclose(m._movement_factor(0.25), 2.0)
    assert math.isclose(m._movement_factor(2.0), 0.25)
    assert math.isclose(m._movement_factor(0.0), 10.0)      # floored at 0.05
    assert m._movement_factor(None) == 1.0                 # the first onset


def test_only_the_movement_term_is_scaled():
    base = _m()
    timed = _m(movement_time_base="onset")
    a, b = [FretPosition(0, 5)], [FretPosition(0, 7)]            # two frets of movement, same string
    plain = base._score_fingering(b, a, None)
    assert math.isclose(timed._score_fingering(b, a, None, 0.25) - plain, -2 * 3.0 * (2.0 - 1.0))
    c = [FretPosition(1, 5)]                                     # a string switch, no movement
    assert math.isclose(timed._score_fingering(c, a, None, 0.25), base._score_fingering(c, a, None))


def test_gap_by_time_base_and_tempo():
    prev = [MusicalEvent(0.0, 60, 0.5, 90), MusicalEvent(0.0, 64, 1.0, 90)]   # ends at 1.0 beat
    cur = [MusicalEvent(2.0, 67, 1.0, 90)]
    onset = _m(movement_time_base="onset", tempo_bpm=120.0)
    end = _m(movement_time_base="end", tempo_bpm=120.0)
    assert math.isclose(onset._gap_seconds(prev, cur), 1.0)     # two beats at 120
    assert math.isclose(end._gap_seconds(prev, cur), 0.5)       # one beat free
    assert _m()._gap_seconds(prev, cur) is None and onset._gap_seconds(None, cur) is None
    slow = _m(movement_time_base="onset", tempo_bpm=60.0)
    assert math.isclose(slow._gap_seconds(prev, cur), 2.0)


def test_a_hurried_move_prefers_the_string_switch():
    """G2 then B2 half a beat apart. Time-blind: E3 then E7 (four frets of movement, 12 points,
    beats a one-fret move plus a string switch at 13). With the move charged against a quarter
    second (factor 2 at the 0.5 s reference), E7 costs 24 and A2 costs 16, so the mapper switches
    strings instead; under the end-to-start base the gap is zero (held notes), the floor makes
    the move ten times dearer, and the answer is the same."""
    def run(**kw):
        evs = [MusicalEvent(0.0, 43, 0.5, 90), MusicalEvent(0.5, 47, 0.5, 90)]
        m = GuitarMapper(MapperConfig(**kw))
        return [(e.string, e.fret) for e in m.map_events_to_fretboard(evs, no_articulations=True)]
    assert run() == [(5, 3), (5, 7)]
    assert run(movement_time_base="onset", tempo_bpm=120.0) == [(5, 3), (4, 2)]
    assert run(movement_time_base="end", tempo_bpm=120.0) == [(5, 3), (4, 2)]
    assert run(movement_time_base="onset", tempo_bpm=30.0) == [(5, 3), (5, 7)]   # a whole second: cheap again


def test_viterbi_and_greedy_agree_on_the_objective_with_time():
    evs = [MusicalEvent(i * 0.25, p, 0.25, 90) for i, p in enumerate((64, 71, 64, 69, 76, 64, 59, 71))]
    kw = dict(movement_time_base="end", tempo_bpm=200.0)
    v = GuitarMapper(MapperConfig(**kw))
    g = GuitarMapper(MapperConfig(optimizer="greedy", **kw))
    mv = v.map_events_to_fretboard([MusicalEvent(e.time, e.pitch, e.duration, e.velocity) for e in evs], no_articulations=True)
    mg = g.map_events_to_fretboard([MusicalEvent(e.time, e.pitch, e.duration, e.velocity) for e in evs], no_articulations=True)
    assert len(mv) == len(mg) == 8
    assert v.last_path_score >= g.last_path_score - 1e-9      # Viterbi is never worse under the same objective
