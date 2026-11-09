"""Exhaustive search for the smallest triangle-inequality violation of entropy and
1 - modal share under optimized warping. Total length ordering; pitch alphabet 0..K-1;
A's first pitch fixed at 0 (both measures are transposition-invariant)."""
import sys, itertools
sys.path.insert(0, "/opt/claude/gtrsnipe/docs/research/theory")
import alignment_check as ac

K = int(sys.argv[1]) if len(sys.argv) > 1 else 4
MAXTOT = int(sys.argv[2]) if len(sys.argv) > 2 else 6

def seqs(n, first_zero=False):
    for s in itertools.product(range(K), repeat=n):
        if first_zero and s[0] != 0:
            continue
        yield list(s)

for name in ("entropy", "1 - modal share"):
    f = ac.STATS[name]
    found = None
    for tot in range(3, MAXTOT + 1):
        viol = []
        for na in range(1, tot - 1):
            for nb in range(1, tot - na):
                nc = tot - na - nb
                if nc < 1: continue
                for a in seqs(na, True):
                    for b in seqs(nb):
                        for c in seqs(nc):
                            ab, bc, acd = ac.dist(a, b, f), ac.dist(b, c, f), ac.dist(a, c, f)
                            if acd > ab + bc + 1e-9:
                                viol.append((a, b, c, ab, bc, acd))
        print(f"{name}: total length {tot}: {len(viol)} violations (alphabet {K})")
        if viol and found is None:
            found = tot
            for v in viol[:6]:
                print("   ", v)
    print()
