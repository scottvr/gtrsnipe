"""Tune-family retrieval: do the offset measures find variants of the same tune?
(backlog R03; the experiment in docs/dev/coupled_transposition_structure.md s11)

Every measure sees the SAME note pairing, so they differ only in how they score
the coupling. The pairing is measure-neutral: each melody is sampled at ``grid``
points spread evenly over its own duration (the pitch sounding at each point),
so any two melodies align point for point and longer notes weigh more.

Measures (distances; all transposition-invariant except the plain Hamming floor):

  hamming       share of points whose pitches differ, no transposition (a floor)
  ti_hamming    1 - C1: points missed by the best single transposition
                (Makinen, Navarro & Ukkonen 2005) -- baseline
  switches      interval Hamming distance S -- baseline
  variation     interval L1 distance TV (SIMILE's diff) -- baseline
  log_richness  log2 of the number of distinct offsets -- candidate
  entropy       Shannon entropy of the offsets -- candidate
  vocab_90/_75  log2 of how many offsets it takes to cover 90% / 75% of the points:
                richness with stray offsets trimmed -- candidate
  miss_k        1 - C_k for k = 2, 3, 6: points the best k offsets miss -- candidate

Scores, over every melody as a query against all the others (relevant = same
tune family): mean average precision (MAP) and mean AUC, both tie-aware (richness
ties a lot), with paired bootstrap 95% intervals over queries. Then the question
the note asks: does a pair model that adds richness, entropy and reuse to the
three baselines rank better than the baselines alone? Logistic regression,
cross-validated by leaving one tune family out.
"""
from __future__ import annotations

import json
import math
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

from .corpus import Melody

MEASURES = ["hamming", "ti_hamming", "switches", "variation",
            "log_richness", "entropy", "vocab_90", "vocab_75", "miss_2", "miss_3", "miss_6"]
BASELINES = ["ti_hamming", "switches", "variation"]
CANDIDATES = ["log_richness", "entropy", "reuse"]


# -- alignment ----------------------------------------------------------------------

def grid_pitches(mel: Melody, n: int) -> np.ndarray:
    """The pitch sounding at n points spread evenly over the melody (through rests,
    the last note is held): point k sits at (k + 1/2) / n of the total duration."""
    on = np.asarray(mel.onsets, dtype=np.float64)
    end = on[-1] + mel.durations[-1]
    t = (np.arange(n) + 0.5) / n * end
    idx = np.searchsorted(on, t, side="right") - 1
    return np.asarray(mel.pitches, dtype=np.int64)[np.clip(idx, 0, len(on) - 1)]


# -- measures, one query against many ------------------------------------------------

def pair_features(G: np.ndarray, q: int) -> Dict[str, np.ndarray]:
    """Every measure (plus reuse) for melody q against each row of G (M x n)."""
    M, n = G.shape
    D = G - G[q]                                        # offsets, M x n
    S = np.sort(D, axis=1)
    new = np.ones_like(S, dtype=bool)
    new[:, 1:] = S[:, 1:] != S[:, :-1]
    r = new.sum(1)
    run = np.cumsum(new, axis=1) - 1                    # which distinct offset each point is
    counts = np.zeros((M, n), dtype=np.int64)
    np.add.at(counts, (np.repeat(np.arange(M), n), run.ravel()), 1)
    p = counts / n
    with np.errstate(divide="ignore", invalid="ignore"):
        ent = -np.where(p > 0, p * np.log2(p), 0.0).sum(1)
    cov = np.cumsum(-np.sort(-counts, axis=1), axis=1) / n     # C_1 .. C_n
    steps = np.diff(D, axis=1)
    sw = (steps != 0).sum(1)
    return {
        "hamming": (D != 0).mean(1),
        "ti_hamming": 1 - cov[:, 0],
        "switches": sw / max(1, n - 1),
        "variation": np.abs(steps).sum(1) / max(1, n - 1),
        "log_richness": np.log2(r),
        "entropy": np.maximum(ent, 0.0),
        "vocab_90": np.log2(1 + np.argmax(cov >= 0.9 - 1e-12, axis=1)),
        "vocab_75": np.log2(1 + np.argmax(cov >= 0.75 - 1e-12, axis=1)),
        "miss_2": 1 - cov[:, min(1, n - 1)],
        "miss_3": 1 - cov[:, min(2, n - 1)],
        "miss_6": 1 - cov[:, min(5, n - 1)],
        "reuse": (sw + 1 - r) / max(1, n - 1),
    }


# -- tie-aware scores -----------------------------------------------------------------

