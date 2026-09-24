"""The CPU-decoupling regression guard (Epic A / decision D2).

These assert that the core MIDI/tab/abc/vex pipeline never imports torch,
tensorflow, librosa, numba, demucs, basic-pitch, onnxruntime, or scipy. They
run in clean child interpreters so the check is not polluted by whatever the
pytest process has already imported.
"""
from tests.conftest import HEAVY_MODULES, run_in_clean_interpreter


def test_core_import_loads_no_heavy_modules():
    result = run_in_clean_interpreter(
        f"""
        import sys
        import gtrsnipe.converter          # the module the CLI entrypoint lives in
        from gtrsnipe.formats import abc, mid, tab, vex
        heavy = {HEAVY_MODULES!r}
        leaked = sorted(set(heavy) & set(sys.modules))
        assert not leaked, f"heavy modules imported at core import: {{leaked}}"
        print("OK")
        """
    )
    assert result.returncode == 0, result.stderr
    assert "OK" in result.stdout


def test_midi_to_tab_run_loads_no_heavy_modules(scale_midi, tmp_path):
    out_tab = tmp_path / "scale.tab"
    result = run_in_clean_interpreter(
        f"""
        import sys, runpy
        sys.argv = ["gtrsnipe.converter", "-i", {str(scale_midi)!r},
                    "-o", {str(out_tab)!r}, "-y"]
        try:
            runpy.run_module("gtrsnipe.converter", run_name="__main__")
        except SystemExit:
            pass
        heavy = {HEAVY_MODULES!r}
        leaked = sorted(set(heavy) & set(sys.modules))
        assert not leaked, f"MIDI->tab run pulled heavy modules: {{leaked}}"
        print("OK")
        """
    )
    assert result.returncode == 0, result.stderr
    assert "OK" in result.stdout
    assert out_tab.exists(), "MIDI->tab conversion produced no output file"
