"""F08: rhythm in a tab. The dash-count layout, columns as time, the loose layout, the
note-length letters, and reading each of them back (docs/app/DESIGN-tab-rhythm.md)."""
import sys
from fractions import Fraction

import pytest

from gtrsnipe.arguments import setup_parser
from gtrsnipe.core.types import MusicalEvent, Song, Track
from gtrsnipe.formats.tab.generator.ascii import AsciiTabGenerator
from gtrsnipe.formats.tab.parser import AsciiTabParser
from gtrsnipe.formats.tab.rhythm import (base_name, dashes_for, legend, length_for, letter_for,
                                         letters_length, parse_base, pick_base, read_legend)

OPEN = [64, 59, 55, 50, 45, 40]                       # string index 0 = high e


def song(notes, time_signature="4/4"):
    """A Song from (time, string, fret) triples, with the positions already set."""
    events = [MusicalEvent(time=t, pitch=OPEN[s] + f, duration=0.25, velocity=90, string=s, fret=f)
              for t, s, f in notes]
    return Song(tracks=[Track(events=events)], title="t", time_signature=time_signature)


def tab(notes, **kw):
    return AsciiTabGenerator.generate(song(notes, kw.pop("time_signature", "4/4")), "",
                                      premapped=True, no_articulations=True, **kw)


def staff(text):
    return [l for l in text.splitlines() if "|" in l and not l.startswith("//")]


def header(text, word):
    return next((l for l in text.splitlines() if l.startswith(f"// {word}")), None)


def onsets(s):
    return sorted({round(e.time, 5) for e in s.tracks[0].events})


RUN = [(i * 0.25, 0, f) for i, f in enumerate([0, 1, 3, 5, 7, 5, 3, 1] * 2)] + [(4.0, 0, 0)]
HYMN = [(0, 1, 8), (0.75, 1, 8), (1, 1, 8), (1.75, 1, 6), (2, 1, 5), (2.75, 1, 8), (3, 0, 8), (3.75, 0, 10),
        (4, 0, 12), (4.75, 0, 12), (5, 0, 12), (5.75, 0, 10), (6, 0, 8)]
RESTS = [(1, 0, 0), (2, 0, 3), (3, 0, 8),                                   # a quarter rest, three quarters
         (8, 2, 0), (8, 3, 2), (8, 4, 3),                                   # (bar 2 is silent) a half-note chord
         (10, 2, 0), (10, 3, 0), (10, 4, 2), (10, 5, 3)]                    # and another
FIVE = [(0, 0, 5), (1.25, 0, 7), (2, 0, 8), (3, 0, 7), (4, 0, 5), (5, 0, 7), (6, 0, 8), (7, 0, 7)]
TRIPLETS = [(0, 0, 0), (1 / 3, 0, 1), (2 / 3, 0, 3), (1, 0, 5), (2, 0, 3), (3, 0, 1),    # a triplet, quarters
            (4, 0, 0), (5, 0, 1), (6, 0, 3), (7, 0, 5)]                                  # plain quarters
OFF_GRID = [(0, 0, 0), (0.013, 1, 1), (1.37, 0, 3), (2.911, 0, 5),                       # played, not written
            (4, 0, 0), (5, 0, 1), (6, 0, 3), (7, 0, 5)]


# -- the table, the base, the letters ----------------------------------------------------------

def test_the_dash_count_table():
    base = Fraction(1, 4)                              # a sixteenth
    lengths = [0.25, 0.375, 0.5, 0.75, 1, 1.5, 2, 3, 4]
    assert [dashes_for(x, base) for x in lengths] == [1, 2, 3, 4, 5, 6, 7, 8, 9]
    assert [length_for(n, base) for n in range(1, 10)] == [Fraction(x).limit_denominator(64) for x in lengths]
    assert dashes_for(1.25, base) is None and dashes_for(1 / 3, base) is None and length_for(0, base) is None


def test_the_base_is_the_longest_plain_note_no_longer_than_the_shortest_gap():
    assert pick_base([1, 0.5, 2]) == Fraction(1, 2)
    assert pick_base([0.75, 1.5]) == Fraction(1, 2)   # a dotted eighth: the base is an eighth
    assert pick_base([1 / 3, 1]) == Fraction(1, 4)
    assert pick_base([]) == Fraction(1, 4)
    assert base_name(Fraction(1, 4)) == "1/16" and parse_base("1/8") == Fraction(1, 2)
    with pytest.raises(ValueError):
        parse_base("1/3")


