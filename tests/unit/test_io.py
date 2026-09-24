"""Unit tests for text/MIDI IO helpers."""
import pytest

from gtrsnipe.utils.io import read_text_file, save_midi_file, save_text_file


def test_save_and_read_round_trip(tmp_path):
    path = tmp_path / "out.tab"
    save_text_file("hello\nworld", str(path))
    assert path.read_text() == "hello\nworld"


def test_save_text_creates_parent_dirs(tmp_path):
    path = tmp_path / "nested" / "deep" / "out.txt"
    save_text_file("data", str(path))
    assert path.exists()
    assert path.read_text() == "data"


def test_read_text_file_strips_comments_and_whitespace(tmp_path):
    path = tmp_path / "in.tab"
    path.write_text("// a comment\n# another\nreal content\n  \n")
    assert read_text_file(str(path)) == "real content"


def test_read_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        read_text_file(str(tmp_path / "does-not-exist.tab"))


def test_save_midi_file_round_trip(tmp_path):
    from midiutil import MIDIFile

    midi = MIDIFile(1)
    midi.addTempo(0, 0, 120)
    midi.addNote(0, 0, 60, 0, 1, 100)
    path = tmp_path / "out.mid"
    save_midi_file(midi, str(path))
    assert path.exists()
    # A valid Standard MIDI File starts with the "MThd" header chunk.
    assert path.read_bytes()[:4] == b"MThd"
