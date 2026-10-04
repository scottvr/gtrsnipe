"""C04: extended chords, and C05: chord names spelled for a key."""
import pytest

from gtrsnipe.chords.chart import _canonical_positions, open_positions, shape_string
from gtrsnipe.chords.shape import name_shape, spell_pitches
from gtrsnipe.core.chords import Chord, identify, is_clear
from gtrsnipe.core.config import MapperConfig
from gtrsnipe.core.keys import Key, parse_key
from gtrsnipe.core.theory import note_name_to_pitch as n
from gtrsnipe.guitar.mapper import GuitarMapper

STANDARD = [n(x) for x in ("E2", "A2", "D3", "G3", "B3", "E4")]            # low -> high


def named(notes, **kw):
    pitches = [n(x) for x in notes.split()]
    return identify(pitches, bass=min(pitches), **kw).name


@pytest.mark.parametrize("notes, name", [
    ("C3 E3 G3 Bb3 D4", "C9"), ("C3 E3 Bb3 D4", "C9"),               # the fifth is optional
    ("D3 F#3 A3 C#4 E4", "Dmaj9"), ("A2 C3 E3 G3 B3", "Am9"),
    ("E2 G#2 D3 G3", "E7#9"), ("C3 E3 G3 Bb3 Db4", "C7b9"),
    ("C3 F3 G3 Bb3", "C7sus4"), ("D3 G3 A3 C4", "D7sus4"),
    ("C3 Bb3 D4 F4", "C11"), ("D3 C4 E4 G4", "D11"),                   # Bb/C and C/D
    ("F2 C3 Eb3 G3 Bb3", "F11"),                                       # Cm7/F
    ("A2 C3 G3 D4", "Am11"), ("A2 C3 E3 G3 D4", "Am11"),
    ("G2 F3 B3 E4", "G13"), ("C3 E3 G3 Bb3 D4 A4", "C13"),             # with or without the 9th
    ("C3 E3 B3 A4", "Cmaj13"), ("A2 C3 G3 F#4", "Am13"),
])
def test_extended_chords_are_named(notes, name):
    assert named(notes) == name


def test_a_melody_note_over_a_triad_is_not_an_extension():
    assert named("C3 E3 G3 D4") == "C"                  # no seventh: add9 is for shapes only
    assert named("C3 E3 G3 A3 D4") == "C6"              # likewise 6/9
    assert named("C3 E3 G3 Bb3 D4 F#4") == "C7"         # something outside the chord
    assert named("C3 Bb3 D4") != "C9"                   # incomplete: no third


def test_an_extended_name_needs_its_root_in_the_bass():
    assert not identify([n(x) for x in "E3 G3 Bb3 C4 D4".split()], bass=n("E3")).extended
    assert named("C3 D3 E3 G3") == "C"                  # not D11/C
    assert named("C3 Eb3 G3 Db4") == "Cm"               # not Eb13/C
    # with no bass given, the lowest pitch stands in for it
    assert identify([n(x) for x in "C3 E3 G3 Bb3 D4".split()]).name == "C9"
    assert identify([n(x) for x in "E3 G3 Bb3 C4 D4".split()]).quality != "9"


def test_fret_shapes_name_the_added_ninths_too():
    assert name_shape("x32033", STANDARD).label == "Cadd9"
    assert name_shape("x3223x", STANDARD).label == "C6/9"
    assert name_shape("x02410", STANDARD).label == "Amadd9"
    assert name_shape("x3233x", STANDARD).label == "C9"
    assert name_shape("3x345x", STANDARD).label == "G13"
    assert name_shape("x02030", STANDARD).label == "A7sus4"
    assert name_shape("x32010", STANDARD).label == "C"


def test_is_clear_for_extended_chords():
    c9 = [n(x) for x in "C3 E3 Bb3 D4".split()]
    assert is_clear(identify(c9, bass=c9[0]), c9)
    assert not is_clear(Chord(0, "9"), [n(x) for x in "C3 E3 G3 D4".split()])       # no seventh
    assert not is_clear(Chord(0, "9"), c9 + [n("F#4")])                              # an extra


def test_diagrams_for_extended_chords():
    mapper = GuitarMapper(MapperConfig())
    c9 = _canonical_positions(Chord(0, "9"), mapper)
    pitches = sorted(mapper.open_string_pitches[p.string] + p.fret for p in c9)
    assert [p % 12 for p in pitches] == [0, 4, 10, 2]                   # C E Bb D, the 9th on top
    high_to_low = list(reversed(STANDARD))
    assert shape_string(open_positions(Chord(0, "add9"), high_to_low), 6) == "x30010"   # C D G C E
    assert shape_string(open_positions(Chord(9, "7sus4"), high_to_low), 6) == "x00030"  # A D G D E


# -- C05: spelling ------------------------------------------------------------------------

def test_names_are_spelled_for_the_key():
    ab = [n(x) for x in "Ab2 C3 Eb3".split()]
    assert identify(ab, bass=ab[0], key=parse_key("Eb")).name == "Ab"
    assert identify(ab, bass=ab[0], key=parse_key("E")).name == "G#"
    assert identify(ab, bass=ab[0]).name == "Ab"                         # no key: its own
    csm = [n(x) for x in "C#3 E3 G#3".split()]
    assert identify(csm, bass=csm[0]).name == "C#m"
    assert identify(csm, bass=csm[0], key=parse_key("Ab")).name == "Dbm"


def test_a_slash_bass_is_spelled_as_the_chord_spells_it():
    key = parse_key("C")
    assert Chord(4, "", bass=8, key=key).name == "E/G#"                  # not E/Ab, even in C
    assert Chord(2, "", bass=6).name == "D/F#"
    assert Chord(8, "", bass=0).name == "Ab/C"
    assert Chord(10, "m", bass=1).name == "Bbm/Db"
    assert Chord(1, "m", bass=8).name == "C#m/G#"
    assert Chord(0, "7", bass=10, key=key).name == "C7/Bb"
    assert Chord(0, "aug", bass=8).name == "Caug/G#"
    assert Chord(1, "", bass=5).name == "Db/F"
    assert Chord(1, "", bass=5, key=parse_key("F#")).name == "C#/E#"     # the key has an E#


def test_the_key_is_not_part_of_a_chords_identity():
    assert Chord(8, "", key=parse_key("Eb")) == Chord(8, "")
    assert len({Chord(8, "", key=parse_key("Eb")), Chord(8, "", key=parse_key("E"))}) == 1


def test_a_shapes_notes_are_spelled_like_its_name():
    shape = name_shape("244322", STANDARD)                                # F# major
    assert shape.label == "F#" and spell_pitches(shape) == "F#2 C#3 F#3 A#3 C#4 F#4"
    shape = name_shape("x13331", STANDARD)
    assert shape.label == "Bb" and spell_pitches(shape) == "Bb2 F3 Bb3 D4 F4"
    in_key = name_shape("x46664", STANDARD, key=Key("Db"))
    assert in_key.label == "Db" and spell_pitches(in_key, Key("Db")).startswith("Db3 Ab3")