def test_letters_are_capital_for_long_notes_and_read_in_either_case():
    assert [letter_for(x) for x in (4, 3, 2, 1.5, 1, 0.75, 0.5, 0.25, 0.125)] == \
        ["W", "H.", "H", "q.", "q", "e.", "e", "s", "t"]
    assert letter_for(1.25) == "q+s" and letter_for(2.5) == "H+e"
    assert letter_for(1 / 3) is None and letter_for(0.013) is None      # exact, or no letters
    assert letters_length("q.") == Fraction(3, 2) == letters_length("Q.")
    assert letters_length("h") == 2 and letters_length("Q+S") == Fraction(5, 4)
    assert letters_length("Am") is None and letters_length("G7") is None


def test_the_legend_line():
    line = legend("dashes", Fraction(1, 4))
    assert line == "Rhythm: dash-count, base 1/16   (s=1 s.=2 e=3 e.=4 q=5 q.=6 H=7 H.=8 W=9)"
    assert legend("dashes", Fraction(1, 2), [7, 12], [3]).startswith(
        "Rhythm: dash-count, base 1/8; bars 7, 12 in columns; bar 3 approximate   (e=1")
    assert legend("columns").startswith("Rhythm: columns   (") and legend("loose") is None
    # runs of bars are written as ranges, and read back
    ranged = legend("dashes", Fraction(1, 2), [7, 8, 9, 12], [3, 4])
    assert ranged.startswith("Rhythm: dash-count, base 1/8; bars 7-9, 12 in columns; bars 3-4 approximate   (")
    said = read_legend(f"// {ranged}\n")
    assert (said["in_columns"], said["approximate"]) == ({7, 8, 9, 12}, {3, 4})
    hinted = legend("columns", approximate=[2, 3, 4])
    assert hinted.startswith("Rhythm: columns; bars 2-4 approximate   (")
    assert read_legend(f"// {hinted}\n")["approximate"] == {2, 3, 4}
    said = read_legend("// Rhythm: dash-count, base 1/8; bars 7, 12 in columns   (e=1 q=3)\n")
    assert (said["layout"], said["base"], said["in_columns"]) == ("dashes", Fraction(1, 2), {7, 12})
    assert read_legend("// Rhythm: columns\n")["layout"] == "columns"
    assert read_legend("// Tuning: E2,A2,D3,G3,B3,E4\n") == {
        "layout": None, "base": None, "in_columns": set(), "approximate": set(), "letters": False}
    assert read_legend("// Rhythm: dash-count, base 1/4; bar 3 approximate\n")["approximate"] == {3}


# -- the dash-count layout, against the examples in the design doc -----------------------------

def test_a_sixteenth_run_then_a_whole_note():
    text = tab(RUN)
    assert header(text, "Rhythm") == "// Rhythm: dash-count, base 1/16   (s=1 s.=2 e=3 e.=4 q=5 q.=6 H=7 H.=8 W=9)"
    assert staff(text)[0] == "e|-0-1-3-5-7-5-3-1-0-1-3-5-7-5-3-1-|-0---------|"


def test_dotted_rhythms_and_two_digit_frets():
    lines = staff(tab(HYMN))
    assert lines[0] == "e|----------------------8----10-|-12----12-12----10-8-------|"
    assert lines[1] == "B|-8----8-8----6-5----8---------|---------------------------|"


def test_a_rest_a_silent_bar_and_chords():
    text = tab(RESTS)
    assert "base 1/4" in header(text, "Rhythm")
    assert staff(text) == ["e|--0-3-8-|----|---------|",
                           "B|--------|----|---------|",
                           "G|--------|----|-0---0---|",
                           "D|--------|----|-2---0---|",
                           "A|--------|----|-3---2---|",
                           "E|--------|----|-----3---|"]


