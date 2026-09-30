"""C02: open-position chord shapes (--prefer-open-chords)."""
import re

import pytest

from gtrsnipe.chords.chart import build_chord_sheet, open_positions, shape_string
from gtrsnipe.core.chords import PITCH_CLASS_NAMES, Chord
from gtrsnipe.core.config import MapperConfig
from gtrsnipe.core.theory import note_name_to_pitch as n
from gtrsnipe.core.types import MusicalEvent, Song, Track

STANDARD = [n(x) for x in ("E4", "B3", "G3", "D3", "A2", "E2")]         # high -> low


def chord(name):
    m = re.match(r"([A-G]#?)(.*?)(?:/([A-G]#?))?$", name)
    bass = PITCH_CLASS_NAMES.index(m.group(3)) if m.group(3) else None
    return Chord(PITCH_CLASS_NAMES.index(m.group(1)), m.group(2), bass)


def shape(name, tuning=STANDARD, capo=0):
    pos = open_positions(chord(name), tuning, capo)
    return shape_string(pos, len(tuning)) if pos else None


@pytest.mark.parametrize("name, expected", [
    ("C", "x32010"), ("G", "320003"), ("D", "xx0232"), ("A", "x02220"), ("E", "022100"),
    ("Am", "x02210"), ("Em", "022000"), ("Dm", "xx0231"), ("F", "xx3211"),
    ("A7", "x02020"), ("E7", "020100"), ("D7", "xx0212"), ("G7", "320001"),
    ("B7", "x21202"), ("Cmaj7", "x32000"), ("C/G", "332010"),
])
def test_the_classic_open_shapes_in_standard(name, expected):
    assert shape(name) == expected


def test_straddle_rule_rejects_unfingerable_but_keeps_c7():
    assert shape("Fmaj7") == "xx3210"          # not 102210 (fret 1 around fret 2, open A between)
    assert shape("C7") == "x32310"             # fret 3 around a lower fret is fine


def test_a_capo_gives_the_shape_you_finger():
    assert shape("D", capo=2) == "x32010"      # a C shape two frets up
    assert shape("A", capo=2) == "320003"      # a G shape


def test_other_tunings_and_no_shape():
    open_g = [n(x) for x in ("D4", "B3", "G3", "D3", "G2", "D2")]
    assert shape("G", open_g) == "x00000"
    assert shape("G#") is None                 # nothing in the first position: fall back


def test_chart_draws_open_shapes_with_captions():
    events = ([MusicalEvent(0, p, 4.0, 90) for p in (n("C3"), n("E3"), n("G3"))] +
              [MusicalEvent(4, p, 4.0, 90) for p in (n("G2"), n("B2"), n("D3"))])
    song = Song(tracks=[Track(events=events)], title="t")
    sheet = build_chord_sheet(song, MapperConfig(), prefer_open_chords=True)
    assert "**C** `x32010`" in sheet and "**G** `320003`" in sheet
    assert "Open-position shapes" in sheet
    plain = build_chord_sheet(song, MapperConfig())
    assert "**C** `" in plain and "Open-position shapes" not in plain
