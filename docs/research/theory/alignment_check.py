"""Do the offset distances stay metrics when the alignment is optimized?

Companion to PROOF-alignment.md (backlog R07). An alignment of melodies A (n
notes) and B (m notes) is a warping path: pairs (i, j) from (0, 0) to (n-1, m-1),
each step (1,0), (0,1) or (1,1). For a statistic f of the offsets b_j - a_i
along the path, let d_f(A,B) = min over paths of f. This script enumerates every
path for short random melodies and counts triangle-inequality violations
d(A,C) > d(A,B) + d(B,C):

  log2 richness (distinct offsets)   -- holds: depends on the offset SET
  switch count S along the path      -- holds: repeats along a path add no switches
  total variation TV along the path  -- holds: likewise
  largest jump J along the path      -- holds: likewise
  range R = max - min offset         -- holds: 2x a transposition-invariant discrete Frechet
                                        distance (real-valued transposition; ceil(R/2) in semitones)
  Shannon entropy of the offsets     -- FAILS: path multiplicities re-weight notes
  1 - modal share (TI-Hamming)        -- FAILS: likewise
(the stutter-invariance principle and its proof: PROOF-alignment.md)

It also prints the smallest violation found for each, as a certificate.

Run:  python docs/research/theory/alignment_check.py [trials]
"""
import math
import random
import sys
from collections import Counter
from functools import lru_cache


@lru_cache(maxsize=None)
def paths(n, m):
    """Every warping path from (0,0) to (n-1,m-1), as tuples of pairs."""
    if n == 1 and m == 1:
        return [((0, 0),)]
    out = []
    for di, dj in ((1, 0), (0, 1), (1, 1)):
        pn, pm = n - di, m - dj
        if pn >= 1 and pm >= 1:
            out += [p + ((n - 1, m - 1),) for p in paths(pn, pm)]
    return out


def richness(offs):
    return math.log2(len(set(offs)))


def entropy(offs):
    n = len(offs)
    return max(0.0, -sum(c / n * math.log2(c / n) for c in Counter(offs).values()))


def ti_hamming(offs):
    return 1 - max(Counter(offs).values()) / len(offs)


def switches(offs):
    return sum(1 for x, y in zip(offs, offs[1:]) if x != y)


def variation(offs):
    return sum(abs(y - x) for x, y in zip(offs, offs[1:]))


def jump(offs):
    return max((abs(y - x) for x, y in zip(offs, offs[1:])), default=0)


def spread(offs):
    return max(offs) - min(offs)


STATS = {"log2 richness": richness, "switch count": switches, "total variation": variation,
         "largest jump": jump, "range": spread,
         "entropy": entropy, "1 - modal share": ti_hamming}


def dist(a, b, f):
    return min(f([b[j] - a[i] for i, j in p]) for p in paths(len(a), len(b)))


def main(trials=3000, seed=1):
    rng = random.Random(seed)
    worst = {k: None for k in STATS}
    fails = Counter()
    for _ in range(trials):
        a, b, c = ([rng.choice([0, 2, 4, 5, 7]) for _ in range(rng.randint(1, 5))]
                   for _ in range(3))
        for k, f in STATS.items():
            ab, bc, ac = dist(a, b, f), dist(b, c, f), dist(a, c, f)
            gap = ac - (ab + bc)
            if gap > 1e-9:
                fails[k] += 1
                size = len(a) + len(b) + len(c)
                if worst[k] is None or size < worst[k][0]:
                    worst[k] = (size, a, b, c, ab, bc, ac)
    print(f"{trials} random triples of 1-5 note melodies, every warping path enumerated\n")
    for k in STATS:
        print(f"{k:16} violations: {fails[k]}")
        if worst[k]:
            _, a, b, c, ab, bc, ac = worst[k]
            print(f"    e.g. A={a} B={b} C={c}: d(A,B)={ab:.3f} + d(B,C)={bc:.3f} "
                  f"< d(A,C)={ac:.3f}")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 3000)
