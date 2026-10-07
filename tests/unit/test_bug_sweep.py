"""The v0.6.19 bug sweep (backlog B08-B22): one test per fix."""
import importlib.util
import io
import logging
import sys

import mido
import pytest

from gtrsnipe.arguments import resolve_named_tuning, setup_parser
from gtrsnipe.core.keys import Key
from gtrsnipe.core.types import MusicalEvent, Song, Track
from gtrsnipe.formats.mid.reader import MidiReader
from gtrsnipe.formats.tab.generator.ascii import AsciiTabGenerator
from gtrsnipe.formats.tab.parser import AsciiTabParser

LOW = "X:1\nT:low\nM:4/4\nL:1/4\nK:C\nD,, E,, G,, c|\n"          # D2 is below a guitar's low E


def run(monkeypatch, *argv):
    """Run the converter's main(); return its exit status (0 if it just returns)."""
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


def tab_frets(path):
    return [int(x) for line in open(path) if "|" in line and not line.startswith("//")
            for x in __import__("re").findall(r"\d+", line.split("|", 1)[1])]


# -- B08 ---------------------------------------------------------------------------------

def test_a_failed_conversion_exits_nonzero(monkeypatch, tmp_path):
    bad = tmp_path / "bad.mid"
    bad.write_bytes(b"not a midi file")
    assert run(monkeypatch, "-i", str(bad), "-o", str(tmp_path / "o.tab"), "-y") == 1
    assert run(monkeypatch, "-i", str(tmp_path / "missing.mid"), "-o", str(tmp_path / "o.tab"), "-y") == 1
    good = write(tmp_path, "low.abc", LOW)
    assert run(monkeypatch, "-i", good, "-o", str(tmp_path / "o.tab"), "-y") == 0


# -- B09 ---------------------------------------------------------------------------------

@pytest.mark.parametrize("tuning, expect", [("STANDARD", "BASS_STANDARD"), ("DROP_D", "BASS_DROP_D"),
                                            ("E_FLAT", "BASS_E_FLAT"), ("BASS_DROP_D", "BASS_DROP_D")])
def test_bass_means_the_bass_version_of_the_tuning(tuning, expect):
    assert resolve_named_tuning(tuning, None, True) == (expect, 4)


def test_bass_with_a_tuning_that_has_no_bass_version_is_an_error(monkeypatch, tmp_path, capsys):
    with pytest.raises(ValueError, match="no bass version of OPEN_G"):
        resolve_named_tuning("OPEN_G", None, True)
    src = write(tmp_path, "low.abc", LOW)
    out = tmp_path / "b.tab"
    assert run(monkeypatch, "-i", src, "-o", str(out), "-y", "--bass", "--tuning", "BASS_DROP_D") == 0
    assert "// Tuning: D1,A1,D2,G2" in out.read_text()
    assert run(monkeypatch, "-i", src, "-o", str(out), "-y", "--bass", "--tuning", "OPEN_G") == 2
    assert "no bass version" in capsys.readouterr().err


# -- B10 ---------------------------------------------------------------------------------

def test_piano_tuning_passes_every_note_through_to_midi(monkeypatch, tmp_path, capsys):
    src = write(tmp_path, "wide.abc", "X:1\nT:wide\nM:4/4\nL:1/4\nK:C\nC,,, C c''' c|\n")
    out = tmp_path / "wide.mid"
    assert run(monkeypatch, "-i", src, "-o", str(out), "-y", "--tuning", "PIANO") == 0
    notes = sorted(m.note for t in mido.MidiFile(str(out)).tracks for m in t if m.type == "note_on")
    assert notes == [24, 60, 72, 108]                       # C1 and C8 are far outside a guitar
    assert run(monkeypatch, "-i", src, "-o", str(tmp_path / "wide.tab"), "-y", "--tuning", "PIANO") == 2
    assert "only be used with MIDI output" in capsys.readouterr().err


# -- B11 ---------------------------------------------------------------------------------

def test_transpose_happens_before_the_range_filter(monkeypatch, tmp_path):
    src = write(tmp_path, "low.abc", LOW)
    out = tmp_path / "low.tab"
    assert run(monkeypatch, "-i", src, "-o", str(out), "-y") == 0
    assert len(tab_frets(out)) == 3                         # D2 doesn't fit standard tuning
    assert run(monkeypatch, "-i", src, "-o", str(out), "-y", "--transpose", "2") == 0
    assert len(tab_frets(out)) == 4                         # as E2 it does


