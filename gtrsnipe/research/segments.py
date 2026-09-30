"""Phrase- and motif-level retrieval on MTC-ANN (the R03 follow-ups).

R03 tested whole melodies against their tune families and found the offset profile
no better than transposition-invariant Hamming distance. It left open: phrase-level
retrieval, an alignment-based baseline, the offset measures under their own optimal
warping (R12), and whether low richness with high reuse marks related segments (the
structure note's section 6 hypothesis). MTC-ANN's expert annotations make all of
these testable:

* **phrases**: every phrase carries a label from each of three annotators; within a
  tune family, phrases an annotator gave the same letter are the same phrase (the
  ground truth behind Janssen, van Kranenburg & Volk 2017; the letters are each
  annotator's own, so each annotator is scored separately);
* **motifs**: 1,657 annotated motif occurrences, each with a motif class.

A query is a segment; its candidates are the segments of the *other* songs of its
tune family (``scope="family"``) or of its own song (``scope="song"``); relevant
candidates carry its label. Measures: the R03 grid measures on a time-normalized
grid; dynamic time warping on intervals (an alignment-based baseline); and the
offset measures minimized over warping paths: switches, total variation, largest
jump, range, and richness (exact up to 6, the guitar range).
"""
import csv
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

from .corpus import Melody
from .families import (_bootstrap_ci, _folds, _logit, auc, average_precision, fit_logistic,
                       pair_features)

GRID_MEASURES = ["ti_hamming", "switches", "variation", "log_richness", "entropy", "reuse"]
WARP_MEASURES = ["warp_switches", "warp_variation", "warp_jump", "warp_range", "warp_richness"]
MEASURES = GRID_MEASURES + ["dtw_intervals", "dtw_pitch"] + WARP_MEASURES
BASELINES = ["ti_hamming", "switches", "variation", "dtw_intervals", "dtw_pitch"]
GRID_CANDIDATES = ["log_richness", "entropy", "reuse"]            # the section-6 hypothesis
WARP_CANDIDATES = ["warp_switches", "warp_variation", "warp_richness"]   # R12
RICHNESS_CAP = 6        # warped richness is exact up to this; larger counts as CAP + 1


@dataclass
class Segment:
    family: str
    song: str
    index: int                                   # phrase number, or motif id
    pitches: Tuple[int, ...]
    onsets: Tuple[int, ...]                      # ticks from the segment's first note
    end: int                                     # tick where the last note ends
    labels: Dict[str, str] = field(default_factory=dict)


def _segment(m: Melody, start: int, end: int, index, labels) -> Segment:
    t0 = m.onsets[start]
    return Segment(m.family, m.id, index, tuple(m.pitches[start:end]),
                   tuple(t - t0 for t in m.onsets[start:end]),
                   m.onsets[end - 1] + m.durations[end - 1] - t0, labels)


def load_phrases(melodies: Sequence[Melody], metadata_dir: str) -> List[Segment]:
    """Every annotated phrase, labelled by annotator (ann1, ann2, ann3)."""
    rows: Dict[str, List[List[str]]] = {}
    for row in csv.reader(open(f"{metadata_dir}/MTC-ANN-phrase-similarity.csv")):
        rows.setdefault(row[0], []).append(row)
    out = []
    for m in melodies:
        spans, ann = m.phrase_spans(), rows.get(m.id, [])
        if len(ann) != len(spans):
            continue                              # (all 360 match in MTC-ANN 2.0.1)
        for (s, e), row in zip(spans, sorted(ann, key=lambda r: int(r[1]))):
            out.append(_segment(m, s, e, int(row[1]),
                                {"ann1": row[2], "ann2": row[3], "ann3": row[4]}))
    return out


def load_motifs(melodies: Sequence[Melody], metadata_dir: str) -> List[Segment]:
    """Every annotated motif occurrence, labelled by its motif class."""
    names = [f.strip('"') for f in
             open(f"{metadata_dir}/MTC-ANN-motifs-fieldnames.csv").read().strip().split(",")]
    by = {m.id: m for m in melodies}
    out = []
    for r in csv.DictReader(open(f"{metadata_dir}/MTC-ANN-motifs.csv"), fieldnames=names):
        m = by.get(r["songid"])
        if m is None:
            continue
        s, e = int(r["startindex"]), int(r["endindex"]) + 1
        if not 0 <= s < e <= len(m):
            continue
        out.append(_segment(m, s, e, r["motifid"], {"motif": r["motifclass"]}))
    return out


# -- measures --------------------------------------------------------------------------

def grid_pitches(seg: Segment, n: int) -> np.ndarray:
    """The pitch sounding at n evenly spread points of the segment (as in R03)."""
    on = np.asarray(seg.onsets, dtype=np.float64)
    t = (np.arange(n) + 0.5) / n * max(seg.end, 1)
    idx = np.searchsorted(on, t, side="right") - 1
    return np.asarray(seg.pitches, dtype=np.int64)[np.clip(idx, 0, len(on) - 1)]


