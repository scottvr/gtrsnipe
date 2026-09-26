"""Which offset-distribution "distances" satisfy the triangle inequality?

Companion to coupled_transposition_structure.md. For aligned melodies A, B, C the
pointwise offsets add: (C - A) = (B - A) + (C - B). A distance computed from the
offset distribution is a metric (modulo transposition) only if it never lets
d(A,C) exceed d(A,B) + d(B,C). Hill/Renyi orders 0 (log richness) and 1 (Shannon)
are provably fine; this script gives explicit counterexamples at other orders:

  Example 1 (16 notes): Renyi-2 (log inverse Simpson) and min-entropy (-log C1) fail.
  Example 2 (10 notes): Renyi-1/2 fails -- while Hartley holds with equality and
                        Shannon holds by just 0.002 bits (orders 0 and 1 are the edge).
  1 - C1 (transposition-invariant Hamming) holds in both, as it must.

Run:  python docs/dev/triangle_check.py
"""
from collections import Counter
from math import log2

NAMES = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]


def name(p):
    return f"{NAMES[p % 12]}{p // 12 - 1}"


def renyi(delta, q):
    """Renyi entropy (bits) of the empirical offset distribution; q=0 Hartley,
    q=1 Shannon, q=inf min-entropy."""
    n = len(delta)
    p = [c / n for c in Counter(delta).values()]
    if q == 0:
        return log2(len(p))
    if q == 1:
        return -sum(x * log2(x) for x in p)
    if q == float("inf"):
        return -log2(max(p))
    return log2(sum(x ** q for x in p)) / (1 - q)


MEASURES = {
    "log2 richness (Hartley, q=0)": lambda d: renyi(d, 0),
    "Renyi q=1/2": lambda d: renyi(d, 0.5),
    "Shannon (q=1)": lambda d: renyi(d, 1),
    "Renyi-2 (log inverse Simpson)": lambda d: renyi(d, 2),
    "min-entropy (-log2 C1)": lambda d: renyi(d, float("inf")),
    "1 - C1 (TI-Hamming)": lambda d: 1 - max(Counter(d).values()) / len(d),
}


def show(title, A, d_AB, d_BC):
    B = [a + d for a, d in zip(A, d_AB)]
    C = [b + d for b, d in zip(B, d_BC)]
    d_AC = [c - a for a, c in zip(A, C)]           # = d_AB + d_BC, pointwise
    print(f"\n=== {title} ===")
    for label, mel in (("A", A), ("B", B), ("C", C)):
        print(f"  {label}: " + " ".join(f"{name(p):>4}" for p in mel))
    for label, d in (("B - A", d_AB), ("C - B", d_BC), ("C - A", d_AC)):
        split = ":".join(str(c) for c in sorted(Counter(d).values(), reverse=True))
        print(f"  {label}: " + " ".join(f"{x:>4}" for x in d)
              + f"   ({len(set(d))} distinct; split {split})")
    print("\n| measure | d(A,B) | d(B,C) | d(A,B)+d(B,C) | d(A,C) | triangle |")
    print("|---|---|---|---|---|---|")
    for k, f in MEASURES.items():
        ab, bc, ac = f(d_AB), f(d_BC), f(d_AC)
        verdict = "holds" if ac <= ab + bc + 1e-12 else "**fails**"
        print(f"| {k} | {ab:.4f} | {bc:.4f} | {ab + bc:.4f} | {ac:.4f} | {verdict} |")


# Example 1: B - A is 0 on the first 8 notes, then eight distinct nonzero offsets
# (nine distinct offsets total). C - B is the mirror image; C - A has 16 distinct
# values. (A can be any melody: only offsets matter.)
show("Example 1: 16 notes",
     A=[60, 62, 64, 65, 67, 69, 71, 72, 72, 71, 69, 67, 65, 64, 62, 60],
     d_AB=[0] * 8 + list(range(1, 9)),
     d_BC=list(range(9, 17)) + [0] * 8)

# Example 2: two 7:3 offset splits whose minority notes mostly miss each other,
# giving a 5:2:2:1 split for C - A.
show("Example 2: 10 notes",
     A=[60, 62, 64, 65, 67, 69, 71, 72, 71, 69],
     d_AB=[0, 0, 3, 0, 3, 0, 3, 0, 0, 0],
     d_BC=[9, 0, 9, 0, 0, 9, 0, 0, 0, 0])