# -- B12 ---------------------------------------------------------------------------------

TAB = """// Tuning: {tuning}

e|-0-3-|
B|-----|
G|-----|
D|-----|
A|-----|
E|-----|
"""


def test_analyze_does_not_rank_a_named_tuning_twice(monkeypatch, tmp_path, capsys):
    src = write(tmp_path, "std.tab", TAB.format(tuning="E2,A2,D3,G3,B3,E4"))
    assert run(monkeypatch, "-i", src, "--analyze") == 0
    out = capsys.readouterr().out
    assert "CUSTOM" not in out and out.count(" STANDARD ") == 1 and "17 of 17 tunings" in out


def test_analyze_keeps_its_columns_with_a_long_custom_name(monkeypatch, tmp_path, capsys):
    src = write(tmp_path, "odd.tab", TAB.format(tuning="D2,G2,E3,F3,C4,D4"))
    assert run(monkeypatch, "-i", src, "--analyze") == 0
    lines = capsys.readouterr().out.splitlines()
    header = next(l for l in lines if l.lstrip().startswith("rank"))
    row = next(l for l in lines if "CUSTOM D2,G2,E3,F3,C4,D4" in l)
    plain = next(l for l in lines if " STANDARD " in l)
    assert header.index("strings") + len("strings") == row.index(" 6 ") + 2 == plain.index(" 6 ") + 2


# -- B13, B15 ----------------------------------------------------------------------------

EB = "X:1\nT:x\nM:4/4\nL:1/4\nK:Eb\n[E,G,B,]4 | [A,CE]4 | [B,DF_A]4 | [E,G,B,]4 |\n"


def test_a_chart_does_not_warn_about_its_own_diagram_search(tmp_path, caplog):
    from gtrsnipe.chords.cli import main
    src = write(tmp_path, "x.abc", EB)
    with caplog.at_level(logging.WARNING):
        assert main([src, "-o", str(tmp_path / "x.chords.md"), "--chart-voicing", "compact"]) == 0
    assert "Could not find a playable fingering" not in caplog.text
    assert logging.getLogger("gtrsnipe.guitar.mapper").level == logging.NOTSET      # restored


def test_one_saved_message_per_output(monkeypatch, tmp_path, capsys):
    src = write(tmp_path, "x.abc", EB)
    assert run(monkeypatch, "-i", src, "-o", str(tmp_path / "x.tab"), "-o", str(tmp_path / "x.mid"), "-y") == 0
    shown = capsys.readouterr()
    assert (shown.out + shown.err).count("Successfully saved") == 2      # one per file, not two


def test_no_output_produced_is_an_error(monkeypatch, tmp_path):
    from gtrsnipe.converter import MusicConverter
    monkeypatch.setattr(MusicConverter, "convert", lambda self, **kw: None)
    src = write(tmp_path, "x.abc", EB)
    out = tmp_path / "x.tab"
    assert run(monkeypatch, "-i", src, "-o", str(out), "-y") == 1 and not out.exists()


# -- B14 ---------------------------------------------------------------------------------

def test_a_missing_file_is_a_message_not_a_traceback(tmp_path, capsys):
    from gtrsnipe.chords.cli import main as chords_main
    from gtrsnipe.player.app import main as play_main
    missing = str(tmp_path / "nope.mid")
    assert play_main([missing]) == 1
    assert "gtrsnipe-play: can't read" in capsys.readouterr().err
    assert chords_main([missing]) == 1
    assert "gtrsnipe-chords: can't read" in capsys.readouterr().err


# -- B16, B17, B18, B20 ------------------------------------------------------------------

def test_research_profile_names_its_own_flags(capsys):
    from gtrsnipe.research.cli import main
    assert main(["profile", "C4 D4 E4", "C4 D4 E4 F4"]) == 1
    err = capsys.readouterr().err
    assert "--subdivide" in err and "--homograph-subdivide" not in err


def test_help_texts_say_what_the_option_does():
    from gtrsnipe.player.transport import HELP_TEXT
    action = next(a for a in setup_parser()._actions if "--mono-lowest-only" in a.option_strings)
    assert "ASCII tab output only" in action.help
    assert all(key in HELP_TEXT for key in ("enter", " p)", "home"))


