"""Every gtrsnipe subpackage must be packaged. The find pattern used to be
``include = ["gtrsnipe"]``, which matches the top-level package only: a wheel
(any non-editable ``pip install``) shipped 3 modules and none of formats/,
guitar/, player/... This mirrors setuptools' fnmatch rule without building."""
from fnmatch import fnmatchcase
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def test_every_subpackage_matches_the_find_patterns():
    tomllib = pytest.importorskip("tomllib")
    cfg = tomllib.loads((ROOT / "pyproject.toml").read_text())
    find = cfg["tool"]["setuptools"]["packages"]["find"]
    include, exclude = find.get("include", ["*"]), find.get("exclude", [])
    packages = sorted({".".join(p.parent.relative_to(ROOT).parts)
                       for p in (ROOT / "gtrsnipe").rglob("*.py")
                       if "__pycache__" not in p.parts})
    assert "gtrsnipe.formats.tab.generator" in packages
    missing = [p for p in packages
               if not any(fnmatchcase(p, pat) for pat in include)
               or any(fnmatchcase(p, pat) for pat in exclude)]
    assert missing == []
