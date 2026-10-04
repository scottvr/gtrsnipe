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
    assert "open-position shapes where one exists" in sheet
    compact = build_chord_sheet(song, MapperConfig(), voicing="compact")
    assert "**C** `" in compact and "compact voicings of each chord's name" in compact


# -- C07: --chart-voicing source ----------------------------------------------------------

def test_source_voicing_matches_the_tabs_own_fingering():
    from gtrsnipe.formats.tab.generator.ascii import AsciiTabGenerator
    from gtrsnipe.formats.tab.parser import AsciiTabParser
    # a C chord voiced as the source plays it: C3 G3 C4 E4 (no low-string E)
    events = [MusicalEvent(0, p, 4.0, 90) for p in (n("C3"), n("G3"), n("C4"), n("E4"))]
    song = Song(tracks=[Track(events=events)], title="t")
    sheet = build_chord_sheet(song, MapperConfig())            # source is the default
    assert "as this song's tab fingers it" in sheet
    caption = next(l for l in sheet.splitlines() if l.startswith("**C** "))
    shape = caption.split("`")[1]
    tab = AsciiTabGenerator.generate(song, "", max_line_width=200)
    parsed = AsciiTabParser.parse(tab).tracks[0].events
    tab_frets = {e.string: e.fret for e in parsed}             # 0 = highest string
    expect = "".join(str(tab_frets[s]) if s in tab_frets else "x" for s in reversed(range(6)))
    assert shape == expect and not caption.endswith(" *")


def test_source_voicing_falls_back_and_says_so():
    # an arpeggio whose chord tones need two frets on one string: no single hand shape
    run_ = [n(x) for x in ("C3", "E3", "G3", "C4", "E4", "G4", "C5", "E5")]
    events = [MusicalEvent(i * 0.5, p, 0.5, 90) for i, p in enumerate(run_)]
    sheet = build_chord_sheet(Song(tracks=[Track(events=events)], title="t"), MapperConfig())
    caption = next(l for l in sheet.splitlines() if l.startswith("**C** "))
    assert caption.endswith(" *")             # a compact voicing, marked
