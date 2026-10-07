"""v0.7.0: a tab is kept as written (B05), and the reader honours what a tab states:
its bars, capo, time signature and technique marks."""
import argparse
import sys

import mido
import pytest

from gtrsnipe.arguments import adopt_tab_header, setup_parser
from gtrsnipe.core.config import MapperConfig
from gtrsnipe.core.types import Song, Track
from gtrsnipe.formats.tab.parser import AsciiTabParser
from gtrsnipe.guitar.fingering import positioned, slide
from gtrsnipe.guitar.mapper import GuitarMapper

HEADER = "// Tempo: 100 BPM\n// Time: 4/4\n// Tuning: E2,A2,D3,G3,B3,E4\n\n"
THREE = HEADER + """e|----------------|----------------|-0-----------|
B|----------------|-0-------3------|-------------|
G|-0-2-4-5-7-5-4-2|----------------|-------------|
D|----------------|----------------|-------------|
A|----------------|-----------h5---|-------------|
E|----------------|----------------|-------------|
"""
ONE_STRING = HEADER + """e|----------|
B|----------|
G|----------|
D|----------|
A|-7-9-10-12|
E|----------|
"""


def notes(text):
    """(bar, string, fret, technique) for every note of a tab, in order."""
    song = AsciiTabParser.parse(text)
    bar = 4.0 if song.time_signature == "4/4" else None
    num, den = (int(x) for x in song.time_signature.split("/"))
    bar = num * 4.0 / den
    return [(int(e.time // bar), e.string, e.fret, e.technique)
            for e in sorted(song.tracks[0].events, key=lambda e: (e.time, e.string))]


def run(monkeypatch, *argv):
    from gtrsnipe.converter import main
    monkeypatch.setattr(sys, "argv", ["gtrsnipe", *argv])
    try:
        main()
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else (0 if e.code is None else 1)
    return 0


def write(tmp_path, name, text):
    path = tmp_path / name
    path.write_text(text)
    return str(path)


# -- the reader ----------------------------------------------------------------------------

def test_each_bar_is_one_measure():
    events = sorted(AsciiTabParser.parse(THREE).tracks[0].events, key=lambda e: e.time)
    assert [e.time for e in events] == [0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4.0, 6.0, 6.75, 8.0]
    assert [e.duration for e in events][:3] == [0.5, 0.5, 0.5]
    assert events[-1].duration == 4.0                          # the last note rings to the bar's end


def test_a_bar_of_four_notes_and_a_bar_of_sixteen_are_both_one_measure():
    rest = "".join(f"\n{s}|--------|--------------------------------|" for s in "BGDAE")
    tab = HEADER + "e|-5-7-8-5|-5-7-8-5-7-8-5-7-8-5-7-8-5-7-8-5|" + rest + "\n"
    times = sorted(e.time for e in AsciiTabParser.parse(tab).tracks[0].events)
    assert times[:4] == [0, 1, 2, 3]                           # quarter notes
    assert times[4:8] == [4, 4.25, 4.5, 4.75] and len(times) == 20


def test_the_time_signature_line_sets_the_bar_length():
    tab = THREE.replace("// Time: 4/4", "// Time: 3/4")
    song = AsciiTabParser.parse(tab)
    assert song.time_signature == "3/4"
    assert sorted({int(e.time // 3) for e in song.tracks[0].events}) == [0, 1, 2]
    assert min(e.time for e in song.tracks[0].events if e.string == 0) == 6.0   # bar 3 starts on beat 6


def test_technique_marks_are_read():
    tab = HEADER + "e|-5h7p5t12-|" + "".join(f"\n{s}|----------|" for s in "BGDAE") + "\n"
    assert [n[3] for n in notes(tab)] == [None, "hammer-on", "pull-off", "tap"]


def test_the_capo_line_is_read():
    tab = HEADER.replace("// Tuning", "// Capo: 2nd Fret\n// Tuning") + \
        "e|--------|\nB|-1-3-5-8|\nG|--------|\nD|--------|\nA|--------|\nE|--------|\n"
    assert AsciiTabParser.header_capo(tab) == 2 and AsciiTabParser.header_capo(THREE) is None
    pitches = lambda **kw: sorted(e.pitch for e in AsciiTabParser.parse(tab, **kw).tracks[0].events)
    assert pitches() == [62, 64, 66, 69]                       # D E F# A: the frets count from the capo
    assert pitches(capo=0) == [60, 62, 64, 67]                 # an explicit capo wins
    assert [n[2] for n in notes(tab)] == [1, 3, 5, 8]          # the written frets either way


# -- whose fingering -----------------------------------------------------------------------

def test_positioned_keeps_a_tabs_own_fingering():
    song = AsciiTabParser.parse(ONE_STRING)
    mapper = GuitarMapper(MapperConfig())
    song.as_written = True
    kept = positioned(song, song.tracks[0].events, mapper)
    assert [(e.string, e.fret) for e in kept] == [(4, 7), (4, 9), (4, 10), (4, 12)]
    assert all(e.technique == "pick" for e in kept)
    song.as_written = False
    assert [(e.string, e.fret) for e in positioned(song, song.tracks[0].events, mapper)] != \
        [(4, 7), (4, 9), (4, 10), (4, 12)]                      # the mapper prefers the D string


def test_positioned_keeps_marks_unless_articulations_are_off():
    song = AsciiTabParser.parse(THREE)
    song.as_written = True
    mapper = GuitarMapper(MapperConfig())
    assert [e.technique for e in positioned(song, song.tracks[0].events, mapper)].count("hammer-on") == 1
    plain = positioned(song, song.tracks[0].events, mapper, no_articulations=True)
    assert {e.technique for e in plain} == {"pick"}


def test_slide_moves_every_note_along_its_string_or_none():
    song = AsciiTabParser.parse(ONE_STRING)
    before = [(e.string, e.fret, e.pitch) for e in song.tracks[0].events]
    assert slide(song, 2, 24) == []
    assert [(e.string, e.fret, e.pitch) for e in song.tracks[0].events] == \
        [(s, f + 2, p + 2) for s, f, p in before]
    stuck = slide(song, 12, 24)                                 # 22 and 26 don't fit: nothing moves
    assert len(stuck) == 1 and "fret 14 -> 26" in stuck[0]
    assert [e.fret for e in song.tracks[0].events] == [9, 11, 12, 14]


# -- the command line ----------------------------------------------------------------------

def test_tab_to_tab_keeps_the_tab(monkeypatch, tmp_path):
    src = write(tmp_path, "three.tab", THREE)
    out = tmp_path / "out.tab"
    assert run(monkeypatch, "-i", src, "-o", str(out), "-y") == 0
    text = out.read_text()
    assert notes(text) == notes(THREE)                          # bars, strings, frets and marks
    assert "Fingering:" not in text


def test_refinger_is_asked_for_and_said(monkeypatch, tmp_path):
    src = write(tmp_path, "one.tab", ONE_STRING)
    out = tmp_path / "out.tab"
    assert run(monkeypatch, "-i", src, "-o", str(out), "-y", "--refinger") == 0
    text = out.read_text()
    assert "// Fingering: gtrsnipe's, not the source tab's own (--refinger)." in text
    assert [n[1] for n in notes(text)] != [4, 4, 4, 4]
    assert run(monkeypatch, "-i", src, "-o", str(out), "-y") == 0
    assert [(n[1], n[2]) for n in notes(out.read_text())] == [(4, 7), (4, 9), (4, 10), (4, 12)]


def midi_pitches(path):
    return sorted(m.note for t in mido.MidiFile(str(path)).tracks for m in t if m.type == "note_on")


def test_transpose_refingers_by_default_and_slides_with_no_refinger(monkeypatch, tmp_path, capsys):
    src = write(tmp_path, "one.tab", ONE_STRING)
    out, mid = tmp_path / "out.tab", tmp_path / "out.mid"
    assert run(monkeypatch, "-i", src, "-o", str(out), "-o", str(mid), "-y", "--transpose", "2") == 0
    assert "(--transpose changed the notes)" in out.read_text()
    assert midi_pitches(mid) == [54, 56, 57, 59]                # E F# G A, up a tone
    assert run(monkeypatch, "-i", src, "-o", str(out), "-o", str(mid), "-y",
               "--transpose", "2", "--no-refinger") == 0
    text = out.read_text()
    assert [(n[1], n[2]) for n in notes(text)] == [(4, 9), (4, 11), (4, 12), (4, 14)]
    assert "Fingering:" not in text and midi_pitches(mid) == [54, 56, 57, 59]
    capsys.readouterr()
    out.unlink()
    assert run(monkeypatch, "-i", src, "-o", str(out), "-y", "--transpose", "-8", "--no-refinger") == 1
    shown = capsys.readouterr()
    assert "can't stay on their string" in shown.out + shown.err and not out.exists()


def test_single_string_refingers_and_conflicts_with_no_refinger(monkeypatch, tmp_path, capsys):
    src = write(tmp_path, "three.tab", THREE)
    out = tmp_path / "out.tab"
    assert run(monkeypatch, "-i", src, "-o", str(out), "-y", "--single-string", "3") == 0
    assert "(--single-string)" in out.read_text()
    assert {n[1] for n in notes(out.read_text())} == {2}
    assert run(monkeypatch, "-i", src, "-o", str(out), "-y", "--single-string", "3", "--no-refinger") == 2
    assert "can't be combined with --no-refinger" in capsys.readouterr().err


def test_mapper_options_are_inert_on_a_kept_tab_and_it_says_so(monkeypatch, tmp_path, capsys):
    src = write(tmp_path, "one.tab", ONE_STRING)
    out = tmp_path / "out.tab"
    assert run(monkeypatch, "-i", src, "-o", str(out), "-y", "--prefer-open", "--sweet-spot-high", "5") == 0
    shown = capsys.readouterr()
    assert "Mapper options have no effect on it: --sweet-spot-high, --prefer-open" in shown.out + shown.err
    assert [(n[1], n[2]) for n in notes(out.read_text())] == [(4, 7), (4, 9), (4, 10), (4, 12)]
    assert run(monkeypatch, "-i", src, "-o", str(out), "-y", "--prefer-open", "--no-refinger") == 0
    shown = capsys.readouterr()
    assert "no effect" not in shown.out + shown.err             # you said so yourself


def test_a_capoed_tab_round_trips(monkeypatch, tmp_path):
    abc = write(tmp_path, "c.abc", "X:1\nT:c\nM:4/4\nL:1/4\nK:D\nD E F A|\n")
    tab, mid, again = tmp_path / "capo.tab", tmp_path / "capo.mid", tmp_path / "again.tab"
    assert run(monkeypatch, "-i", abc, "-o", str(tab), "-y", "--capo", "2") == 0
    assert "// Capo: 2nd Fret" in tab.read_text()
    assert run(monkeypatch, "-i", str(tab), "-o", str(mid), "-o", str(again), "-y") == 0
    assert midi_pitches(mid) == [62, 64, 66, 69]                # read with its own capo
    assert "// Capo: 2nd Fret" in again.read_text() and notes(again.read_text()) == notes(tab.read_text())
    assert run(monkeypatch, "-i", str(tab), "-o", str(mid), "-y", "--capo", "0") == 0
    assert midi_pitches(mid) == [60, 62, 64, 67]                # an explicit --capo 0 wins


def test_tuning_reads_the_fingering_but_refinger_keeps_the_notes(monkeypatch, tmp_path):
    low = HEADER + "e|----|\nB|----|\nG|----|\nD|----|\nA|-2--|\nE|-0-3|\n"          # E2+B2, then G2
    src = write(tmp_path, "low.tab", low)
    out, mid = tmp_path / "out.tab", tmp_path / "out.mid"
    # --tuning alone: the same fingering, read in drop D (the low string sounds a tone lower)
    assert run(monkeypatch, "-i", src, "-o", str(out), "-o", str(mid), "-y", "--tuning", "DROP_D") == 0
    assert midi_pitches(mid) == [38, 41, 47] and [(n[1], n[2]) for n in notes(out.read_text())] == [(4, 2), (5, 0), (5, 3)]
    # with --refinger: the same notes (read in the tab's own tuning), fingered for drop D
    assert run(monkeypatch, "-i", src, "-o", str(out), "-o", str(mid), "-y", "--tuning", "DROP_D", "--refinger") == 0
    text = out.read_text()
    assert midi_pitches(mid) == [40, 43, 47] and "// Tuning: D2,A2,D3,G3,B3,E4" in text
    assert (5, 2) in [(n[1], n[2]) for n in notes(text)]        # E2 is fret 2 on a low D


TRIAD = HEADER + """e|-------|
B|-8-----|
G|-9-----|
D|-10----|
A|-------|
E|-------|
"""


def test_a_chart_draws_the_tabs_own_shapes(tmp_path, capsys):
    from gtrsnipe.chords.cli import main
    src = write(tmp_path, "triad.tab", TRIAD)
    assert main([src]) == 0
    assert "**C** `x,x,10,9,8,x`" in capsys.readouterr().out    # C at the 8th fret, as written
    assert main([src, "--refinger"]) == 0
    assert "`x,x,10,9,8,x`" not in capsys.readouterr().out      # the mapper plays it lower


def test_foreign_tabs_with_padding_on_both_sides():
    rest = "".join(f"\n{s}|---------|" for s in "BGDAE")
    times = sorted(e.time for e in AsciiTabParser.parse("e|-5-7-8-5-|" + rest + "\n").tracks[0].events)
    assert times == [0, 1, 2, 3]                                # no header: slots end at the bar line
    rest = "".join(f"\n{s}|--------|" for s in "BGDAE")
    times = sorted(e.time for e in AsciiTabParser.parse("e|5-7-8-5-|" + rest + "\n").tracks[0].events)
    assert times == [0, 1, 2, 3]                                # or start at it


def test_the_player_shows_the_tab_as_written(tmp_path):
    from gtrsnipe.player.app import parse_and_map
    src = write(tmp_path, "one.tab", ONE_STRING)
    kept = parse_and_map(src, MapperConfig())
    assert [(e.string, e.fret) for e in kept.tracks[0].events] == [(4, 7), (4, 9), (4, 10), (4, 12)]
    again = parse_and_map(src, MapperConfig(), refinger=True)
    assert [(e.string, e.fret) for e in again.tracks[0].events] != [(4, 7), (4, 9), (4, 10), (4, 12)]


def test_every_command_adopts_a_tabs_own_tuning_and_capo(tmp_path):
    tab = HEADER.replace("E2,A2,D3,G3,B3,E4", "D2,A2,D3,G3,B3,E4").replace("// Tuning", "// Capo: 3rd Fret\n// Tuning") \
        + "e|-0-|\nB|---|\nG|---|\nD|---|\nA|---|\nE|---|\n"
    src = write(tmp_path, "dropd.tab", tab)
    args = setup_parser().parse_args(["-i", src])
    adopt_tab_header(args, src)
    assert args.tuning_pitches == "D2,A2,D3,G3,B3,E4" and args.capo == 3
    args = setup_parser().parse_args(["-i", src, "--tuning", "STANDARD", "--capo", "0"])
    adopt_tab_header(args, src)
    assert args.tuning_pitches is None and args.capo == 0       # explicit options win
    assert setup_parser().parse_args([]).refinger is None
    assert setup_parser().parse_args(["--no-refinger"]).refinger is False
