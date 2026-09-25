"""Golden-output regression gate, driven by profiles (opt-in, local fixtures).

Each *case* is a directory under the golden dir (``$GTRSNIPE_GOLDEN_DIR`` or
``tests/golden/cases/``, which is gitignored — inputs may be copyrighted). A case
contains:

    input.<ext>        exactly one input file (.mid/.abc/.vex/.tab/.wav/…)
    profile            (optional) a .gtrsnipe profile file with the option set
    expected.<ext>     one or more committed golden outputs (.tab/.mid/.abc/.vex/
                       .chords.md); each is produced and compared

For every ``expected.*`` the harness runs the real CLI
``python -m gtrsnipe.converter -i input -o out.<ext> [--config-dir CASE --profile profile]``
and compares. Text outputs are normalized to drop the volatile
``// Transcribed with: …`` command echo (the only line that legitimately varies by
path). If no fixtures are present the whole gate is skipped, so public CI stays
green without shipping sample files.

To add a case: `mkdir tests/golden/cases/asturias`, drop in your `input.mid`, save
your tuned options with `gtrsnipe … --save-args profile` (move it in), then
generate and eyeball `expected.tab` once and commit *the profile* (not the input).
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
_GOLDEN_DIR = Path(os.environ.get("GTRSNIPE_GOLDEN_DIR",
                                  Path(__file__).parent / "cases"))
_TEXT_SUFFIXES = (".tab", ".abc", ".vex", ".md")


def _cases():
    if not _GOLDEN_DIR.is_dir():
        return []
    return [d for d in sorted(_GOLDEN_DIR.iterdir())
            if d.is_dir() and list(d.glob("expected.*"))]


def _normalize(text: str) -> str:
    # The command echo embeds absolute paths/args; ignore it (and trailing space).
    return "\n".join(ln.rstrip() for ln in text.splitlines()
                     if not ln.startswith("// Transcribed with:"))


_CASES = _cases()


@pytest.mark.skipif(not _CASES, reason="no golden fixtures present (see tests/golden/README.md)")
@pytest.mark.parametrize("case", _CASES or [None],
                         ids=[c.name for c in _CASES] or ["none"])
def test_golden(case, tmp_path):
    inputs = [p for p in case.glob("input.*") if p.is_file()]
    assert len(inputs) == 1, f"{case.name}: need exactly one input.* file, found {inputs}"
    inp = inputs[0]

    env = dict(os.environ)
    env["PYTHONPATH"] = str(_REPO_ROOT) + os.pathsep + env.get("PYTHONPATH", "")

    for exp in sorted(case.glob("expected.*")):
        suffix = exp.name[len("expected"):]        # ".tab" or ".chords.md"
        out = tmp_path / ("out" + suffix)
        cmd = [sys.executable, "-m", "gtrsnipe.converter",
               "-i", str(inp), "-o", str(out), "-y"]
        if (case / "profile").is_file():
            cmd += ["--config-dir", str(case), "--profile", "profile"]

        r = subprocess.run(cmd, capture_output=True, text=True, env=env)
        assert out.exists(), (
            f"{case.name}{suffix}: output not produced (rc={r.returncode})\n{r.stderr}")

        is_text = out.name.endswith(_TEXT_SUFFIXES)
        if is_text:
            got, want = _normalize(out.read_text()), _normalize(exp.read_text())
        else:
            got, want = out.read_bytes(), exp.read_bytes()
        assert got == want, f"{case.name}{suffix} differs from its golden"
