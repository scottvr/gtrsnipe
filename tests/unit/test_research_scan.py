"""The homograph scan (backlog R04): units, rhythm buckets, work and family
exclusions, eligibility counts, candidates, and the solver hand-off."""
import gzip
import json

import numpy as np
import pytest

from gtrsnipe.research import corpus as C
from gtrsnipe.research import scan as S
from gtrsnipe.research.cli import main as research_main

Q = C.TPQ
E8 = Q // 2
A = [60, 62, 64, 65, 67, 69, 71, 72]
DELTA = [0, 0, 0, -3, 0, -3, 2, -3]         # richness 3, C1 = 1/2, contour agreement 4/7


def mel(id_, pitches, corpus="mtc-fs", family="", rhythm=None, phrases=(0,)):
    ons = [0]
    for d in (rhythm or [E8] * (len(pitches) - 1)):
        ons.append(ons[-1] + d)
    return C.Melody(id_, corpus, list(pitches), ons, [E8] * len(pitches), title=id_,
                    family=family, phrases=list(phrases))


def corpus():
    return [
        mel("NLB000001_01", A, family="f1"),
        mel("NLB000002_01", [a + d for a, d in zip(A, DELTA)]),       # the homograph partner
        mel("NLB000003_01", [a + 7 for a in A]),                        # a transposition
        mel("NLB000004_01", [a + d for a, d in zip(A, range(0, 16, 2))]),  # richness 8
        mel("NLB000001_02", [a + d for a, d in zip(A, DELTA)]),       # same work as the first
        mel("NLB000005_01", [a + d for a, d in zip(A, DELTA)], family="f1"),  # same family
        mel("NLB000006_01", [60, 64] * 4),                              # mechanical figure
        mel("NLB000007_01", A, rhythm=[E8, E8, Q, E8, E8, Q, Q]),       # another rhythm
    ]


def test_rhythm_key_merges_proportional_rhythms():
    assert S.rhythm_key([0, 240, 480, 960]) == S.rhythm_key([0, 480, 960, 1920]) == (1, 1, 2)
    assert S.rhythm_key([0, 240, 720]) != S.rhythm_key([0, 480, 720])


def test_work_keys_group_voices_and_duplicates():
    m1 = C.Melody("NLB123456_01", "mtc-fs", [60], [0], [Q])
    m2 = C.Melody("NLB123456_02", "mtc-fs", [60], [0], [Q])
    l1 = C.Melody("ABBA/Waterloo", "lakh-clean", [60], [0], [Q])
    l2 = C.Melody("ABBA/Waterloo.1", "lakh-clean", [60], [0], [Q])
    assert S.work_key(m1) == S.work_key(m2) and S.work_key(l1) == S.work_key(l2)
    assert S.work_key(m1) != S.work_key(C.Melody("NLB123457_01", "mtc-fs", [60], [0], [Q]))


def test_mechanical_figures():
    assert S.mechanical([60, 64, 67, 64] * 3)          # Alberti bass
    assert S.mechanical([60, 62] * 5)                  # two pitches
    assert S.mechanical([70, 73, 77, 73, 77, 73] * 4)  # a 6-note arpeggio cell, repeated
    assert S.mechanical([65, 69, 72, 77, 81, 84, 70, 74, 77, 82, 86, 89])  # broken chords
    assert not S.mechanical(A)
    assert not S.mechanical([67, 64, 67, 72, 71, 69, 67, 64])  # a leap or two is still a tune


def test_distinct_pairs_bound_richness():
    a = np.array([[60, 62, 64, 60, 62, 64]])
    assert S.distinct_pairs(a, a + 5).tolist() == [3]
    assert S.distinct_pairs(a, np.array([[1, 2, 3, 4, 5, 6]])).tolist() == [6]


def test_scan_counts_and_finds_the_homograph():
    stats, top, _ = S.scan(corpus(), min_keep_len=8)
    st = stats[8]
    # 7 phrases share the 8-eighths rhythm; 21 pairs minus 1 same-work and 1 same-family pair
    assert st.units == 8 and st.excluded == 1 and st.pairs == 21 - 1 - 1
    assert st.transposed >= 1 and st.eligible >= 1
    assert st.richness[1] >= 1 and st.richness[8] >= 1
    best = [c for c in top if {c.a.split("@")[0], c.b.split("@")[0]}
            == {"mtc-fs:NLB000001_01", "mtc-fs:NLB000002_01"}]
    assert best and best[0].richness == 3 and best[0].c1 == pytest.approx(1 / 2)
    assert best[0].pairs == 8 and best[0].contour == pytest.approx(4 / 7, abs=1e-3)
    assert best[0].offsets in (DELTA, [-d for d in DELTA])
    # the mechanical phrase never appears in a candidate
    assert not any("NLB000006" in c.a + c.b for c in top)


def test_cross_corpus_only_pairs_units_from_different_corpora():
    mels = corpus()
    mels[1].corpus = "essen"
    _, top, _ = S.scan(mels, cross_corpus=True)
    assert top and all(c.a.split(":")[0] != c.b.split(":")[0] for c in top)


def test_windows_for_melodies_without_phrase_marks():
    m = mel("x", A + A, phrases=())
    us = S.units_of([m], "window", 5, 64, window=8, stride=4)
    assert [(u.start, u.end) for u in us] == [(0, 8), (4, 12), (8, 16)]
    assert S.units_of([m], "phrase", 5, 64) == []


def test_solve_and_render_the_best_candidate():
    mels = corpus()
    by_ref = {m.ref: m for m in mels}
    _, top, _ = S.scan(mels)
    c = next(c for c in top if c.richness == 3)
    out = S.solve(c, by_ref)
    assert out["aligned"] and out["richness"] == 3 and out["free"]
    assert out["anchored"]["tunings"][0] == ["E2", "A2", "D3", "G3", "B3", "E4"]
    text = S.render(c, by_ref)
    assert text and "e|" in text


def test_physics_sample_is_reservoir_bounded():
    _, _, samples = S.scan(corpus(), sample_per_length=2)
    assert all(len(v) <= 2 for v in samples.values()) and samples


def test_cli_scan_writes_stats_candidates_and_tabs(tmp_path, capsys):
    path = tmp_path / "t.jsonl.gz"
    head = {"format": C.CACHE_FORMAT, "version": C.CACHE_VERSION, "corpus": "t", "tpq": C.TPQ,
            "about": "", "built": "", "gtrsnipe": "", "files": 0, "melodies": 8, "errors": 0,
            "error_sample": []}
    with gzip.open(path, "wt") as f:
        f.write(json.dumps(head) + "\n")
        for m in corpus():
            f.write(m.to_json() + "\n")
    out = tmp_path / "r.json"
    tabs = tmp_path / "tabs"
    assert research_main(["scan", str(path), "--solve", "3", "--physics-sample", "2",
                          "--json", str(out), "--tabs", str(tabs)]) == 0
    text = capsys.readouterr().out
    assert "Same-rhythm pairs" in text and "Best unrelated-sounding pairs" in text
    data = json.loads(out.read_text())
    assert data["stats"]["8"]["pairs"] == 19 and data["top"]
    assert list(tabs.glob("*.tab"))