def test_a_technique_mark_takes_the_dash_before_its_note():
    events = song([(0, 0, 5), (1, 0, 7), (2, 0, 5), (3, 0, 3)])
    for e, tech in zip(events.tracks[0].events, ("pick", "hammer-on", "pull-off", "pick")):
        e.technique = tech
    events.as_written = True
    text = AsciiTabGenerator.generate(events, "")
    assert staff(text)[0] == "e|-5h7p5-3-|"
    back = AsciiTabParser.parse(text)
    assert onsets(back) == [0, 1, 2, 3] and not back.rhythm_approximate
    assert [e.technique for e in sorted(back.tracks[0].events, key=lambda e: e.time)][1:3] == ["hammer-on", "pull-off"]


# -- lengths the table doesn't hold --------------------------------------------------------------

def test_an_odd_bar_is_written_in_columns_and_named():
    text = tab(FIVE)                                   # bar 1 holds a note five sixteenths long
    assert "base 1/8; bar 1 in columns" in header(text, "Rhythm")
    first, second = staff(text)[0][2:].split("|")[:2]
    assert second == "-5---7---8---7---"               # quarters at three dashes each
    assert first == "-5---------7-----8-------7------"  # sixteen slots of two
    assert onsets(AsciiTabParser.parse(text)) == [0, 1.25, 2, 3, 4, 5, 6, 7]


def test_odd_bars_nearest_and_error():
    text = tab(FIVE, odd_bars="nearest")
    assert "bar 1 approximate" in header(text, "Rhythm") and "in columns" not in text
    back = AsciiTabParser.parse(text)
    assert back.rhythm_approximate and onsets(back)[4:] == [4, 5, 6, 7]     # only bar 1 is off
    with pytest.raises(ValueError, match="bars 1"):
        tab(FIVE, odd_bars="error")


def test_triplets_are_written_in_columns_and_get_no_letters():
    text = tab(TRIPLETS, letters=True)
    assert "bar 1 in columns" in header(text, "Rhythm")
    first, second = staff(text)[0][2:].split("|")[:2]
    assert first == "-0-1-3-5-----3-----1----"           # twelve slots of two: a triplet eighth each
    assert letter_row(text).split() == ["q"] * 4         # nearly-right letters would be worse than none
    assert letter_row(text).index("q") == 2 + len(first) + 1 + 1    # ... and bar 2's sit over bar 2
    for options in ({}, {"letters": True}, {"rhythm": "columns"}, {"rhythm": "columns", "letters": True}):
        back = AsciiTabParser.parse(tab(TRIPLETS, **options))
        assert onsets(back) == onsets(song(TRIPLETS)) and not back.rhythm_approximate, options
    # where only letters could have said it, the bar is read by its spacing, and said to be
    back = AsciiTabParser.parse(tab(TRIPLETS, rhythm="loose", letters=True))
    assert back.rhythm_approximate and onsets(back)[-4:] == [4, 5, 6, 7]


def test_a_bar_on_no_grid_is_named_as_approximate():
    for layout in ("dashes", "columns"):
        text = tab(OFF_GRID, rhythm=layout, letters=True)
        assert "bar 1 approximate" in header(text, "Rhythm"), layout
        back = AsciiTabParser.parse(text)
        assert back.rhythm_approximate and onsets(back)[-4:] == [4, 5, 6, 7], layout
        assert len(back.tracks[0].events) == len(OFF_GRID)


def test_letters_do_not_widen_a_bar_in_columns_more_than_they_need():
    assert staff(tab(FIVE, letters=True)) == staff(tab(FIVE))       # 'q+s' has five slots to sit in
    assert letter_row(tab(FIVE, letters=True)).split() == ["q+s", "e.", "q", "q", "q", "q", "q", "q"]


def test_a_fixed_base():
    quarters = [(float(i), 0, 5) for i in range(4)]
    assert staff(tab(quarters))[0] == "e|-5-5-5-5-|"
    text = tab(quarters, base="1/16")
    assert "base 1/16" in header(text, "Rhythm") and staff(text)[0] == "e|-5-----5-----5-----5-----|"
    # a base longer than a bar's shortest note: that bar can't be counted in dashes
    assert "bar 1 in columns" in header(tab([(0, 0, 5), (0.5, 0, 7), (1, 0, 8), (2, 0, 7)], base="1/4"), "Rhythm")


