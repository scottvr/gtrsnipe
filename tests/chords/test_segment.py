"""Tests for per-measure chord segmentation."""
import pytest

from gtrsnipe.chords.segment import (
    beats_per_measure,
    segment_by_measure,
)
from gtrsnipe.core.types import MusicalEvent, Song, Track


def ev(time, pitch, duration=1.0):
    return MusicalEvent(time=time, pitch=pitch, duration=duration, velocity=100)


def song(events, time_signature="4/4"):
    return Song(tracks=[Track(events=events)], time_signature=time_signature)


C, E, G, A, B, D = 60, 64, 67, 69, 71, 62


# -- beats_per_measure ------------------------------------------------------

def test_beats_per_measure_common():
    assert beats_per_measure("4/4") == 4.0
    assert beats_per_measure("3/4") == 3.0
    assert beats_per_measure("6/8") == 3.0
    assert beats_per_measure("2/2") == 4.0


def test_beats_per_measure_bad_input_defaults_to_four():
    assert beats_per_measure("garbage") == 4.0
    assert beats_per_measure("0/0") == 4.0


# -- segmentation -----------------------------------------------------------

def test_empty_song_has_no_spans():
    assert segment_by_measure(song([])) == []


def test_one_measure_one_chord():
    # A C major triad filling a 4/4 bar.
    spans = segment_by_measure(song([ev(0, C, 4), ev(0, E, 4), ev(0, G, 4)]))
    assert len(spans) == 1
    assert spans[0].label == "C"
    assert spans[0].index == 0
    assert spans[0].start_beat == 0.0


def test_two_measures_two_chords():
    spans = segment_by_measure(song([
        ev(0, C, 4), ev(0, E, 4), ev(0, G, 4),        # bar 1: C
        ev(4, A, 4), ev(4, C + 12, 4), ev(4, E + 12, 4),  # bar 2: Am
    ]))
    assert [s.label for s in spans] == ["C", "Am"]


def test_arpeggiated_chord_over_a_bar_reads_as_one_chord():
    # Root, then third, then fifth entering across the bar (your arpeggio case).
    spans = segment_by_measure(song([
        ev(0, C, 4),   # C sustains the whole bar
        ev(1, E, 3),
        ev(2, G, 2),
    ]))
    assert len(spans) == 1
    assert spans[0].label == "C"


def test_short_passing_tone_is_dropped():
    # A sustained C triad plus a very short D (1/16 of the bar) -> still C, not C-with-D.
    spans = segment_by_measure(song([
        ev(0, C, 4), ev(0, E, 4), ev(0, G, 4),
        ev(1.0, D, 0.25),  # brief passing tone, under the 15% threshold
    ]))
    assert spans[0].label == "C"


def test_rest_measure_is_no_chord():
    # Bar 1 has a chord; bar 2 is empty -> N.C.
    spans = segment_by_measure(song([ev(0, C, 4), ev(0, E, 4), ev(0, G, 4)],
                                     ) )
    # Extend to two bars by placing a note far out with silence between.
    spans = segment_by_measure(song([
        ev(0, C, 4), ev(0, E, 4), ev(0, G, 4),
        ev(8, C, 4), ev(8, E, 4), ev(8, G, 4),
    ]))
    assert len(spans) == 3
    assert spans[0].label == "C"
    assert spans[1].label == "N.C."   # empty middle bar
    assert spans[2].label == "C"


def test_dropped_passing_tone_is_not_the_bass():
    # Regression: a brief LOW passing note (below the chord, dropped by the
    # threshold) must not become a spurious slash-chord bass.
    spans = segment_by_measure(song([
        ev(0, C, 4), ev(0, E, 4), ev(0, G, 4),  # sustained C major
        ev(1.0, 44, 0.25),                       # brief G#2, under threshold
    ]))
    assert spans[0].label == "C"   # not "C/G#"


def test_chord_sustained_across_barline_fills_later_measures():
    # Regression: a chord held through two bars must read C, C — not C, N.C.
    spans = segment_by_measure(song([
        ev(0, C, 8), ev(0, E, 8), ev(0, G, 8),
    ]))
    assert [s.label for s in spans] == ["C", "C"]


def test_onset_exactly_on_final_barline_is_not_dropped():
    # Regression: a stab landing exactly on the last measure boundary was rounded
    # away by n_measures and excluded by the half-open filter.
    spans = segment_by_measure(song([
        ev(0, C, 4), ev(0, E, 4), ev(0, G, 4),   # bar 1
        ev(4, G, 0), ev(4, B, 0), ev(4, D + 12, 0),  # zero-dur stab at beat 4
    ]))
    assert len(spans) == 2
    assert spans[0].label == "C"
    assert spans[1].label == "G"


def test_power_chord_measure():
    spans = segment_by_measure(song([ev(0, C, 4), ev(0, G, 4)]))
    assert spans[0].label == "C5"


def test_three_four_time_two_bars():
    spans = segment_by_measure(song([
        ev(0, C, 3), ev(0, E, 3), ev(0, G, 3),    # bar 1 (beats 0-3): C
        ev(3, G, 3), ev(3, B, 3), ev(3, D + 12, 3),  # bar 2 (beats 3-6): G
    ], time_signature="3/4"))
    assert [s.label for s in spans] == ["C", "G"]


def test_voicing_pitches_are_recorded():
    spans = segment_by_measure(song([ev(0, C, 4), ev(0, E, 4), ev(0, G, 4)]))
    assert spans[0].pitches == (C, E, G)
