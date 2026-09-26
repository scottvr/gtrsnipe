"""MidiReader container handling: RIFF 'RMID' wrappers, junk prefixes, and
non-MIDI files (which used to come back as silently EMPTY songs)."""
import struct

import pytest

from gtrsnipe.formats.mid.reader import MidiReader


def _pitches(song):
    return [e.pitch for t in song.tracks for e in sorted(t.events, key=lambda e: e.time)]


def _riff_rmid(smf: bytes) -> bytes:
    """Wrap SMF bytes the way .rmi files do: RIFF <size> RMID, then a 'data' chunk
    (padded to an even length)."""
    data = b"data" + struct.pack("<I", len(smf)) + smf + (b"\x00" if len(smf) % 2 else b"")
    return b"RIFF" + struct.pack("<I", 4 + len(data)) + b"RMID" + data


def test_plain_smf_still_parses(scale_midi):
    assert _pitches(MidiReader.parse(str(scale_midi), None)) == [60, 62, 64, 65, 67, 69, 71, 72]


def test_riff_wrapped_midi_is_read(scale_midi, tmp_path):
    # review: the py-midi fallback "succeeded" on these with 0 tracks / 0 notes
    rmi = tmp_path / "wrapped.mid"
    rmi.write_bytes(_riff_rmid(scale_midi.read_bytes()))
    assert _pitches(MidiReader.parse(str(rmi), None)) == [60, 62, 64, 65, 67, 69, 71, 72]


def test_riff_chunk_before_data_is_skipped(scale_midi, tmp_path):
    smf = scale_midi.read_bytes()
    info = b"LIST" + struct.pack("<I", 5) + b"INFO!" + b"\x00"   # odd size -> pad byte
    data = b"data" + struct.pack("<I", len(smf)) + smf
    body = b"RMID" + info + data
    rmi = tmp_path / "list_then_data.rmi"
    rmi.write_bytes(b"RIFF" + struct.pack("<I", len(body)) + body)
    assert len(_pitches(MidiReader.parse(str(rmi), None))) == 8


def test_junk_prefix_before_header_is_skipped(scale_midi, tmp_path):
    f = tmp_path / "macbinary.mid"
    f.write_bytes(b"\x00" * 128 + scale_midi.read_bytes())     # e.g. a MacBinary header
    assert len(_pitches(MidiReader.parse(str(f), None))) == 8


@pytest.mark.parametrize("head", [b"CAKEWALK\x1a\x00", b"STAR DATA V3.50\x1a",
                                  b"<!DOCTYPE html><html>", b"\x00" * 2048])
def test_non_midi_raises_instead_of_returning_an_empty_song(tmp_path, head):
    f = tmp_path / "not_midi.mid"
    f.write_bytes(head + b"\x00" * 64)
    with pytest.raises(ValueError, match="not a MIDI file"):
        MidiReader.parse(str(f), None)


def test_riff_without_midi_data_raises(tmp_path):
    f = tmp_path / "empty.rmi"
    f.write_bytes(b"RIFF" + struct.pack("<I", 4) + b"RMID")
    with pytest.raises(ValueError, match="without a MIDI 'data' chunk"):
        MidiReader.parse(str(f), None)