# -- columns as time, and the loose layout -------------------------------------------------------

def test_columns_layout():
    text = tab(HYMN, rhythm="columns")
    assert header(text, "Rhythm").startswith("// Rhythm: columns")
    rows = staff(text)
    assert rows[1] == "B|-8--------8--8--------6--5--------8-------------|"      # sixteen slots of three
    assert rows[0] == "e|-------------------------------------8--------10|"
    assert onsets(AsciiTabParser.parse(text)) == onsets(song(HYMN))


def test_loose_layout_states_no_rhythm():
    text = tab(HYMN, rhythm="loose")
    assert header(text, "Rhythm") is None
    assert staff(text)[1] == "B|-8---8-8---6-5---8-------|------------------|"
    assert AsciiTabParser.parse(text).rhythm_approximate


# -- letters -----------------------------------------------------------------------------------

def letter_row(text):
    lines = text.splitlines()
    return lines[next(i for i, l in enumerate(lines) if l.startswith("e|")) - 1]


def test_letters_sit_over_their_notes():
    text = tab(RESTS, letters=True)
    assert header(text, "Lengths") is not None
    assert letter_row(text) == "  q q q q        H   H"
    row = letter_row(tab(RUN, letters=True))
    assert row.split() == ["s"] * 16 + ["W"]


def test_letters_make_any_layout_exact():
    # a dotted note at the end of a bar, then a bar opening with a rest: the letters of one
    # bar must not push the next bar's off their notes
    notes = [(0, 0, 5), (1, 0, 7), (2.5, 0, 8), (4.5, 0, 7), (5, 0, 5), (7.25, 0, 3)]
    for layout in ("loose", "dashes", "columns"):
        text = tab(notes, rhythm=layout, letters=True)
        back = AsciiTabParser.parse(text)
        assert onsets(back) == onsets(song(notes)), layout
        assert not back.rhythm_approximate, layout
    shouted = tab(notes, rhythm="loose", letters=True)
    row = letter_row(shouted)
    assert onsets(AsciiTabParser.parse(shouted.replace(row, row.upper()))) == onsets(song(notes))


def test_a_chord_name_line_is_not_taken_for_letters():
    text = tab(RESTS, name_chords=True)                # no '// Lengths' line: nothing to read
    assert onsets(AsciiTabParser.parse(text)) == onsets(song(RESTS))


# -- reading back ------------------------------------------------------------------------------

@pytest.mark.parametrize("options", [{}, {"letters": True}, {"rhythm": "columns"}, {"base": "1/32"},
                                     {"rhythm": "columns", "letters": True}, {"max_line_width": 30}])
@pytest.mark.parametrize("notes", [RUN, HYMN, RESTS, FIVE])
def test_what_is_written_is_read_back_exactly_and_written_the_same_again(notes, options):
    text = tab(notes, **options)
    back = AsciiTabParser.parse(text)
    assert onsets(back) == onsets(song(notes)) and not back.rhythm_approximate
    assert sorted((e.string, e.fret) for e in back.tracks[0].events) == sorted((s, f) for _, s, f in notes)
    back.as_written = True
    again = AsciiTabGenerator.generate(back, "", no_articulations=True, **options)
    assert staff(again) == staff(text) and header(again, "Rhythm") == header(text, "Rhythm")


def test_a_bar_that_does_not_add_up_is_read_by_its_spacing():
    text = tab(HYMN)
    rows = staff(text)
    edited = text
    for row in rows:                                   # someone deletes the last dash of bar 2
        edited = edited.replace(row, row[:-2] + row[-1])
    back = AsciiTabParser.parse(edited)
    assert back.rhythm_approximate
    assert onsets(back)[:8] == onsets(song(HYMN))[:8]   # bar 1 still adds up, and is exact
    assert len(onsets(back)) == 13


