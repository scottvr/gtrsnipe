"""The R03 follow-ups: phrase/motif retrieval measures (research/segments.py)."""
import random

import numpy as np
import pytest

from gtrsnipe.research.segments import (Segment, dtw_intervals, features, run, warp_measures,
                                        warped_richness)


def _paths(n, m):
    def rec(i, j, acc):
        if (i, j) == (n - 1, m - 1):
            yield acc
            return
        for di, dj in ((1, 0), (0, 1), (1, 1)):
            if i + di < n and j + dj < m:
                yield from rec(i + di, j + dj, acc + [(i + di, j + dj)])
    yield from rec(0, 0, [(0, 0)])


def test_warped_measures_match_brute_force():
    rnd = random.Random(3)
    for _ in range(80):
        n, m = rnd.randint(1, 5), rnd.randint(1, 5)
        a = [rnd.randint(55, 67) for _ in range(n)]
        b = [rnd.randint(55, 67) for _ in range(m)]
        D = np.subtract.outer(np.array(b), np.array(a)).T
        best = dict(r=99, s=99, tv=99, j=99, R=99)
        for p in _paths(n, m):
            d = [int(D[i, j]) for i, j in p]
            steps = [abs(x - y) for x, y in zip(d, d[1:])]
            best = dict(r=min(best["r"], len(set(d))), s=min(best["s"], sum(x != 0 for x in steps)),
                        tv=min(best["tv"], sum(steps)), j=min(best["j"], max(steps, default=0)),
                        R=min(best["R"], max(d) - min(d)))
        w, norm = warp_measures(a, b), max(1, n + m - 2)
        assert warped_richness(D) == min(best["r"], 7)
        assert round(w["warp_switches"] * norm) == best["s"]
        assert round(w["warp_variation"] * norm) == best["tv"]
        assert w["warp_jump"] == best["j"] and w["warp_range"] == best["R"]


def test_transposition_and_stretching_cost_nothing():
    a = [60, 62, 64, 65, 67]
    b = [x + 7 for x in (60, 62, 62, 64, 65, 67)]             # transposed, one note repeated
    w = warp_measures(a, b)
    assert w["warp_switches"] == 0 and w["warp_range"] == 0 and w["warp_richness"] == 0
    assert dtw_intervals(a, [x + 5 for x in a]) == 0


def seg(fam, song, i, pitches, label):
    return Segment(fam, song, i, tuple(pitches), tuple(range(0, 480 * len(pitches), 480)),
                   480 * len(pitches), {"x": label})


def test_run_finds_same_labelled_phrases():
    motif = [60, 62, 64, 62, 60]
    other = [67, 65, 64, 62, 59]
    segs = [seg("F", "s1", 0, motif, "a"), seg("F", "s1", 1, other, "b"),
            seg("F", "s2", 0, [p + 3 for p in motif], "a"), seg("F", "s2", 1, other, "b"),
            seg("F", "s3", 0, [p - 2 for p in motif], "a"), seg("F", "s3", 1, other, "b")]
    feats = features(segs, scope="family", grid=8, workers=1)
    res = run(segs, "x", feats, grid=8, bootstrap=50, models=False)
    assert res["queries"] == 6
    assert res["measures"]["ti_hamming"]["map"] == pytest.approx(1.0)
    assert res["measures"]["warp_richness"]["map"] == pytest.approx(1.0)
