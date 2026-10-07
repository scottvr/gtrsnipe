"""C01 (--name-chords: chord names over the tab) and C06 (--name-chord SHAPE)."""
import sys

import pytest

from gtrsnipe.chords.segment import segment_by_measure
from gtrsnipe.chords.shape import name_shape, parse_shape
from gtrsnipe.core.chords import identify, is_clear
from gtrsnipe.core.theory import note_name_to_pitch as n
from gtrsnipe.core.types import MusicalEvent, Song, Track
from gtrsnipe.formats.tab.generator.ascii import AsciiTabGenerator
from gtrsnipe.formats.tab.parser import AsciiTabParser

STD = [n(x) for x in ("E2", "A2", "D3", "G3", "B3", "E4")]


def ps(names):
    return [n(x) for x in names.split()]


# -- is_clear: only plainly spelled chords get a name over a tab ----------------------

@pytest.mark.parametrize("notes, clear", [
    ("C3 E3 G3", True),                  # a triad
    ("C3 E3 G3 D4", True),               # one extra tone is tolerated
    ("C3 E3 B3", True),                  # Cmaj7 without its fifth
    ("C3 G3", True),                     # a power chord, exactly
    ("C4 D4 E4 F4", False),              # a melody fragment ("Fmaj7/C" without its third)
    ("G2 F#3 C4", False),                # "C5/G": a power chord with an extra tone
    ("C3 E3", False),                    # two tones: too few to name
])
def test_is_clear(notes, clear):
    pitches = ps(notes)
    chord = identify(pitches, bass=min(pitches))
    assert chord is not None and is_clear(chord, pitches) is clear


# -- the downbeat bass --------------------------------------------------------------------

def sixteenths(bars):
    events, t = [], 0.0
    for bar in bars:
        for _ in range(2):
            for p in ps(bar):
                events.append(MusicalEvent(t, p, 0.25, 90))
                t += 0.25
    return Song(tracks=[Track(events=events)])


PRELUDE = ["G2 D3 B3 A3 B3 D3 B3 D3", "G2 E3 C4 B3 C4 E3 C4 E3"]     # Bach, BWV 1007, bars 1-2


def test_an_arpeggio_bass_counts_when_it_starts_the_bar():
    song = sixteenths(PRELUDE)
    plain = [s.label for s in segment_by_measure(song)]
    kept = [s.label for s in segment_by_measure(song, keep_downbeat_bass=True)]
    assert kept == ["G", "C/G"]
    assert plain != kept               # chord charts keep the duration-only rule


# -- the name line over the tab --------------------------------------------------------------

def bar(t, pitches, kind="block"):
    if kind == "block":
        return [MusicalEvent(t, p, 4.0, 90) for p in pitches]
    return [MusicalEvent(t + i, p, 1.0, 90) for i, p in enumerate(pitches)]


def progression():
    events = (bar(0, ps("C3 E3 G3 C4 E4")) + bar(4, ps("G2 B2 D3 G3 B3")) +
              bar(8, ps("A2 E3 A3 C4 E4")) + bar(12, ps("A2 E3 A3 C4 E4")) +
              bar(16, ps("C5 D5 E5 F5"), "melody") + bar(20, ps("F2 C3 F3 A3 C4 F4")))
    return Song(tracks=[Track(events=events)], title="p")


def name_lines(text):
    return [l for l in text.splitlines() if l.strip() and not l.startswith("//") and "|" not in l]


def test_names_change_only_and_repeat_per_line():
    # one line: the repeated Am bar gets no name, and the melody bar none either
    wide = AsciiTabGenerator.generate(progression(), "", max_line_width=400, name_chords=True)
    assert [l.split() for l in name_lines(wide)] == [["C", "G", "Am", "F"]]
    # a bar per line: every line starts with its chord, so Am appears again
    # (a row narrower than any bar: each bar gets a row to itself, in any layout)
    narrow = AsciiTabGenerator.generate(progression(), "", max_line_width=1, name_chords=True)
    assert [w for l in name_lines(narrow) for w in l.split()] == ["C", "G", "Am", "Am", "F"]


def test_names_sit_over_a_fret_digit():
    text = AsciiTabGenerator.generate(progression(), "", max_line_width=400, name_chords=True)
    lines = text.splitlines()
    names = name_lines(text)
    # each name sits over a fret digit of the staff line below it
    for i, l in enumerate(lines):
        if l in names:
            staff = lines[i + 1:i + 7]
            for word in l.split():
                col = l.index(word)
                assert any(s[col].isdigit() for s in staff)


def test_without_the_flag_nothing_changes():
    a = AsciiTabGenerator.generate(progression(), "", max_line_width=60)
    assert not name_lines(a)


def test_a_named_tab_parses_back_to_the_same_notes():
    named = AsciiTabGenerator.generate(progression(), "", max_line_width=60, name_chords=True)
    plain = AsciiTabGenerator.generate(progression(), "", max_line_width=60)
    notes = lambda t: sorted((e.time, e.pitch) for e in AsciiTabParser.parse(t).tracks[0].events)
    assert notes(named) == notes(plain)


def test_crowded_names_are_nudged_apart():
    assert AsciiTabGenerator._chord_name_line([(3, "Cmaj7"), (5, "G")]) == "   Cmaj7 G"


# -- --name-chord SHAPE --------------------------------------------------------------------------

@pytest.mark.parametrize("shape, name", [
    ("x,3,2,0,1,0", "C"), ("x,x,3,2,1,0", "Fmaj7"), ("320003", "G"),
    ("0,0,2,2,1,0", "Am/E"), ("x02220", "A"),
])
def test_shapes_in_standard(shape, name):
    assert name_shape(shape, STD).label == name


def test_tuning_and_capo_change_the_name():
    baritone = [n(x) for x in ("B1", "E2", "A2", "D3", "F#3", "B3")]
    assert name_shape("x,3,2,0,1,0", baritone).label == "G"
    assert name_shape("x02220", STD, capo=2).label == "B"


@pytest.mark.parametrize("bad", ["x,3,2,0,1", "x3201", "x,3,2,0,1,q", "x,x,x,x,x,x"])
def test_bad_shapes_are_rejected(bad):
    with pytest.raises(ValueError):
        parse_shape(bad, 6)


def test_cli_name_chord(monkeypatch, capsys):
    from gtrsnipe.converter import main
    monkeypatch.setattr(sys, "argv", ["gtrsnipe", "--tuning", "DROP_D",
                                      "--name-chord", "0,x,0,2,3,2", "--name-chord", "x,3,2"])
    with pytest.raises(SystemExit) as e:
        main()
    out = capsys.readouterr().out
    assert e.value.code == 1                       # one bad shape
    assert "0,x,0,2,3,2" in out and " D " in out and "DROP_D" in out and "Error" in out


@pytest.mark.parametrize("first, second, expect", [
    ("C3 E3 G3", "G2 B2 D3", ["C", "G"]),        # named whole, this bar reads "G6"
    ("C3 E3 G3", "A2 C3 E3", ["C", "Am"]),       # ... and this one "Am7"
    ("C3 E3 G3", "C3 E3 G3", ["C"]),             # the same chord twice: one name
])
def test_a_bar_with_two_chords_gets_both_names(first, second, expect):
    events = ([MusicalEvent(0, p, 2.0, 90) for p in ps(first)] +
              [MusicalEvent(2, p, 2.0, 90) for p in ps(second)])
    text = AsciiTabGenerator.generate(Song(tracks=[Track(events=events)]), "",
                                      max_line_width=200, name_chords=True)
    assert [w for l in name_lines(text) for w in l.split()] == expect
