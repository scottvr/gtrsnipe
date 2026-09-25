"""Regression: librosa relocated its tempo estimator across versions.

librosa.beat.tempo (<=0.9) -> librosa.feature.tempo (0.10) ->
librosa.feature.rhythm.tempo (1.x). The audio path crashed on librosa 1.0.0
with `module 'librosa.beat' has no attribute 'tempo'`. These tests are skipped
where librosa isn't installed (core stays torch/librosa-free).
"""
import pytest

librosa = pytest.importorskip("librosa")
np = pytest.importorskip("numpy")


def test_librosa_tempo_runs_on_current_librosa():
    from gtrsnipe.audio.tempo_detector import librosa_tempo
    sr = 22050
    # A 4-second click-ish signal so tempo estimation has something to chew on.
    t = np.linspace(0, 4.0, sr * 4, endpoint=False)
    y = (np.sin(2 * np.pi * 110 * t) *
         (np.mod(t, 0.5) < 0.05)).astype(np.float32)  # pulse every 0.5s
    result = librosa_tempo(y, sr)
    assert float(result[0]) > 0  # a positive BPM, no AttributeError


def test_librosa_tempo_raises_clearly_if_no_estimator(monkeypatch):
    # If a future librosa removes every known location, fail with a clear message.
    import gtrsnipe.audio.tempo_detector as td

    class Empty:
        feature = None
        beat = None
    monkeypatch.setattr(td, "librosa", Empty)
    with pytest.raises(AttributeError, match="no tempo estimator"):
        td.librosa_tempo([0.0], 22050)