def average_precision(dist: np.ndarray, rel: np.ndarray) -> float:
    """Expected AP when tied distances are ordered at random (exact, not sampled):
    a relevant item at position k of a tie group of g items holding rg relevant,
    after b items (rb relevant), has precision (rb + 1 + k(rg-1)/(g-1)) / (b + 1 + k)."""
    R = int(rel.sum())
    if R == 0:
        return float("nan")
    order = np.argsort(dist, kind="stable")
    d, r = dist[order], rel[order].astype(np.int64)
    starts = np.flatnonzero(np.r_[True, d[1:] != d[:-1]])
    g = np.diff(np.r_[starts, len(d)])
    rg = np.add.reduceat(r, starts)
    b = starts
    rb = np.cumsum(np.r_[0, rg[:-1]])
    contrib = np.zeros(len(g))
    one = (g == 1) & (rg > 0)
    contrib[one] = (rb[one] + 1) / (b[one] + 1)
    for i in np.flatnonzero((g > 1) & (rg > 0)):
        k = np.arange(g[i])
        frac = (rg[i] - 1) / (g[i] - 1)
        contrib[i] = rg[i] * np.mean((rb[i] + 1 + k * frac) / (b[i] + 1 + k))
    return float(contrib.sum() / R)


def auc(dist: np.ndarray, rel: np.ndarray) -> float:
    """P(a relevant item is nearer than an irrelevant one), ties counted half."""
    R, N = int(rel.sum()), int((~rel).sum())
    if R == 0 or N == 0:
        return float("nan")
    _, inv, cnt = np.unique(dist, return_inverse=True, return_counts=True)
    avg_rank = (np.cumsum(cnt) - (cnt - 1) / 2)[inv]            # 1-based, ties averaged
    u = avg_rank[rel].sum() - R * (R + 1) / 2                   # relevant ranked BELOW irrelevant
    return 1 - u / (R * N)


# -- logistic pair model --------------------------------------------------------------

