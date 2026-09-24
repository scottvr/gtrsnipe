"""Shared pytest fixtures for the gtrsnipe suite.

The whole tier here is torch-free: every fixture and helper uses only core
dependencies (midiutil/MIDIFile/mido/numpy), so `pytest` runs green on a
CPU-only install with no audio/ML extras present.
"""
import subprocess
import sys
import textwrap

import pytest

# Heavy modules that must never be imported by the core MIDI/tab/abc/vex path.
HEAVY_MODULES = [
    "torch", "torchaudio", "tensorflow", "librosa",
    "numba", "demucs", "basic_pitch", "onnxruntime", "scipy",
]


@pytest.fixture
def scale_midi(tmp_path):
    """Write a one-octave C-major scale to a .mid file and return its path.

    Uses midiutil directly (a core dep) so the fixture needs no committed
    sample files and no audio extras.
    """
    from midiutil import MIDIFile

    path = tmp_path / "scale.mid"
    midi = MIDIFile(1)
    midi.addTempo(0, 0, 120)
    for i, pitch in enumerate([60, 62, 64, 65, 67, 69, 71, 72]):
        midi.addNote(0, 0, pitch, i * 0.5, 0.5, 100)
    with open(path, "wb") as fh:
        midi.writeFile(fh)
    return path


def run_in_clean_interpreter(code: str):
    """Run `code` in a fresh child interpreter and return the CompletedProcess.

    A child process is the only reliable way to assert on sys.modules: the
    pytest process itself may already have imported heavy modules (e.g. scipy is
    pulled in by unrelated plugins or an [audio] install), which would produce
    false positives for an in-process check.
    """
    return subprocess.run(
        [sys.executable, "-c", textwrap.dedent(code)],
        capture_output=True,
        text=True,
    )
