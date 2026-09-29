"""The Demucs wrapper: importable without a NameError, and 'guitar' maps to the right stem.

demucs itself is an optional heavy extra, so it is stubbed here."""
import importlib
import importlib.machinery
import sys
import types

import pytest


@pytest.fixture
def separator(monkeypatch, tmp_path):
    calls = []
    demucs = types.ModuleType("demucs")
    demucs.__spec__ = importlib.machinery.ModuleSpec("demucs", None)
    sep = types.ModuleType("demucs.separate")
    sep.__spec__ = importlib.machinery.ModuleSpec("demucs.separate", None)

    def fake_main(args):
        calls.append(args)
        stem, model, out, audio = args[1], args[3], args[5], args[6]
        path = tmp_path / out / model / "song"
        path.mkdir(parents=True, exist_ok=True)
        (path / f"{stem}.wav").write_bytes(b"")
    sep.main = fake_main
    monkeypatch.setitem(sys.modules, "demucs", demucs)
    monkeypatch.setitem(sys.modules, "demucs.separate", sep)
    monkeypatch.delitem(sys.modules, "gtrsnipe.audio.separator", raising=False)
    monkeypatch.chdir(tmp_path)
    mod = importlib.import_module("gtrsnipe.audio.separator")   # used to raise NameError
    return mod, calls


@pytest.mark.parametrize("model, stem", [("htdemucs", "other"), ("htdemucs_ft", "other"),
                                         ("htdemucs_6s", "guitar")])
def test_guitar_maps_to_the_right_stem(separator, model, stem):
    mod, calls = separator
    out = mod.separate_instrument("song.wav", "guitar", model)
    assert calls[-1][1] == stem and out.endswith(f"{model}/song/{stem}.wav")


def test_other_instruments_pass_through(separator):
    mod, calls = separator
    mod.separate_instrument("song.wav", "bass", "htdemucs")
    assert calls[-1][1] == "bass"
