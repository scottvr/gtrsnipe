"""C05/F02: the key through the formats: ABC and MIDI in and out, charts, tabs, the CLI."""
import io
import sys

import mido
import pytest

from gtrsnipe.chords.chart import build_chord_sheet
from gtrsnipe.converter import MusicConverter, transpose_song
from gtrsnipe.core.config import MapperConfig
from gtrsnipe.core.keys import DOUBTED, FROM_FILE, FROM_OPTION, Key, parse_key
from gtrsnipe.core.theory import note_name_to_pitch as n
from gtrsnipe.core.types import MusicalEvent, Song, Track
from gtrsnipe.formats.abc.generator import AbcGenerator
from gtrsnipe.formats.abc.parser import AbcParser
from gtrsnipe.formats.mid.generator import MidiGenerator
from gtrsnipe.formats.mid.reader import MidiReader
from gtrsnipe.formats.tab.generator.ascii import AsciiTabGenerator


def melody(names, key=None, source=FROM_OPTION):
    events = [MusicalEvent(i * 0.5, n(x), 0.5, 90) for i, x in enumerate(names.split())]
    song = Song(tracks=[Track(events=events)], title="t")
    if key:
        song.key, song.key_source = parse_key(key), source
    return song


def chords(*bars, key=None):
    events = [MusicalEvent(4.0 * i, n(x), 4.0, 90) for i, bar in enumerate(bars) for x in bar.split()]
    song = Song(tracks=[Track(events=events)], title="t")
    if key:
        song.key, song.key_source = parse_key(key), FROM_FILE
    return song


FLAT_TUNE = "Eb4 G4 Bb4 Ab4 A4 Ab4 G4 F4 E4 Eb5 D5 Db5 B4 B4 C5 Bb3"


# -- ABC -----------------------------------------------------------------------------------

@pytest.mark.parametrize("key", ["Eb", "E", "C", "Gb", "C#", "F#m", "D dorian"])
def test_abc_output_reads_back_the_same_under_every_accidental_rule(key):
    song = melody(FLAT_TUNE, key)
    text = AbcGenerator.generate(song, "1/8")
    assert f"K:{parse_key(key).abc}" in text.splitlines()
    for rule in ("not", "octave", "pitch"):
        back = AbcParser.parse(text, propagate_accidentals=rule)
        assert [e.pitch for e in back.tracks[0].events] == [e.pitch for e in song.tracks[0].events]
    assert AbcParser.parse(text).key == parse_key(key)


def test_abc_writes_the_key_signature_not_every_accidental():
    body = AbcGenerator.generate(melody("Eb4 G4 Bb4 Ab4", "Eb"), "1/8").splitlines()[-1]
    assert body.split()[:4] == ["E", "G", "B", "A"]                  # the flats are in K:Eb
    body = AbcGenerator.generate(melody("Eb4 E4 Eb4 F4 | Eb4".replace("| ", ""), "Eb"), "1/8")
    assert body.splitlines()[-1].split()[:3] == ["E", "=E", "_E"]    # natural, then the flat again
    c = AbcGenerator.generate(melody("Bb3 Eb4 F#4", "C"), "1/8").splitlines()[-1].split()
    assert c[:3] == ["_B,", "_E", "^F"]                              # flats in C, where C spells flats


def test_abc_octaves_follow_the_letter():
    # Cb4 is the pitch B3 (in Gb major), B#3 the pitch C4 (in C# major)
    for key, pitch, note in (("Gb", n("B3"), "C"), ("C#", n("C4"), "B,")):
        song = Song(tracks=[Track(events=[MusicalEvent(0, pitch, 1, 90)])], key=parse_key(key),
                    key_source=FROM_FILE)
        text = AbcGenerator.generate(song, "1/4")
        assert text.splitlines()[-1].split()[0] == note
        assert AbcParser.parse(text).tracks[0].events[0].pitch == pitch


def test_abc_estimates_the_key_and_says_so():
    text = AbcGenerator.generate(melody("Eb4 G4 Bb4 Ab4 F4 D4 Eb4 Bb3 C4 Ab4 G4 Eb4"))
    lines = text.splitlines()
    assert "K:Eb" in lines and lines[lines.index("K:Eb") - 1].startswith("% key estimated")
    assert "% key estimated" not in AbcGenerator.generate(melody(FLAT_TUNE, "Eb"))


def test_abc_input_keeps_its_key():
    song = AbcParser.parse("X:1\nT:x\nM:4/4\nL:1/4\nK:Bb\nB,DFB|\n")
    assert song.key == Key("Bb") and song.key_source == FROM_FILE
    assert AbcParser.parse("X:1\nK:Ador\nA2|\n").key == Key("A", "dorian")
    assert AbcParser.parse("X:1\nK:HP\nA2|\n").key is None


# -- MIDI ----------------------------------------------------------------------------------

def midi_bytes(key=None, notes=(60, 64, 67)):
    mid = mido.MidiFile()
    track = mido.MidiTrack()
    mid.tracks.append(track)
    if key:
        track.append(mido.MetaMessage("key_signature", key=key, time=0))
    for p in notes:
        track.append(mido.Message("note_on", note=p, velocity=90, time=0))
        track.append(mido.Message("note_off", note=p, velocity=0, time=480))
    buf = io.BytesIO()
    mid.save(file=buf)
    return buf.getvalue()


def read_midi(tmp_path, data):
    path = tmp_path / "x.mid"
    path.write_bytes(data)
    return MidiReader.parse(str(path), None)


