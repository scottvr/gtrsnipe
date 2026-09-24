"""Unit tests for core music theory helpers (pure functions, no I/O)."""
import pytest

from gtrsnipe.core.theory import (
    midi_to_hz,
    note_name_to_pitch,
    pitch_to_note_name,
)


@pytest.mark.parametrize(
    "name,pitch",
    [
        ("C4", 60),
        ("A4", 69),
        ("C-1", 0),
        ("G9", 127),
        ("C#5", 73),
        ("Db5", 73),   # enharmonic with C#5
        ("Eb3", 51),
    ],
)
def test_note_name_to_pitch(name, pitch):
    assert note_name_to_pitch(name) == pitch


def test_note_name_to_pitch_rejects_garbage():
    with pytest.raises(ValueError):
        note_name_to_pitch("not-a-note")


@pytest.mark.parametrize(
    "pitch,name",
    [
        (60, "C4"),
        (69, "A4"),
        (0, "C-1"),
        (127, "G9"),
        (61, "C#4"),
    ],
)
def test_pitch_to_note_name(pitch, name):
    assert pitch_to_note_name(pitch) == name


def test_pitch_to_note_name_out_of_range():
    assert pitch_to_note_name(-1) == "Invalid Pitch"
    assert pitch_to_note_name(128) == "Invalid Pitch"


def test_name_pitch_round_trip():
    # Natural notes round-trip exactly (no enharmonic ambiguity).
    for pitch in range(0, 128):
        name = pitch_to_note_name(pitch)
        assert note_name_to_pitch(name) == pitch


def test_midi_to_hz_a440():
    assert midi_to_hz(69) == pytest.approx(440.0)
    assert midi_to_hz(60) == pytest.approx(261.6256, rel=1e-4)
    # One octave up doubles the frequency.
    assert midi_to_hz(81) == pytest.approx(880.0)