def test_the_dead_clock_module_is_gone():
    assert importlib.util.find_spec("gtrsnipe.player.clock") is None


# -- B21 ---------------------------------------------------------------------------------

def onsets(events):
    return sorted({round(e.time, 4) for e in events})


def test_a_tab_gtrsnipe_wrote_reads_back_with_even_timing():
    # steady sixteenths that mix one- and two-digit frets, across barlines
    pitches = [64, 76, 79, 81, 64, 77, 81, 84] * 4
    song = Song(tracks=[Track(events=[MusicalEvent(i * 0.25, p, 0.25, 90) for i, p in enumerate(pitches)])])
    tab = AsciiTabGenerator.generate(song, "", max_line_width=60)
    assert any(len(str(f)) == 2 for f in [e.fret for e in AsciiTabParser.parse(tab).tracks[0].events])
    back = AsciiTabParser.parse(tab).tracks[0].events
    times = onsets(back)
    assert [e.pitch for e in sorted(back, key=lambda e: e.time)] == pitches
    assert {round(b - a, 4) for a, b in zip(times, times[1:])} == {0.25}


def test_a_chord_with_a_two_digit_fret_stays_one_chord():
    events = [MusicalEvent(i * 0.5, p, 0.5, 90) for i in range(8) for p in ((52, 76) if i % 2 else (55, 64))]
    tab = AsciiTabGenerator.generate(Song(tracks=[Track(events=events)]), "", max_line_width=60)
    back = AsciiTabParser.parse(tab).tracks[0].events
    times = onsets(back)
    assert len(times) == 8 and len({round(b - a, 4) for a, b in zip(times, times[1:])}) == 1


def test_a_tab_from_elsewhere_is_read_by_its_columns():
    def gaps(text):
        times = onsets(AsciiTabParser.parse(text).tracks[0].events)
        return [round(b - a, 3) for a, b in zip(times, times[1:])]
    rest = "\nB|----------|\nG|----------|\nD|----------|\nA|----------|\nE|----------|\n"
    header = "// Tuning: E2,A2,D3,G3,B3,E4\n\n"
    # no '// Tuning' header: fixed-width slots are even as they stand
    assert len(set(gaps("e|-5--12-7--|" + rest))) == 1
    # gtrsnipe's own layout puts the 7 one dash after the END of the 12
    assert len(set(gaps(header + "e|-5-12-7---|" + rest))) == 1
    # so each rule misreads the other's layout: the header is what tells them apart
    assert len(set(gaps("e|-5-12-7---|" + rest))) == 2
    assert len(set(gaps(header + "e|-5--12-7--|" + rest))) == 2


# -- B22 ---------------------------------------------------------------------------------

def test_key_signature_bytes():
    assert MidiReader._key_from_bytes(bytes([0xFD, 0])) == Key("Eb")            # three flats
    assert MidiReader._key_from_bytes(bytes([3, 1])) == Key("F#", "minor")
    assert MidiReader._key_from_bytes(bytes([0, 0])) == Key("C")
    assert MidiReader._key_from_bytes(bytes([9, 0])) is None and MidiReader._key_from_bytes(b"") is None


@pytest.mark.parametrize("name", ["Eb", "F#m", "Bbm"])
def test_the_fallback_midi_reader_survives_any_key_signature(tmp_path, name):
    """py-midi read a flat key's count as unsigned and lost the whole track. It still
    garbles a track's leading events (here it loses the key and the first note), which
    is parked: this only checks that a key signature no longer stops the fallback, and
    that no track is parsed twice."""
    mid = mido.MidiFile()
    track = mido.MidiTrack()
    mid.tracks.append(track)
    track.append(mido.MetaMessage("key_signature", key=name, time=0))
    for p in (60, 64, 67):
        track.append(mido.Message("note_on", note=p, velocity=90, time=0))
        track.append(mido.Message("note_off", note=p, velocity=0, time=480))
    path = tmp_path / "k.mid"
    mid.save(str(path))
    song = MidiReader._parse_with_py_midi(str(path), None)             # used to raise
    pitches = [e.pitch for t in song.tracks for e in t.events]
    assert pitches and set(pitches) <= {60, 64, 67} and len(pitches) == len(set(pitches))
    assert song.key in (None, mido_key(name))


def mido_key(name):
    from gtrsnipe.core.keys import parse_key
    return parse_key(name)