def test_midi_key_signature_is_read(tmp_path):
    song = read_midi(tmp_path, midi_bytes("Eb"))
    assert song.key == Key("Eb") and song.key_source == FROM_FILE
    assert read_midi(tmp_path, midi_bytes("F#m")).key == Key("F#", "minor")
    assert read_midi(tmp_path, midi_bytes(None)).key is None
    assert read_midi(tmp_path, midi_bytes("C")).key_source == DOUBTED     # a likely default


def test_midi_output_carries_the_songs_own_key(tmp_path):
    def written_key(song):
        path = tmp_path / "out.mid"
        with open(path, "wb") as f:
            MidiGenerator.generate(song).writeFile(f)
        return [m.key for t in mido.MidiFile(str(path)).tracks for m in t
                if m.is_meta and m.type == "key_signature"]
    assert written_key(melody("Eb4 G4 Bb4", "Eb")) == ["Eb"]
    assert written_key(melody("A3 C4 E4", "Am")) == ["Am"]
    assert written_key(melody("Eb4 G4 Bb4")) == []                        # never an estimate
    assert written_key(melody("C4 E4 G4", "C", DOUBTED)) == []


# -- charts, tabs, transposing -------------------------------------------------------------

def test_a_chart_spells_in_the_songs_key_and_names_it():
    song = chords("Eb2 G2 Bb2", "Ab2 C3 Eb3", "Bb2 D3 F3 Ab3", key="Eb")
    sheet = build_chord_sheet(song, MapperConfig())
    assert "Eb major (from the file)" in sheet
    assert "| Eb  | Ab  | Bb7 |" in sheet
    sharp = build_chord_sheet(chords("E2 G#2 B2", "G#2 B2 D#3", key="E"), MapperConfig())
    assert "| E   | G#m |" in sharp


def test_a_chart_estimates_the_key_and_says_so():
    sheet = build_chord_sheet(chords("Eb2 G2 Bb2", "Ab2 C3 Eb3", "Bb2 D3 F3 Ab3", "Eb2 G2 Bb2"),
                              MapperConfig())
    assert "Eb major (estimated from the notes)" in sheet and "| Ab " in sheet


def test_a_tab_says_which_key_its_chord_names_are_spelled_in():
    song = chords("Eb3 G3 Bb3", "Ab2 C3 Eb3", key="Eb")
    tab = AsciiTabGenerator.generate(song, "", max_line_width=200, name_chords=True)
    assert "// Chord names are spelled in Eb major (from the file)." in tab
    names = [l.split() for l in tab.splitlines() if l.strip() and "|" not in l and not l.startswith("//")]
    assert names[0] == ["Eb", "Ab"]
    plain = AsciiTabGenerator.generate(song, "", max_line_width=200)
    assert "Chord names" not in plain                                      # only with --name-chords


def test_transposing_moves_the_key():
    song = chords("Eb2 G2 Bb2", "Ab2 C3 Eb3", key="Eb")
    transpose_song(song, 2)
    assert song.key == Key("F") and song.key_source == "from the file, transposed"
    assert [e.pitch for e in song.tracks[0].events][:3] == [n("F2"), n("A2"), n("C3")]
    doubted = melody("C4 E4 G4", "C", DOUBTED)
    transpose_song(doubted, 2)
    assert doubted.key is None                                             # estimate afresh


# -- the command line ----------------------------------------------------------------------

def run(monkeypatch, capsys, *argv):
    from gtrsnipe.converter import main
    monkeypatch.setattr(sys, "argv", ["gtrsnipe", *argv])
    try:
        main()
    except SystemExit:
        pass
    return capsys.readouterr()


ABC = "X:1\nT:x\nM:4/4\nL:1/4\nK:Eb\n[E,G,B,]4 | [A,CE]4 | [B,DF_A]4 | [E,G,B,]4 |\n"


def test_cli_key_option(monkeypatch, capsys, tmp_path):
    src = tmp_path / "x.abc"
    src.write_text(ABC)
    out = tmp_path / "x.chords.md"
    run(monkeypatch, capsys, "-i", str(src), "-o", str(out), "-y", "--key", "D#m")
    assert "D# minor (from --key)" in out.read_text()
    run(monkeypatch, capsys, "-i", str(src), "-o", str(out), "-y", "--key", "auto")
    assert "Eb major (estimated from the notes)" in out.read_text()
    run(monkeypatch, capsys, "-i", str(src), "-o", str(out), "-y")
    assert "Eb major (from the file)" in out.read_text()
    err = run(monkeypatch, capsys, "-i", str(src), "-o", str(out), "-y", "--key", "D# major").err
    assert "use Eb major" in err


def test_cli_transpose_reaches_the_chord_chart(monkeypatch, capsys, tmp_path):
    src = tmp_path / "x.abc"
    src.write_text(ABC)
    out = tmp_path / "x.chords.md"
    run(monkeypatch, capsys, "-i", str(src), "-o", str(out), "-y", "--transpose", "2")
    sheet = out.read_text()
    assert "F major (from the file, transposed)" in sheet and "| F  | Bb | C7 | F  |" in sheet


def test_cli_name_chord_with_a_key(monkeypatch, capsys):
    out = run(monkeypatch, capsys, "--key", "Db", "--name-chord", "x46664").out
    assert "Db3 Ab3 Db4 F4 Ab4" in out and "spelled in Db major" in out
    out = run(monkeypatch, capsys, "--name-chord", "x46664", "--name-chord", "x32033").out
    assert " Db " in out and "Cadd9" in out and "spelled in" not in out


def test_chords_cli_takes_the_key(tmp_path, capsys):
    from gtrsnipe.chords.cli import main
    src = tmp_path / "x.abc"
    src.write_text(ABC)
    main([str(src), "--key", "D#m"])
    assert "D# minor (from --key)" in capsys.readouterr().out