def fit_logistic(X: np.ndarray, y: np.ndarray, ridge: float = 1e-3, iters: int = 50
                 ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Class-balanced logistic regression by Newton's method on standardized
    features. Returns (weights incl. intercept, feature means, feature scales)."""
    mu, sd = X.mean(0), X.std(0)
    sd[sd == 0] = 1.0
    Z = np.hstack([np.ones((len(X), 1)), (X - mu) / sd])
    sw = np.where(y == 1, 0.5 / max(1, y.sum()), 0.5 / max(1, (1 - y).sum())) * len(y)
    w = np.zeros(Z.shape[1])
    for _ in range(iters):
        p = 1 / (1 + np.exp(-np.clip(Z @ w, -30, 30)))
        g = Z.T @ (sw * (p - y)) + ridge * np.r_[0, w[1:]]
        H = (Z * (sw * p * (1 - p))[:, None]).T @ Z + ridge * np.diag(np.r_[0, np.ones(len(w) - 1)])
        step = np.linalg.solve(H, g)
        w -= step
        if np.abs(step).max() < 1e-8:
            break
    return w, mu, sd


def _logit(model, X: np.ndarray) -> np.ndarray:
    w, mu, sd = model
    return w[0] + ((X - mu) / sd) @ w[1:]


# -- the experiment ---------------------------------------------------------------------

def _bootstrap_ci(values: np.ndarray, rng: np.random.Generator, B: int) -> Tuple[float, float]:
    idx = rng.integers(0, len(values), size=(B, len(values)))
    means = np.nanmean(values[idx], axis=1)
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def run(melodies: Sequence[Melody], *, grid: int = 64, bootstrap: int = 2000,
        seed: int = 20260926, max_queries: Optional[int] = None,
        models: bool = True) -> dict:
    """Score every measure at tune-family retrieval. Melodies without a family
    label are candidates (distractors) but not queries."""
    mels = [m for m in melodies if len(m)]
    fam = np.array([m.family for m in mels])
    G = np.stack([grid_pitches(m, grid) for m in mels])
    labelled = np.flatnonzero(fam != "")
    counts = {f: int((fam == f).sum()) for f in set(fam[labelled])}
    queries = np.array([q for q in labelled if counts[fam[q]] > 1])
    rng = np.random.default_rng(seed)
    if max_queries and len(queries) > max_queries:
        queries = np.sort(rng.choice(queries, max_queries, replace=False))

    ap = {m: np.full(len(queries), np.nan) for m in MEASURES}
    au = {m: np.full(len(queries), np.nan) for m in MEASURES}
    feats: Dict[int, Dict[str, np.ndarray]] = {}
    for qi, q in enumerate(queries):
        f = pair_features(G, q)
        mask = np.arange(len(mels)) != q
        rel = (fam == fam[q])[mask]
        for m in MEASURES:
            ap[m][qi] = average_precision(f[m][mask], rel)
            au[m][qi] = auc(f[m][mask], rel)
        if models:
            feats[q] = {k: f[k].astype(np.float32) for k in BASELINES + CANDIDATES}

    base_rate = np.array([(counts[fam[q]] - 1) / (len(mels) - 1) for q in queries])
    out = {"melodies": len(mels), "queries": int(len(queries)), "families": len(counts),
           "grid": grid, "bootstrap": bootstrap, "seed": seed,
           "chance_map": float(base_rate.mean()), "measures": {}}
    ref = ap["ti_hamming"]
    for m in MEASURES:
        diff = ap[m] - ref
        out["measures"][m] = {
            "map": float(np.nanmean(ap[m])), "map_ci": _bootstrap_ci(ap[m], rng, bootstrap),
            "auc": float(np.nanmean(au[m])), "auc_ci": _bootstrap_ci(au[m], rng, bootstrap),
            "map_vs_ti_hamming": float(np.nanmean(diff)),
            "map_vs_ti_hamming_ci": _bootstrap_ci(diff, rng, bootstrap)}
    if models:
        out["models"] = _pair_models(mels, fam, queries, feats, rng, bootstrap)
    return out


def _folds(families: List[str], rng: np.random.Generator, k: int = 10) -> List[List[str]]:
    """Leave one family out when there are few families, else k groups of families."""
    fams = sorted(families)
    if len(fams) <= 30:
        return [[f] for f in fams]
    order = [fams[i] for i in rng.permutation(len(fams))]
    return [order[i::k] for i in range(k)]


def _pair_models(mels, fam, queries, feats, rng, bootstrap) -> dict:
    """Logistic pair models, cross-validated by tune family (a query's family is
    never seen in training): baselines vs baselines + candidates."""
    sets = {"baselines": BASELINES, "baselines+candidates": BASELINES + CANDIDATES}
    n = len(mels)
    qset = list(queries)
    ap = {k: np.full(len(qset), np.nan) for k in sets}
    au = {k: np.full(len(qset), np.nan) for k in sets}
    coefs: Dict[str, List[List[float]]] = {k: [] for k in sets}
    pos = {q: i for i, q in enumerate(qset)}
    labelled = fam != ""
    for fold in _folds(list(set(fam[qset])), rng):
        held = set(fold)
        usable = labelled & ~np.isin(fam, list(held))
        train_q = [q for q in qset if fam[q] not in held]
        test_q = [q for q in qset if fam[q] in held]
        for name, cols in sets.items():
            X, y = [], []
            for q in train_q:
                others = np.flatnonzero(usable & (np.arange(n) > q))
                if not len(others):
                    continue
                X.append(np.column_stack([feats[q][c_][others] for c_ in cols]))
                y.append((fam[others] == fam[q]).astype(float))
            model = fit_logistic(np.vstack(X), np.concatenate(y))
            coefs[name].append([float(x) for x in model[0]])
            for q in test_q:
                mask = np.arange(n) != q
                Xq = np.column_stack([feats[q][c_][mask] for c_ in cols])
                dist = -_logit(model, Xq)
                rel = (fam == fam[q])[mask]
                qi = pos[q]
                ap[name][qi] = average_precision(dist, rel)
                au[name][qi] = auc(dist, rel)
    diff = ap["baselines+candidates"] - ap["baselines"]
    out = {}
    for name, cols in sets.items():
        W = np.array(coefs[name])
        out[name] = {"features": cols, "map": float(np.nanmean(ap[name])),
                     "map_ci": _bootstrap_ci(ap[name], rng, bootstrap),
                     "auc": float(np.nanmean(au[name])),
                     "auc_ci": _bootstrap_ci(au[name], rng, bootstrap),
                     "mean_weights": dict(zip(["intercept"] + cols, W.mean(0).round(3).tolist()))}
    out["gain_map"] = float(np.nanmean(diff))
    out["gain_map_ci"] = _bootstrap_ci(diff, rng, bootstrap)
    return out


def format_results(res: dict, title: str = "") -> str:
    lines = [f"Tune-family retrieval{': ' + title if title else ''}",
             f"  {res['melodies']} melodies, {res['queries']} queries in {res['families']} "
             f"families; grid {res['grid']} points; chance MAP {res['chance_map']:.3f}",
             "",
             "  measure        MAP    (95% CI)          AUC    (95% CI)          MAP - TI-Hamming (95% CI)"]
    for m, v in res["measures"].items():
        lines.append(f"  {m:13} {v['map']:.3f}  ({v['map_ci'][0]:.3f}-{v['map_ci'][1]:.3f})   "
                     f"{v['auc']:.3f}  ({v['auc_ci'][0]:.3f}-{v['auc_ci'][1]:.3f})   "
                     f"{v['map_vs_ti_hamming']:+.3f} ({v['map_vs_ti_hamming_ci'][0]:+.3f} to "
                     f"{v['map_vs_ti_hamming_ci'][1]:+.3f})")
    if "models" in res:
        mo = res["models"]
        lines += ["", "  Pair models (logistic, cross-validated by tune family):"]
        for name in ("baselines", "baselines+candidates"):
            v = mo[name]
            lines.append(f"  {name:21} MAP {v['map']:.3f} ({v['map_ci'][0]:.3f}-{v['map_ci'][1]:.3f})"
                         f"   AUC {v['auc']:.3f} ({v['auc_ci'][0]:.3f}-{v['auc_ci'][1]:.3f})")
            lines.append("      mean standardized weights: " + ", ".join(
                f"{k} {w:+.2f}" for k, w in v["mean_weights"].items()))
        lo, hi = mo["gain_map_ci"]
        lines.append(f"  gain from the candidates: MAP {mo['gain_map']:+.3f} (95% CI {lo:+.3f} to {hi:+.3f})")
    return "\n".join(lines)


def results_json(res: dict) -> str:
    return json.dumps(res, indent=1, default=lambda x: x.tolist() if hasattr(x, "tolist") else str(x))
