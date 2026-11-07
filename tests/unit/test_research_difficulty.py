"""M03: the per-onset difficulty descriptors and the tab profile."""
import math

from gtrsnipe.core.types import MusicalEvent, Song, Track
from gtrsnipe.research import difficulty as D


def _song(onsets, tempo=120.0):
    """onsets: list of (time_beats, duration_beats, [(string, fret), ...]); pitches are faked from
    standard tuning so the mapper is never needed."""
    opens = [64, 59, 55, 50, 45, 40]
    evs = []
    for t, dur, pairs in onsets:
        for s, f in pairs:
            evs.append(MusicalEvent(t, opens[s] + f, dur, 90, string=s, fret=f))
    return Song(tracks=[Track(events=evs)], tempo=tempo, title="t")


A_BARRE = [(5, 5), (4, 7), (3, 7), (2, 6), (1, 5), (0, 5)]     # 5-7-7-6-5-5 low->high
B_BARRE = [(s, f + 2) for s, f in A_BARRE]
A_MINOR = [(5, 5), (4, 7), (3, 7), (2, 5), (1, 5), (0, 5)]


def test_barre_shape_is_four_fingers_with_a_barre_and_span_two():
    o = D.onsets(_song([(0, 1, A_BARRE)]))[0]
    assert o.notes == 6 and o.fretted == 6
    assert o.position == 5 and o.fingers == 4 and o.span == 2 and o.barre


def test_open_and_single_notes():
    o = D.onsets(_song([(0, 1, [(1, 0), (0, 0)]), (1, 1, [(0, 7)])]))
    assert o[0].position is None and o[0].fingers == 0 and o[0].span == 0 and not o[0].barre
    assert o[1].position == 7 and o[1].fingers == 1 and o[1].shift == 0.0  # no position to move from


def test_lazy_hand_stays_put_within_reach_and_moves_the_least_that_fits():
    # the A minor pentatonic box at the 5th position: frets 5-8 on every string, no hand move
    box = [(0, 1, [(5, 5)]), (1, 1, [(5, 8)]), (2, 1, [(4, 5)]), (3, 1, [(4, 7)]), (4, 1, [(0, 8)]), (5, 1, [(0, 5)])]
    o = D.onsets(_song(box))
    assert [x.position for x in o] == [5.0] * 6 and all(x.shift == 0 for x in o)
    assert [x.index_fret for x in o] == [5, 8, 5, 7, 8, 5]
    # reach 0 is the plain index proxy: every note is its own position
    o0 = D.onsets(_song(box), reach=0)
    assert [x.position for x in o0] == [5.0, 8.0, 5.0, 7.0, 8.0, 5.0]
    # a shape anchors the index at its lowest fret even when the lazy hand could reach it
    o = D.onsets(_song([(0, 1, [(0, 5)]), (1, 1, [(1, 7), (0, 8)])]))
    assert o[1].position == 7.0 and o[1].shift == 2.0
    # a note beyond reach moves the hand up the least that fits; a lower one pulls it down to itself
    o = D.onsets(_song([(0, 1, [(0, 5)]), (1, 1, [(0, 10)]), (2, 1, [(0, 2)])]))
    assert [x.position for x in o] == [5.0, 7.0, 2.0] and [x.shift for x in o] == [0.0, 2.0, 5.0]
    # the hand is carried across an open note
    o = D.onsets(_song([(0, 1, [(0, 5)]), (1, 1, [(0, 0)]), (2, 1, [(0, 12)])]))
    assert o[1].position is None and o[2].shift == 4.0     # 5 -> 9 (12 - reach), not 12


def test_barre_slide_moves_two_frets_with_no_shape_change():
    o = D.onsets(_song([(0, 1, A_BARRE), (1, 1, B_BARRE)]))
    assert o[1].shift == 2 and o[1].shape_change == 12   # every (string, fret) pair differs
    o = D.onsets(_song([(0, 1, A_BARRE), (1, 1, A_MINOR)]))
    assert o[1].shift == 0 and o[1].shape_change == 2     # one note moved: one pair out, one in


def test_time_bases_differ_only_when_a_note_ends_early():
    held = _song([(0, 1.0, A_BARRE), (1, 1, B_BARRE)])            # held to the next onset
    cut = _song([(0, 0.5, A_BARRE), (1, 1, B_BARRE)])             # released half a beat early
    for song in (held, cut):
        on = D.onsets(song, time_base="onset")[1]
        assert math.isclose(on.gap, 0.5)                           # one beat at 120 bpm
    assert math.isclose(D.onsets(held, time_base="end")[1].gap, D.MIN_GAP_SECONDS)   # floored
    assert math.isclose(D.onsets(cut, time_base="end")[1].gap, 0.25)
    assert D.onsets(held, time_base="end")[1].move_rate > D.onsets(cut, time_base="end")[1].move_rate


def test_tempo_scales_seconds_and_rates():
    slow = D.onsets(_song([(0, 1, A_BARRE), (1, 1, B_BARRE)], tempo=60.0), time_base="onset")[1]
    fast = D.onsets(_song([(0, 1, A_BARRE), (1, 1, B_BARRE)], tempo=240.0), time_base="onset")[1]
    assert math.isclose(slow.gap, 1.0) and math.isclose(fast.gap, 0.25)
    assert math.isclose(fast.move_rate, 4 * slow.move_rate)


def test_lz_complexity_prefers_repeats():
    assert D.lz_complexity([]) == 0
    assert D.lz_complexity(["a"] * 16) < D.lz_complexity(list("abcdefghijklmnop"))
    rep = _song([(i, 1, A_BARRE if i % 2 else B_BARRE) for i in range(16)])
    uniq = _song([(i, 1, [(0, i)]) for i in range(16)])
    assert D.profile(rep).repetitiveness > D.profile(uniq).repetitiveness


def test_profile_counts_and_uses_the_tabs_own_fingering():
    song = _song([(0, 1, A_BARRE), (1, 1, B_BARRE), (2, 1, [(0, 0)]), (3, 1, [(0, 12)])])
    p = D.profile(song, "x")
    assert p.fingering == "as written" and p.onsets == 4 and p.notes == 14
    assert p.shifts == 1                     # the barre slide; the open note has no position
    assert p.max_position == 9 and p.position_range == 4      # the lazy hand reaches 12 from 9
    assert math.isclose(p.chord_share, 0.5) and math.isclose(p.barre_share, 0.5)
    assert p.stats["fingers"][2] == 4 and p.index > 0


def test_refinger_uses_the_mapper():
    song = _song([(0, 1, [(0, 12)])])      # E5 written at the 12th fret of the high e
    p = D.profile(song, "x", refinger=True)
    assert p.fingering == "mapper" and p.onsets == 1


def test_unfingered_input_is_mapped():
    evs = [MusicalEvent(i * 0.5, 64 + i, 0.5, 90) for i in range(6)]
    p = D.profile(Song(tracks=[Track(events=evs)]), "line")
    assert p.fingering == "mapper" and p.onsets == 6 and p.notes == 6