def dtw_intervals(a: Sequence[int], b: Sequence[int]) -> float:
    """Dynamic time warping on the interval sequences (transposition-invariant),
    |interval difference| per matched pair, normalized by the two lengths."""
    ia, ib = np.diff(a), np.diff(b)
    if not len(ia) or not len(ib):
        return float(abs(len(ia) - len(ib)))
    n, m = len(ia), len(ib)
    C = np.abs(ia[:, None] - ib[None, :]).astype(np.float64)
    D = np.full((n + 1, m + 1), np.inf)
    D[0, 0] = 0.0
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            D[i, j] = C[i - 1, j - 1] + min(D[i - 1, j], D[i, j - 1], D[i - 1, j - 1])
    return float(D[n, m] / (n + m))


def dtw_pitch(a: Sequence[int], b: Sequence[int], shift: int) -> float:
    """Dynamic time warping on pitch after transposing b by ``shift`` (the grid's modal
    offset, TI-Hamming's own transposition): a warped, transposition-invariant pitch
    baseline, so a gain from the warped offset measures isn't just from warping."""
    A = np.asarray(a, dtype=np.int64)
    B = np.asarray(b, dtype=np.int64) - shift
    n, m = len(A), len(B)
    C = np.abs(A[:, None] - B[None, :]).astype(np.float64)
    D = np.full((n + 1, m + 1), np.inf)
    D[0, 0] = 0.0
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            D[i, j] = C[i - 1, j - 1] + min(D[i - 1, j], D[i, j - 1], D[i - 1, j - 1])
    return float(D[n, m] / (n + m))


def _paths(n: int, m: int):
    """Cells in an order where each cell's predecessors come first."""
    for i in range(n):
        for j in range(m):
            yield i, j, [(i - 1, j), (i, j - 1), (i - 1, j - 1)]


def warp_measures(a: Sequence[int], b: Sequence[int]) -> Dict[str, float]:
    """The offset measures minimized over warping paths (R07's pseudometrics):
    switches, total variation, largest jump, range, and richness (log2; exact up
    to RICHNESS_CAP distinct offsets, larger counted as CAP + 1)."""
    A, B = np.asarray(a, dtype=np.int64), np.asarray(b, dtype=np.int64)
    n, m = len(A), len(B)
    D = B[None, :] - A[:, None]                        # the offset of each cell
    INF = float("inf")
    sw = np.full((n, m), INF)
    tv = np.full((n, m), INF)
    jp = np.full((n, m), INF)
    sw[0, 0] = tv[0, 0] = jp[0, 0] = 0.0
    for i, j, preds in _paths(n, m):
        if i == 0 and j == 0:
            continue
        d = D[i, j]
        best_s = best_t = best_j = INF
        for pi, pj in preds:
            if pi < 0 or pj < 0:
                continue
            step = abs(int(d - D[pi, pj]))
            best_s = min(best_s, sw[pi, pj] + (step != 0))
            best_t = min(best_t, tv[pi, pj] + step)
            best_j = min(best_j, max(jp[pi, pj], step))
        sw[i, j], tv[i, j], jp[i, j] = best_s, best_t, best_j
    # range: for each lower bound lo, the smallest max offset over paths that stay >= lo
    rng_best = INF
    for lo in np.unique(D):
        if D[0, 0] < lo or D[n - 1, m - 1] < lo:
            continue
        hi = np.full((n, m), INF)
        hi[0, 0] = D[0, 0]
        for i, j, preds in _paths(n, m):
            if (i, j) == (0, 0) or D[i, j] < lo:
                continue
            p = min((hi[pi, pj] for pi, pj in preds if pi >= 0 and pj >= 0), default=INF)
            hi[i, j] = max(p, D[i, j])
        if hi[n - 1, m - 1] < INF:
            rng_best = min(rng_best, hi[n - 1, m - 1] - lo)
    return {"warp_switches": sw[-1, -1] / max(1, n + m - 2),
            "warp_variation": tv[-1, -1] / max(1, n + m - 2),
            "warp_jump": float(jp[-1, -1]),
            "warp_range": float(rng_best),
            "warp_richness": math.log2(warped_richness(D))}


