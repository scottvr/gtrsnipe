"""ABC parser (backlog B01). The old parser ignored key signatures and read chord
symbols as notes: it decoded 0 of the 1,034 Nottingham tunes correctly. The new
one matches music21 note-for-note on 94% of them; the rest are music21 quirks.
These cases pin the features real ABC uses."""
import pytest

from gtrsnipe.core.theory import pitch_to_note_name
from gtrsnipe.formats.abc.parser import AbcParser, key_accidentals

H = "X:1\nT:t\nM:4/4\nL:1/8\n"


def notes(abc, **kw):
    ev = sorted(AbcParser.parse(abc, **kw).tracks[0].events, key=lambda e: (e.time, e.pitch))
    return [(pitch_to_note_name(e.pitch), e.time, e.duration) for e in ev]


def names(abc, **kw):
    return [n for n, _, _ in notes(abc, **kw)]


@pytest.mark.parametrize("key,expected", [
    ("G", {"F": 1}), ("D", {"F": 1, "C": 1}), ("F", {"B": -1}), ("Bb", {"B": -1, "E": -1}),
    ("Am", {}), ("E minor", {"F": 1}), ("Edor", {"F": 1, "C": 1}), ("Dmix", {"F": 1}),
    ("Ador", {"F": 1}), ("F#m", {"F": 1, "C": 1, "G": 1}), ("C#", {l: 1 for l in "FCGDAEB"}),
    ("HP", {}), ("Hp", {"F": 1, "C": 1}), ("none", {}), ("D exp ^c", {"C": 1}),
    ("Ddor ^c", {"C": 1}), ("G clef=bass", {"F": 1}),
])
def test_key_signatures(key, expected):
    assert key_accidentals(key) == expected


def test_key_signature_applies_to_notes():
    assert names(H + "K:G\nF G A B|") == ["F#4", "G4", "A4", "B4"]
    assert names(H + "K:Bb\nB E") == ["Bb4", "Eb4"]


def test_chord_symbols_decorations_grace_notes_and_lyrics_are_not_notes():
    abc = H + 'K:C\n"G"G2 "D7"!trill!A ~B .c {g}d +fermata+e\nw: la la la la\n'
    assert names(abc) == ["G4", "A4", "B4", "C5", "D5", "E5"]


def test_comments_are_stripped():
    assert names(H + "K:C\nA % Acoustic Guitar\nB") == ["A4", "B4"]


def test_accidental_propagation_follows_the_abc_version():
    body = "K:C\n^F F f | F"
    assert names(H + body) == ["F#4", "F4", "F5", "F4"]                 # legacy: own note only
    assert names("%abc-2.1\n" + H + body) == ["F#4", "F#4", "F#5", "F4"]  # 2.x default 'pitch'
    octave = "%abc-2.1\n%%propagate-accidentals octave\n" + H + body
    assert names(octave) == ["F#4", "F#4", "F5", "F4"]
    assert names(H + body, propagate_accidentals="octave") == ["F#4", "F#4", "F5", "F4"]


def test_ties_attached_and_detached():
    assert notes(H + "K:C\nC2-C2 D") == [("C4", 0.0, 2.0), ("D4", 2.0, 0.5)]
    # Nottingham writes ties apart, even across a chord symbol or bar line
    assert notes(H + 'K:G\nB3 -"Em"B2d') == [("B4", 0.0, 2.5), ("D5", 2.5, 0.5)]
    assert notes(H + "K:C\nD3 -|D2 E") == [("D4", 0.0, 2.5), ("E4", 2.5, 0.5)]
    # a "tie" into a different pitch is not a tie: both notes stay
    assert names(H + "K:C\nB-c") == ["B4", "C5"]


def test_a_tied_note_keeps_its_accidental():
    # legacy file: ^G3 -G3 is one G# held; the following plain G is natural again
    assert notes(H + "K:D\n^G3 -G3 G") == [("Ab4", 0.0, 3.0), ("G4", 3.0, 0.5)]
    assert notes(H + "K:C\n[^FA]-[FA] F") == [("F#4", 0.0, 1.0), ("A4", 0.0, 1.0), ("F4", 1.0, 0.5)]


def test_broken_rhythm_and_tuplets():
    assert notes(H + "K:C\nA>B c") == [("A4", 0.0, 0.75), ("B4", 0.75, 0.25), ("C5", 1.0, 0.5)]
    assert notes(H + "K:C\nA<B") == [("A4", 0.0, 0.25), ("B4", 0.25, 0.75)]
    trip = notes(H + "K:C\n(3ABc d")
    assert [round(t, 4) for _, t, _ in trip] == [0.0, 0.3333, 0.6667, 1.0]


def test_rests_chords_lengths_and_multibar_rests():
    assert notes(H + "K:C\n[CEG]2 z [^FA]/") == [
        ("C4", 0.0, 1.0), ("E4", 0.0, 1.0), ("G4", 0.0, 1.0), ("F#4", 1.5, 0.25), ("A4", 1.5, 0.25)]
    assert notes(H + "K:C\nZ2 A") == [("A4", 8.0, 0.5)]
    assert notes(H + "K:C\nA// B3/2") == [("A4", 0.0, 0.125), ("B4", 0.125, 0.75)]


def test_default_unit_length_follows_the_meter():
    assert notes("X:1\nM:C\nK:C\nA")[0][2] == 0.5         # 1/8
    assert notes("X:1\nM:2/4\nK:C\nA")[0][2] == 0.25      # 1/16 when the meter is < 3/4


def test_inline_and_body_fields_change_key_and_length():
    assert names(H + "K:C\nF [K:G] F") == ["F4", "F#4"]
    assert names(H + "K:C\nF\nK:D\nF C") == ["F4", "F#4", "C#4"]
    assert notes(H + "K:C\nA [L:1/4] B") == [("A4", 0.0, 0.5), ("B4", 0.5, 1.0)]


def test_first_tune_and_first_voice_only():
    assert names(H + "K:C\nA\nX:2\nT:u\nK:C\nB") == ["A4"]
    assert names(H + "K:C\nV:1\nA B\nV:2\nc d\nV:1\nC") == ["A4", "B4", "C4"]


def test_repeats_and_endings_read_as_written():
    assert names(H + "K:C\n|:A B:|[1 c|2 d|]") == ["A4", "B4", "C5", "D5"]


def test_header_metadata():
    song = AbcParser.parse("X:1\nT:My Tune\nM:6/8\nQ:1/4=90\nK:G\nG")
    assert song.title == "My Tune" and song.time_signature == "6/8" and song.tempo == 90


def test_generator_output_round_trips():
    from gtrsnipe.core.types import MusicalEvent, Song, Track
    from gtrsnipe.formats.abc.generator import AbcGenerator
    pitches = [60, 62, 64, 66, 67, 70, 72]
    song = Song(tracks=[Track(events=[MusicalEvent(i * 0.5, p, 0.5, 90)
                                      for i, p in enumerate(pitches)],
                              instrument_name="Acoustic Guitar")])
    back = AbcParser.parse(AbcGenerator.generate(song))
    assert [e.pitch for e in sorted(back.tracks[0].events, key=lambda e: e.time)] == pitches
