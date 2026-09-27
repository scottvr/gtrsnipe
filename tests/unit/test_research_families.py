"""Tune-family retrieval (backlog R03): alignment, the vectorized measures, the
tie-aware scores and the experiment driver, on synthetic families."""
import gzip
import itertools
import json

import numpy as np
import pytest

from gtrsnipe.research import corpus as C
from gtrsnipe.research.cli import main as research_main
from gtrsnipe.research.families import (MEASURES, auc, average_precision, grid_pitches,
                                        pair_features, run)
from gtrsnipe.research.offsets import profile_of_deltas

Q = C.TPQ


def mel(pitches, durs=None, family="", id_=None):
    durs = durs or [Q] * len(pitches)
    ons = list(itertools.accumulate([0] + durs[:-1]))
    return C.Melody(id_ or f"m{id(pitches)}", "t", list(pitches), ons, list(durs), family=family)


def test_grid_samples_the_sounding_pitch_weighted_by_duration():
    m = mel([60, 62], [Q, 3 * Q])
    assert grid_pitches(m, 4).tolist() == [60, 62, 62, 62]
    assert grid_pitches(m, 8).tolist() == [60, 60] + [62] * 6


def test_vectorized_measures_match_the_offset_profile():
    rng = np.random.default_rng(3)
    G = rng.integers(55, 72, size=(6, 16))
    f = pair_features(G, 2)
    for i in range(6):
        p = profile_of_deltas((G[i] - G[2]).tolist())
        assert f["log_richness"][i] == pytest.approx(p.log_richness)
        assert f["entropy"][i] == pytest.approx(p.entropy)
        assert f["ti_hamming"][i] == pytest.approx(p.ti_hamming)
        assert f["miss_3"][i] == pytest.approx(1 - p.coverage[2])
        k90 = next(k for k in range(1, 17) if sum(sorted(np.unique(G[i] - G[2], return_counts=True)[1],
                                                           reverse=True)[:k]) >= 0.9 * 16)
        assert f["vocab_90"][i] == pytest.approx(np.log2(k90))
        assert f["switches"][i] == pytest.approx(p.switches / 15)
        assert f["variation"][i] == pytest.approx(p.total_variation / 15)
        assert f["reuse"][i] == pytest.approx(p.reuse / 15)


def _brute_ap(d, rel):
    groups = [[i for i in range(len(d)) if d[i] == v] for v in sorted(set(d))]
    aps = []
    for perms in itertools.product(*[itertools.permutations(g) for g in groups]):
        hits, s = 0, 0.0
        for k, i in enumerate([i for p in perms for i in p], 1):
            if rel[i]:
                hits += 1
                s += hits / k
        aps.append(s / rel.sum())
    return np.mean(aps)


def test_average_precision_and_auc_handle_ties_exactly():
    rng = np.random.default_rng(0)
    for _ in range(60):
        n = int(rng.integers(3, 7))
        d = rng.integers(0, 3, n).astype(float)
        rel = rng.random(n) < 0.4
        if not 0 < rel.sum() < n:
            continue
        assert average_precision(d, rel) == pytest.approx(_brute_ap(d, rel))
        pos, neg = d[rel], d[~rel]
        want = np.mean([1 if a < b else 0.5 if a == b else 0 for a in pos for b in neg])
        assert auc(d, rel) == pytest.approx(want)


def _families():
    """Two tune families of transposed variants (one note altered here and there),
    plus unlabelled distractors."""
    rng = np.random.default_rng(1)
    motifs = {"F1": [60, 62, 64, 65, 67, 65, 64, 62, 60, 67, 64, 60],
              "F2": [67, 67, 69, 67, 72, 71, 67, 67, 69, 67, 74, 72]}
    out = []
    for fam, mot in motifs.items():
        for v in range(5):
            shift = int(rng.integers(-5, 6))
            var = [x + shift for x in mot]
            var[int(rng.integers(0, len(var)))] += 2
            out.append(mel(var, family=fam, id_=f"{fam}.{v}"))
    for k in range(6):
        out.append(mel(rng.integers(55, 75, 12).tolist(), id_=f"x{k}"))
    return out


def test_run_scores_every_measure_and_the_pair_models():
    res = run(_families(), grid=24, bootstrap=200)
    assert res["queries"] == 10 and res["families"] == 2 and res["melodies"] == 16
    assert set(res["measures"]) == set(MEASURES)
    assert res["measures"]["ti_hamming"]["map"] > 0.9        # transposed variants
    assert res["measures"]["hamming"]["map"] < res["measures"]["ti_hamming"]["map"]
    lo, hi = res["measures"]["ti_hamming"]["map_ci"]
    assert lo <= res["measures"]["ti_hamming"]["map"] <= hi
    assert {"baselines", "baselines+candidates", "gain_map"} <= set(res["models"])


def test_cli_families(tmp_path, capsys):
    path = tmp_path / "fam.jsonl.gz"
    head = {"format": C.CACHE_FORMAT, "version": C.CACHE_VERSION, "corpus": "fam",
            "tpq": C.TPQ, "about": "", "built": "", "gtrsnipe": "", "files": 0,
            "melodies": 16, "errors": 0, "error_sample": []}
    with gzip.open(path, "wt") as f:
        f.write(json.dumps(head) + "\n")
        for m in _families():
            f.write(m.to_json() + "\n")
    out_json = tmp_path / "r.json"
    assert research_main(["families", str(path), "--grid", "24", "--bootstrap", "100",
                          "--json", str(out_json)]) == 0
    assert "ti_hamming" in capsys.readouterr().out
    assert json.loads(out_json.read_text())["queries"] == 10