def warped_richness(D: np.ndarray, cap: int = RICHNESS_CAP) -> int:
    """The fewest distinct offsets on any warping path through the offset grid D
    (a minimum-label path). Exact up to ``cap``: each cell keeps the minimal
    (by inclusion) offset sets of the paths reaching it, and sets larger than
    ``cap`` are dropped; if none survive, returns cap + 1."""
    n, m = D.shape
    vals = {v: k for k, v in enumerate(np.unique(D).tolist())}
    L = [[1 << vals[int(D[i, j])] for j in range(m)] for i in range(n)]
    sets: List[List[Optional[List[int]]]] = [[None] * m for _ in range(n)]
    sets[0][0] = [L[0][0]]
    for i, j, preds in _paths(n, m):
        if i == 0 and j == 0:
            continue
        cand = set()
        for pi, pj in preds:
            if pi >= 0 and pj >= 0 and sets[pi][pj]:
                for s in sets[pi][pj]:
                    t = s | L[i][j]
                    if bin(t).count("1") <= cap:
                        cand.add(t)
        # keep the minimal sets only (a superset of another is never better)
        ordered = sorted(cand, key=lambda s: bin(s).count("1"))
        keep: List[int] = []
        for s in ordered:
            if not any(k & ~s == 0 for k in keep):
                keep.append(s)
        sets[i][j] = keep
    final = sets[n - 1][m - 1]
    return min((bin(s).count("1") for s in final), default=cap + 1) if final else cap + 1


# -- the experiment -----------------------------------------------------------------------

def _pairs_features(segs: List[Segment], q: int, cand: np.ndarray, G: np.ndarray
                    ) -> Dict[str, np.ndarray]:
    grid = pair_features(G[np.r_[q, cand]], 0)
    f = {k: grid[k][1:] for k in GRID_MEASURES}
    a = segs[q].pitches
    f["dtw_intervals"] = np.array([dtw_intervals(a, segs[c].pitches) for c in cand])
    offsets = G[cand] - G[q]                             # grid offsets, one row per candidate
    modal = [int(np.bincount(row - row.min()).argmax() + row.min()) for row in offsets]
    f["dtw_pitch"] = np.array([dtw_pitch(a, segs[c].pitches, sh) for c, sh in zip(cand, modal)])
    warp = [warp_measures(a, segs[c].pitches) for c in cand]
    for k in WARP_MEASURES:
        f[k] = np.array([w[k] for w in warp])
    return f


_SHARED: dict = {}


def _init_worker(segs, G):
    _SHARED["segs"], _SHARED["G"] = segs, G


def _query_job(args):
    q, cand = args
    return q, cand, _pairs_features(_SHARED["segs"], q, cand, _SHARED["G"])


def features(segs: List[Segment], *, scope: str = "family", grid: int = 16,
             workers: int = 4) -> Dict[int, Tuple[np.ndarray, Dict[str, np.ndarray]]]:
    """Every measure for every query and its candidates. Labels don't enter, so this
    is computed once and shared by all label sources (annotators)."""
    G = np.stack([grid_pitches(s, grid) for s in segs])
    fam = np.array([s.family for s in segs])
    song = np.array([s.song for s in segs])
    jobs = []
    for q in range(len(segs)):
        if scope == "family":
            cand = np.flatnonzero((fam == fam[q]) & (song != song[q]))
        else:
            cand = np.flatnonzero((song == song[q]) & (np.arange(len(segs)) != q))
        if len(cand):
            jobs.append((q, cand))
    if workers > 1:
        from multiprocessing import Pool          # the data goes to each worker once
        with Pool(workers, initializer=_init_worker, initargs=(segs, G)) as pool:
            done = pool.map(_query_job, jobs, chunksize=8)
    else:
        _init_worker(segs, G)
        done = [_query_job(j) for j in jobs]
    return {q: (cand, f) for q, cand, f in done}


