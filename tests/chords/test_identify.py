"""Tests for chord identification (pure pitch-class matching)."""
import pytest

from gtrsnipe.core.chords import Chord, identify

# MIDI reference: C4=60. Pitch classes: C=0 ... B=11.
C, Cs, D, Ds, E, F, Fs, G, Gs, A, As, B = range(60, 72)


def name_of(pitches, bass=None):
    ch = identify(pitches, bass=bass)
    return ch.name if ch else None


# -- triads -----------------------------------------------------------------

def test_major_triad():
    assert name_of([C, E, G]) == "C"


def test_minor_triad():
    assert name_of([A, C + 12, E + 12]) == "Am"


def test_major_triad_any_octave_and_order():
    assert name_of([G + 12, B, D + 12]) == "G"


# -- power chords -----------------------------------------------------------

def test_power_chord_root_and_fifth_only():
    assert name_of([C, G]) == "C5"


def test_power_chord_beats_major_when_third_absent():
    # {root, fifth} must not be mislabeled as a major triad with a missing 3rd.
    assert name_of([E, B]) == "E5"


# -- sevenths ---------------------------------------------------------------

def test_dominant_seventh():
    assert name_of([E, Gs, B, D + 12]) == "E7"


def test_major_seventh():
    assert name_of([C, E, G, B]) == "Cmaj7"


def test_minor_seventh():
    assert name_of([A, C + 12, E + 12, G + 12]) == "Am7"


# -- sus / robustness -------------------------------------------------------

def test_sus4():
    # {C,F,G} is ambiguous (== Fsus2); the bass note resolves it to Csus4.
    assert name_of([C, F, G], bass=C) == "Csus4"


def test_extra_melody_note_does_not_break_the_triad():
    # C major with an added D (a passing melody tone) is still "C".
    assert name_of([C, D, E, G]) == "C"


# -- inversions / slash chords ---------------------------------------------

def test_slash_chord_uses_bass():
    # C major voiced over E in the bass -> C/E.
    assert name_of([C, E, G], bass=E) == "C/E"


def test_root_position_has_no_slash():
    assert name_of([C, E, G], bass=C) == "C"


# -- non-chords -------------------------------------------------------------

def test_single_note_is_not_a_chord():
    assert identify([C]) is None


def test_empty_is_not_a_chord():
    assert identify([]) is None


def test_unison_across_octaves_is_not_a_chord():
    assert identify([C, C + 12, C + 24]) is None


# -- Chord dataclass --------------------------------------------------------

def test_chord_name_property():
    assert Chord(root=2, quality="m7").name == "Dm7"
    assert Chord(root=0, quality="", bass=4).name == "C/E"
    assert Chord(root=0, quality="", bass=0).name == "C"  # bass==root: no slash