def test_without_its_legend_a_tab_is_still_a_tab():
    text = tab(HYMN)
    bare = "\n".join(l for l in text.splitlines() if not l.startswith("// Rhythm"))
    back = AsciiTabParser.parse(bare)
    assert back.rhythm_approximate and len(onsets(back)) == 13
    assert [int(t // 4) for t in onsets(back)] == [0] * 8 + [1] * 5         # every note in its bar


def test_a_short_first_bar_is_a_pickup():
    text = "// Time: 4/4\n// Rhythm: dash-count, base 1/8   (e=1 q=3)\n\n" \
           "e|-5-7-|-8---8---8---8---|\n" + "".join(f"{s}|-----|-----------------|\n" for s in "BGDAE")
    assert onsets(AsciiTabParser.parse(text)) == [3, 3.5, 4, 5, 6, 7]       # the pickup ends at the bar line


def test_a_tab_that_only_hinted_at_its_rhythm_is_written_loose():
    loose = tab(HYMN, rhythm="loose")
    back = AsciiTabParser.parse(loose)
    back.as_written = True
    again = AsciiTabGenerator.generate(back, "", no_articulations=True)
    assert header(again, "Rhythm") is None             # the source stated no lengths, so neither do we
    asked = AsciiTabGenerator.generate(back, "", no_articulations=True, rhythm="columns")
    assert header(asked, "Rhythm") is not None         # unless asked


# -- the command line ----------------------------------------------------------------------------

def run(monkeypatch, *argv):
    from gtrsnipe.converter import main
    monkeypatch.setattr(sys, "argv", ["gtrsnipe", *argv])
    try:
        main()
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else (0 if e.code is None else 1)
    return 0


ABC = "X:1\nT:x\nM:4/4\nL:1/4\nK:C\nG3/4 G/4 G3/4 F/4 E3/4 G/4 c3/4 d/4 | e3/4 e/4 e3/4 d/4 c2 |\n"
ODD = "X:1\nT:x\nM:4/4\nL:1/8\nK:C\nE5 G3 | c2 c2 c2 c2 |\n"


def test_cli_defaults_and_options(monkeypatch, tmp_path):
    args = setup_parser().parse_args([])
    assert (args.max_line_width, args.tab_rhythm, args.tab_base, args.tab_odd_bars, args.tab_letters) == \
        (80, None, "auto", "columns", False)
    src = tmp_path / "x.abc"
    src.write_text(ABC)
    out = tmp_path / "x.tab"
    assert run(monkeypatch, "-i", str(src), "-o", str(out), "-y") == 0
    text = out.read_text()
    assert header(text, "Rhythm").startswith("// Rhythm: dash-count, base 1/16")
    assert onsets(AsciiTabParser.parse(text)) == [0, 0.75, 1, 1.75, 2, 2.75, 3, 3.75, 4, 4.75, 5, 5.75, 6]
    assert run(monkeypatch, "-i", str(src), "-o", str(out), "-y", "--tab-rhythm", "columns", "--tab-letters") == 0
    text = out.read_text()
    assert header(text, "Rhythm").startswith("// Rhythm: columns") and header(text, "Lengths")
    assert run(monkeypatch, "-i", str(src), "-o", str(out), "-y", "--tab-rhythm", "loose") == 0
    assert header(out.read_text(), "Rhythm") is None


def test_cli_odd_bars_error_stops(monkeypatch, tmp_path, capsys):
    src = tmp_path / "odd.abc"
    src.write_text(ODD)
    out = tmp_path / "odd.tab"
    assert run(monkeypatch, "-i", str(src), "-o", str(out), "-y", "--tab-odd-bars", "error") == 1
    shown = capsys.readouterr()
    assert "the dash-count table doesn't" in shown.out + shown.err and not out.exists()
    assert run(monkeypatch, "-i", str(src), "-o", str(out), "-y") == 0
    assert "bar 1 in columns" in header(out.read_text(), "Rhythm")


def test_cli_a_tab_round_trips_through_itself(monkeypatch, tmp_path):
    src = tmp_path / "x.abc"
    src.write_text(ABC)
    first, second, mid = tmp_path / "a.tab", tmp_path / "b.tab", tmp_path / "b.mid"
    assert run(monkeypatch, "-i", str(src), "-o", str(first), "-y", "--tab-letters") == 0
    assert run(monkeypatch, "-i", str(first), "-o", str(second), "-o", str(mid), "-y", "--tab-letters") == 0
    assert staff(second.read_text()) == staff(first.read_text())             # as written, lengths and all
    assert header(second.read_text(), "Rhythm") == header(first.read_text(), "Rhythm")
