"""R04 "Playability" (F06): how many sampled folk pairs have a shared tab within a
comfort limit?

Draws 50 of the solved folk candidates that `gtrsnipe-research scan --json` saved
(all lengths pooled, `random.seed(3)`), and solves each in anchored mode (song A an
ordinary STANDARD tab) with `max_discomfort` = none, 50, 20 and 5 mapper points per
note. Prints the count found at each limit, with the median discomfort and median
highest fret of the tabs found.

Run:  python docs/research/results/r04_playability.py r04-folk.json CACHE_DIR [--n 50] [--seed 3]
      (CACHE_DIR holds essen.jsonl.gz and mtc-fs.jsonl.gz from `gtrsnipe-research corpus build`)
"""
import argparse
import json
import logging
import random
import statistics
import time
from pathlib import Path

from gtrsnipe.core.config import MapperConfig
from gtrsnipe.guitar.homograph import analyze
from gtrsnipe.research.corpus import read_cache
from gtrsnipe.research.scan import Candidate, _songs

LIMITS = (None, 50, 20, 5)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scan_json")
    ap.add_argument("cache_dir")
    ap.add_argument("--n", type=int, default=50)
    ap.add_argument("--seed", type=int, default=3)
    a = ap.parse_args()
    logging.disable(logging.WARNING)
    d = json.load(open(a.scan_json))
    melodies = []
    for c in ("essen", "mtc-fs"):
        melodies += read_cache(str(Path(a.cache_dir) / f"{c}.jsonl.gz"))[1]
    by_ref = {m.ref: m for m in melodies}
    cands = [Candidate(**{k: v for k, v in c.items() if k != "solved"})
             for cs in d["samples"].values() for c in cs]
    random.seed(a.seed)
    cands = random.sample(cands, a.n)
    t0 = time.time()
    print(f"{a.n} pairs, seed {a.seed}, anchored (A in STANDARD)")
    print("limit (points/note)  found  median discomfort  median top fret")
    for limit in LIMITS:
        found = []
        for c in cands:
            rep = analyze(_songs(c, by_ref), anchor=MapperConfig(), anchor_name="STANDARD",
                          mode="anchored", max_discomfort=limit)
            sol = rep.anchored
            if sol is not None:
                found.append((sol.discomfort, max(f for _, f in sol.positions)))
        med_d = statistics.median(x for x, _ in found) if found else float("nan")
        med_f = statistics.median(f for _, f in found) if found else float("nan")
        print(f"{'none' if limit is None else limit:>19}  {len(found):3d}/{a.n}  "
              f"{med_d:17.1f}  {med_f:15.1f}   ({time.time() - t0:.0f}s)", flush=True)


if __name__ == "__main__":
    main()
