"""C05/F02: keys, spelling, and key estimation (core/keys.py)."""
from types import SimpleNamespace as E

import pytest

from gtrsnipe.core.keys import (DOUBTED, ESTIMATED, FROM_FILE, Key, estimate_key, key_on,
                                note_name, parse_abc_key, parse_key, position, song_key,
                                spell_free)
from gtrsnipe.core.theory import note_name_to_pitch as n
from gtrsnipe.core.types import MusicalEvent, Song, Track


def test_line_of_fifths_names_round_trip():
    for pos in range(-8, 13):
        assert position(note_name(pos)) == pos
    assert [note_name(p) for p in (-8, -2, 0, 6, 12)] == ["Fb", "Bb", "C", "F#", "B#"]


@pytest.mark.parametrize("text, name, fifths, abc", [
    ("Eb", "Eb major", -3, "Eb"), ("F#m", "F# minor", 3, "F#m"), ("Bbmin", "Bb minor", -5, "Bbm"),
    ("D dorian", "D dorian", 0, "Ddor"), ("Amix", "A mixolydian", 2, "Amix"),
    ("C major", "C major", 0, "C"), ("a minor", "A minor", 0, "Am"), ("Cb", "Cb major", -7, "Cb"),
])
def test_parse_key(text, name, fifths, abc):
    key = parse_key(text)
    assert (key.name, key.fifths, key.abc) == (name, fifths, abc)


def test_parse_key_rejects_what_it_cannot_read():
    with pytest.raises(ValueError, match="use Eb major"):
        parse_key("D# major")                               # nine sharps
    with pytest.raises(ValueError):
        parse_key("H")
    with pytest.raises(ValueError):
        parse_key("C wibble")
    assert parse_key("none") is None and parse_key("HP") is None


def test_abc_key_fields():
    assert parse_abc_key("G") == Key("G")
    assert parse_abc_key("E minor") == Key("E", "minor")
    assert parse_abc_key("Dmix clef=treble") == Key("D", "mixolydian")
    assert parse_abc_key("D exp ^c") == Key("D")
    assert parse_abc_key("HP") is None and parse_abc_key("none") is None


def test_a_key_spells_its_scale_and_its_chromatic_notes():
    spell = lambda key: [parse_key(key).spell(pc) for pc in range(12)]
    assert spell("C") == ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]
    assert spell("Eb")[8] == "Ab" and spell("E")[8] == "G#"         # the same black key
    assert spell("Eb")[1] == "Db" and spell("E")[1] == "C#"
    assert spell("Am")[8] == "G#" and spell("Dm")[1] == "C#"        # a minor key's leading tone
    assert spell("F#")[5] == "E#" and spell("Gb")[11] == "Cb"       # only where the scale has them
    assert spell("E")[5] == "F" and spell("Bb")[11] == "B"          # not as chromatic notes


def test_key_signatures():
    assert Key("Bb").signature() == {"B": -1, "E": -1}
    assert Key("D").signature() == {"F": 1, "C": 1}
    assert Key("A", "minor").signature() == {} and Key("D", "dorian").signature() == {}


def test_key_on_and_transposing():
    assert key_on(1).tonic == "Db" and key_on(1, "minor").tonic == "C#"
    assert key_on(6).tonic == "F#"                                   # 6 sharps vs 6 flats
    assert Key("Eb").transposed(2) == Key("F")
    assert Key("Bb", "minor").transposed(1) == Key("B", "minor")
    assert Key("D", "dorian").transposed(-2) == Key("C", "dorian")


def test_spelling_with_no_key():
    assert [spell_free(pc) for pc in (1, 3, 6, 8, 10)] == ["Db", "Eb", "F#", "Ab", "Bb"]
    assert [spell_free(pc, minor=True) for pc in (1, 6, 8, 10)] == ["C#", "F#", "G#", "Bb"]


def melody(names, dur=1.0):
    return [E(pitch=n(x), duration=dur) for x in names.split()]


def test_estimate_key():
    assert estimate_key(melody("C4 E4 G4 C5 D4 F4 B3 G4 E4 C4 A4 G4 C4")) == Key("C")
    assert estimate_key(melody("Eb4 G4 Bb4 Ab4 F4 D4 Eb4 Bb3 C4 Ab4 G4 Eb4")) == Key("Eb")
    assert estimate_key(melody("A3 C4 E4 A4 G#4 B4 E4 D4 C4 B3 A3 E4 A3")) == Key("A", "minor")
    assert estimate_key(melody("E4 G#4 B4 E5 F#4 A4 D#4 B4 G#4 E4 C#5 B4 E4")) == Key("E")
    assert estimate_key([]) is None


def song_of(names):
    return Song(tracks=[Track(events=[MusicalEvent(i, n(x), 1.0, 90)
                                      for i, x in enumerate(names.split())])])


def test_song_key_prefers_the_songs_own_and_says_where_it_came_from():
    song = song_of("Eb4 G4 Bb4 Ab4 F4 D4 Eb4 Bb3 C4 Ab4 G4 Eb4")
    assert song_key(song) == (Key("Eb"), ESTIMATED)
    song.key, song.key_source = Key("G"), FROM_FILE
    assert song_key(song) == (Key("G"), FROM_FILE)
    assert song_key(Song()) == (None, "")


def test_a_midi_files_c_major_is_kept_only_if_the_notes_agree():
    flat = song_of("Eb4 G4 Bb4 Ab4 F4 D4 Eb4 Bb3 C4 Ab4 G4 Eb4")
    flat.key, flat.key_source = Key("C"), DOUBTED
    key, how = song_key(flat)
    assert key == Key("Eb") and how.startswith(ESTIMATED) and "looks like a default" in how
    plain = song_of("C4 E4 G4 C5 D4 F4 B3 G4 E4 C4 A4 G4 C4")
    plain.key, plain.key_source = Key("C"), DOUBTED
    assert song_key(plain) == (Key("C"), FROM_FILE)
