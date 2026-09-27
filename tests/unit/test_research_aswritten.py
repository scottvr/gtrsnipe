"""Published tabs as written (backlog R05): reading a tab's fingering, finding
evenly spaced corpus passages, the per-string constancy test, the trivial and
'itself' cases, and the solver hand-off."""
import gzip
import json

import numpy as np
import pytest

from gtrsnipe.research import aswritten as W
from gtrsnipe.research import corpus as C
from gtrsnipe.research.cli import main as research_main

Q = C.TPQ
# 8 steady notes alternating the high e and B strings
TAB = """// Tuning: E2,A2,D3,G3,B3,E4

e|--0-----3-----5-----3-----|
B|-----1-----3-----1-----0--|
G|--------------------------|
D|--------------------------|
A|--------------------------|
E|--------------------------|
"""
A = [64, 60, 67, 62, 69, 60, 67, 59]          # E4 C4 G4 D4 A4 C4 G4 B3
PARTNER = [a + (2 if i % 2 == 0 else -3) for i, a in enumerate(A)]   # e string +2, B string -3


def mel(id_, pitches, step=Q // 2, corpus="t"):
    return C.Melody(id_, corpus, list(pitches), [i * step for i in range(len(pitches))],
                    [step] * len(pitches), title=id_)


@pytest.fixture
def tab_file(tmp_path):
    p = tmp_path / "t.tab"
    p.write_text(TAB)
    return p


def test_read_tab_keeps_the_fingering(tab_file):
    t = W.read_tab(str(tab_file))
    assert t.pitches.tolist() == A
    assert t.strings.tolist() == [0, 1] * 4 and t.frets.tolist() == [0, 1, 3, 3, 5, 1, 3, 0]
    assert not t.chord_at.any() and t.open_pitches == [64, 59, 55, 50, 45, 40]


def test_even_windows_only_take_evenly_spaced_notes():
    m = C.Melody("x", "t", [60, 62, 64, 65, 67, 69], [0, 240, 480, 720, 1200, 1440], [240] * 6)
    P, refs = W.even_windows([m], 3)
    assert refs[:, 1].tolist() == [0, 1] and P.tolist() == [[60, 62, 64], [62, 64, 65]]


def test_scan_finds_the_as_written_partner_and_counts_transpositions(tab_file):
    t = W.read_tab(str(tab_file))
    mels = [mel("partner", PARTNER), mel("same", [a + 5 for a in A]),
            mel("other", [60, 61, 62, 63, 64, 65, 66, 67]),
            mel("uneven", PARTNER, step=0)]              # step 0 -> not a real passage
    mels[3].onsets = [0, 240, 720, 960, 1200, 1680, 1920, 2400]
    res, hits = W.scan_tab(t, mels, [8])
    r = res[8]
    assert r.windows == 1 and r.as_written == 1 and r.itself == 1 and r.trivial == 0
    assert r.itself_found == ["t:same"]
    (h,) = hits
    assert h.ref == "t:partner@1-8" and h.richness == 2 and h.strings == 2 and h.pairs == 6
    assert sorted(set(h.offsets)) == [-3, 2]


def test_one_pitch_per_string_is_trivial(tmp_path):
    p = tmp_path / "t.tab"                     # e string always open, B string always fret 1
    p.write_text(TAB.replace("3-----5-----3", "0-----0-----0")
                    .replace("-1-----3-----1-----0-", "-1-----1-----1-----1-"))
    t = W.read_tab(str(p))
    assert len(set(zip(t.strings.tolist(), t.pitches.tolist()))) == 2
    other = [70, 50, 70, 50, 70, 50, 70, 50]   # any two alternating pitches will do
    res, _ = W.scan_tab(t, [mel("b", other)], [8])
    assert res[8].as_written == 1 and res[8].trivial == 1 and res[8].unrelated == 0


def test_solver_confirms_the_hit(tab_file):
    t = W.read_tab(str(tab_file))
    mels = [mel("partner", PARTNER)]
    _, (h,) = W.scan_tab(t, mels, [8])
    out = W.solve_hit(t, h, {m.ref: m for m in mels})
    assert out["aligned"] and out["as_written"], out["reason"]
    # B may be transposed as a whole, so only the strings' relative retune is fixed: e +2, B -3
    assert out["retunes"][0] - out["retunes"][1] == 5


def test_cli_aswritten(tab_file, tmp_path, capsys):
    path = tmp_path / "c.jsonl.gz"
    head = {"format": C.CACHE_FORMAT, "version": C.CACHE_VERSION, "corpus": "t", "tpq": C.TPQ,
            "about": "", "built": "", "gtrsnipe": "", "files": 0, "melodies": 2, "errors": 0,
            "error_sample": []}
    with gzip.open(path, "wt") as f:
        f.write(json.dumps(head) + "\n")
        for m in (mel("partner", PARTNER), mel("other", list(range(60, 68)))):
            f.write(m.to_json() + "\n")
    out = tmp_path / "r.json"
    assert research_main(["aswritten", str(tab_file), "--corpora", str(path), "--lengths", "8",
                          "--json", str(out)]) == 0
    text = capsys.readouterr().out
    assert "t.tab: 8 notes on 2 strings" in text and "t:partner@1-8" in text
    assert json.loads(out.read_text())["tabs"]["t.tab"]["results"]["8"]["as_written"] == 1