def run(segs: List[Segment], label_key: str, feats_all=None, *, scope: str = "family",
        grid: int = 16, bootstrap: int = 2000, seed: int = 20260930, models: bool = True,
        workers: int = 4) -> dict:
    """Retrieval of same-label segments, for one label source (e.g. 'ann1', 'motif')."""
    if feats_all is None:
        feats_all = features(segs, scope=scope, grid=grid, workers=workers)
    fam = np.array([s.family for s in segs])
    lab = np.array([s.labels.get(label_key, "") for s in segs])
    rng = np.random.default_rng(seed)
    ap = {k: [] for k in MEASURES}
    au = {k: [] for k in MEASURES}
    queries, feats, rels = [], {}, {}
    # the section-6 signature, split by reuse: few distinct offsets (grid r <= 2) and
    # revisited (u >= 1) vs not; counts among related and unrelated candidate pairs
    sig = {"r<=2,u>=1": [0, 0], "r<=2,u=0": [0, 0], "total": [0, 0]}
    for q, (cand, f) in sorted(feats_all.items()):
        if not lab[q]:
            continue
        rel = lab[cand] == lab[q]
        if rel.all() or not rel.any():
            continue
        for k in MEASURES:
            ap[k].append(average_precision(f[k], rel))
            au[k].append(auc(f[k], rel))
        queries.append(q)
        feats[q], rels[q] = f, rel
        r = np.round(2 ** f["log_richness"]).astype(int)
        low = r <= 2
        for key, mask in (("r<=2,u>=1", low & (f["reuse"] > 0)), ("r<=2,u=0", low & (f["reuse"] == 0))):
            sig[key][0] += int((mask & rel).sum())
            sig[key][1] += int((mask & ~rel).sum())
        sig["total"][0] += int(rel.sum())
        sig["total"][1] += int((~rel).sum())
    out = {"segments": len(segs), "label": label_key, "scope": scope, "grid": grid,
           "queries": len(queries), "seed": seed, "bootstrap": bootstrap,
           "chance_map": float(np.mean([rels[q].mean() for q in queries])) if queries else float("nan"),
           "measures": {}, "signature": sig}
    ref = np.array(ap["ti_hamming"])
    for k in MEASURES:
        a_, u_ = np.array(ap[k]), np.array(au[k])
        out["measures"][k] = {"map": float(np.nanmean(a_)), "map_ci": _bootstrap_ci(a_, rng, bootstrap),
                              "auc": float(np.nanmean(u_)), "auc_ci": _bootstrap_ci(u_, rng, bootstrap),
                              "map_vs_ti_hamming": float(np.nanmean(a_ - ref)),
                              "map_vs_ti_hamming_ci": _bootstrap_ci(a_ - ref, rng, bootstrap)}
    if models and queries:
        out["models"] = {name: _models(segs, fam, queries, feats, rels, rng, bootstrap, extra)
                         for name, extra in (("grid candidates (section 6)", GRID_CANDIDATES),
                                             ("warped candidates (R12)", WARP_CANDIDATES))}
    return out


def _models(segs, fam, queries, feats, rels, rng, bootstrap, extra) -> dict:
    """Baselines vs baselines + ``extra``: logistic pair models, cross-validated by
    tune family (a query's family is never in training)."""
    sets = {"baselines": BASELINES, "with candidates": BASELINES + extra}
    ap = {k: np.full(len(queries), np.nan) for k in sets}
    pos = {q: i for i, q in enumerate(queries)}
    for fold in _folds(sorted(set(fam[queries])), rng):
        held = set(fold)
        train = [q for q in queries if fam[q] not in held]
        test = [q for q in queries if fam[q] in held]
        if not train or not test:
            continue
        for name, cols in sets.items():
            X = np.vstack([np.column_stack([feats[q][c] for c in cols]) for q in train])
            y = np.concatenate([rels[q].astype(float) for q in train])
            model = fit_logistic(X, y)
            for q in test:
                Xq = np.column_stack([feats[q][c] for c in cols])
                ap[name][pos[q]] = average_precision(-_logit(model, Xq), rels[q])
    diff = ap["with candidates"] - ap["baselines"]
    return {"candidates": extra, "baselines_map": float(np.nanmean(ap["baselines"])),
            "with_candidates_map": float(np.nanmean(ap["with candidates"])),
            "gain_map": float(np.nanmean(diff)), "gain_map_ci": _bootstrap_ci(diff, rng, bootstrap)}


def format_results(res: dict, title: str = "") -> str:
    lines = [title or f"{res['label']} ({res['scope']} scope)",
             f"  {res['segments']} segments, {res['queries']} queries, grid {res['grid']}, "
             f"chance MAP {res['chance_map']:.3f}",
             "  measure            MAP (95% CI)            AUC    MAP - TI-Hamming (95% CI)"]
    for k, v in sorted(res["measures"].items(), key=lambda kv: -kv[1]["map"]):
        lo, hi = v["map_ci"]
        dlo, dhi = v["map_vs_ti_hamming_ci"]
        lines.append(f"  {k:<16} {v['map']:.3f} ({lo:.3f}-{hi:.3f})   {v['auc']:.3f}  "
                     f"{v['map_vs_ti_hamming']:+.3f} ({dlo:+.3f} to {dhi:+.3f})")
    sig = res["signature"]
    tr, ti = sig["total"]
    for key in ("r<=2,u>=1", "r<=2,u=0"):
        sr, si = sig[key]
        lines.append(f"  pairs with {key:<9}: {100 * sr / max(1, tr):5.1f}% of related, "
                     f"{100 * si / max(1, ti):5.2f}% of unrelated ({sr} / {si})")
    for name, mres in res.get("models", {}).items():
        lo, hi = mres["gain_map_ci"]
        lines.append(f"  {name}: baselines {mres['baselines_map']:.3f} -> "
                     f"{mres['with_candidates_map']:.3f}, gain {mres['gain_map']:+.3f} "
                     f"({lo:+.3f} to {hi:+.3f})")
    return "\n".join(lines)
