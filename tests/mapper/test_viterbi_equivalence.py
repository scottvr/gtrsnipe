"""The DP's hoisted first-order step and bucketed second-order step must give exactly the
path (and path score) of the plain triple loop they replace. The plain loop is kept here as
the oracle; the inputs are seeded random chordal passages, where candidate counts per stage
reach the dozens and the t-2 span term fires."""
import copy
import random

import pytest

from gtrsnipe.core.config import MapperConfig
from gtrsnipe.core.types import MusicalEvent
from gtrsnipe.guitar.mapper import GuitarMapper


def _plain_viterbi(mapper, time_groups):
    """The pre-2026-11-07 stage loop, verbatim in spirit: for k, for j, for i."""
    NONE = -1
    kept, cand = [], []
    for g in time_groups:
        g2 = mapper._preprocess_group(g)
        cs = mapper.generate_candidates(g2)
        if cs:
            kept.append(g2); cand.append(cs)
    T = len(cand)
    second_order = bool(mapper.config.diagonal_span_penalty and mapper.config.let_ring_bonus > 0)
    sc = mapper._score_fingering
    gaps = [None] + [mapper._gap_seconds(kept[t - 1], kept[t]) for t in range(1, T)]
    BP = [dict() for _ in range(T)]
    V = {(NONE, j): sc(fj, None, None) for j, fj in enumerate(cand[0])}
    for st in V: BP[0][st] = None
    if T > 1:
        Vn = {}
        for j, fj in enumerate(cand[1]):
            for i, fi in enumerate(cand[0]):
                s = V[(NONE, i)] + sc(fj, fi, None, gaps[1])
                if (i, j) not in Vn or s > Vn[(i, j)]:
                    Vn[(i, j)] = s; BP[1][(i, j)] = (NONE, i)
        V = Vn
    for t in range(2, T):
        Vn = {}
        for k, fk in enumerate(cand[t]):
            for j, fj in enumerate(cand[t - 1]):
                best_s = best_prev = None
                if second_order:
                    for i, fi in enumerate(cand[t - 2]):
                        if (i, j) not in V: continue
                        s = V[(i, j)] + sc(fk, fj, fi, gaps[t])
                        if best_s is None or s > best_s: best_s, best_prev = s, (i, j)
                else:
                    for i, _fi in enumerate(cand[t - 2]):
                        if (i, j) not in V: continue
                        if best_s is None or V[(i, j)] > best_s: best_s, best_prev = V[(i, j)], (i, j)
                    if best_prev is not None: best_s += sc(fk, fj, None, gaps[t])
                if best_prev is None: continue
                Vn[(j, k)] = best_s; BP[t][(j, k)] = best_prev
        V = Vn
    end_state = max(sorted(V, key=lambda s: (s[0], s[1])), key=lambda s: V[s])
    chosen = [0] * T; st = end_state
    for t in range(T - 1, -1, -1):
        chosen[t] = st[1]; st = BP[t][st]
    return [cand[t][chosen[t]] for t in range(T)], V[end_state]


def _passage(seed, stages=24):
    """Seeded chordal passage: 1 to 4 notes per beat in a guitar-friendly range."""
    rng = random.Random(seed)
    groups = []
    for t in range(stages):
        n = rng.choice([1, 1, 2, 3, 4])
        root = rng.randrange(45, 70)
        pitches = sorted({root + rng.choice([0, 3, 4, 5, 7, 9, 12]) for _ in range(n)})
        groups.append([MusicalEvent(time=float(t), pitch=p, duration=1.0, velocity=90) for p in pitches])
    return groups


CONFIGS = {
    "first-order defaults": {},
    "first-order wiki-ish": dict(string_switch_penalty=0.0, prefer_open=True, sweet_spot_high=4),
    "second-order": dict(let_ring_bonus=210.0, diagonal_span_penalty=True),
    "second-order, tight span": dict(let_ring_bonus=5.0, diagonal_span_penalty=True, unplayable_fret_span=3,
                                     movement_penalty=20.0, string_switch_penalty=0.0),
    "second-order, timed": dict(let_ring_bonus=210.0, diagonal_span_penalty=True, movement_time_base="onset"),
}


@pytest.mark.parametrize("name", list(CONFIGS))
@pytest.mark.parametrize("seed", [1, 2, 3, 4, 5])
def test_dp_matches_plain_triple_loop(name, seed):
    cfg = MapperConfig(**CONFIGS[name])
    groups = _passage(seed)
    oracle_path, oracle_score = _plain_viterbi(GuitarMapper(cfg), copy.deepcopy(groups))
    mapper = GuitarMapper(cfg)
    out = mapper.map_multi_string(copy.deepcopy(groups))
    assert mapper.last_path_score == pytest.approx(oracle_score, abs=1e-9)
    # compare fingerings stage by stage through the written-back events
    written = sorted(out, key=lambda e: (e.time, e.pitch))
    expect = []
    for g, f in zip(groups, oracle_path):
        expect += [(p.string, p.fret) for p in f]
    assert [(e.string, e.fret) for e in written] == expect


def test_second_order_passages_exercise_the_t2_term():
    """Sanity: on at least one seeded passage the t-2 span term changes the answer, so the
    equivalence above is not vacuous."""
    changed = 0
    for seed in range(1, 6):
        groups = _passage(seed)
        a = GuitarMapper(MapperConfig(let_ring_bonus=210.0, diagonal_span_penalty=True))
        b = GuitarMapper(MapperConfig(let_ring_bonus=210.0, diagonal_span_penalty=False))
        pa = [(e.string, e.fret) for e in sorted(a.map_multi_string(copy.deepcopy(groups)), key=lambda e: (e.time, e.pitch))]
        pb = [(e.string, e.fret) for e in sorted(b.map_multi_string(copy.deepcopy(groups)), key=lambda e: (e.time, e.pitch))]
        changed += pa != pb
    assert changed >= 1
