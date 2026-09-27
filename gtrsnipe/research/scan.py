"""Homographs in the wild: which passages of different songs could share one tab?
(backlog R04)

Two passages share a tab only if they align note for note -- the same rhythm
(proportional rhythms count: the same figure at another note value) -- and
their note-for-note offsets fit on the strings: richness <= 6 (six strings),
before the fret, simultaneity and physics checks. So the scan:

1. cuts every melody into units: the corpus's own phrases where it marks them
   (Essen, Meertens), else sliding windows of a fixed length;
2. buckets units by (length, rhythm), so only aligned candidates meet;
3. computes the richness of every pair in a bucket from different works
   (vectorized), and counts per length how many are eligible:
   2 <= richness <= 6 (richness 1 is a plain transposition -- a capo, not a
   homograph);
4. keeps the longest, least similar eligible pairs (one per pair of works) and
   a random sample per length, and runs the full homograph solver on them:
   anchored to STANDARD and 'middle', with string physics.

"Least similar" is the modal share C1: the fraction of notes explained by the
best single transposition. C1 near 1 is one tune with a few notes changed
(variants, shared formulas); C1 <= 1/2 means no transposition explains even
half the notes -- two tunes that sound different, the case the reductio needs.

A pair is only *interesting* when it has more distinct aligned (A, B) pitch
pairs than strings. Richness can never exceed that count, so a passage built
from <= 6 distinct pairs -- two repeated 6-note cells, say -- fits six strings
for free, however long it is. Candidates are ranked by distinct pairs first
(how much coincidence the tab needs), then by length.

Excluded from the candidates (but counted): pairs from the same work (another
voice or stanza of one song, a duplicate MIDI of one title), pairs from the same
labelled tune family, phrases that are mechanical (<= 2 distinct pitches, or a
figure repeating with a period of <= 6 notes: arpeggios, ostinatos, Alberti
basses), and pairs with <= 6 distinct aligned pitch pairs.
"""
from __future__ import annotations

import heapq
import math
import random
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from functools import reduce
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

from .corpus import Melody

STRINGS = 6
DISTINCT_C1 = 0.5
BUCKET_CAP = 6000          # units per bucket compared exhaustively; larger ones are sampled


@dataclass
class Unit:
    mel: int                   # index into the melody list
    start: int                 # note span [start, end)
    end: int
    rhythm: Tuple[int, ...]    # gcd-normalized inter-onset intervals

    @property
    def length(self) -> int:
        return self.end - self.start


def rhythm_key(onsets: Sequence[int]) -> Tuple[int, ...]:
    """Inter-onset intervals divided by their gcd, so a figure and the same
    figure at another note value (8 8 4 vs 16 16 8) share a key."""
    iois = [b - a for a, b in zip(onsets, onsets[1:])]
    g = reduce(math.gcd, iois, 0) or 1
    return tuple(x // g for x in iois)


def work_key(m: Melody) -> str:
    """Melodies with the same key are one work: Meertens voices/stanzas of one
    record (NLB123456_01, _02), Lakh duplicates of one title ('Song.1.mid')."""
    if m.corpus.startswith("mtc"):
        return m.corpus[:3] + ":" + m.id.split("/")[-1].split("_")[0]
    if m.corpus.startswith("lakh"):
        return "lakh:" + re.sub(r"\.\d+$", "", m.id).lower()
    return m.ref


def units_of(melodies: Sequence[Melody], unit: str, min_len: int, max_len: int,
             window: int = 16, stride: int = 4) -> List[Unit]:
    """'phrase': the marked phrases (melodies without marks are skipped);
    'window': every ``window``-note span at ``stride``; 'auto': phrases where
    marked, else windows."""
    out = []
    for i, m in enumerate(melodies):
        use_phrases = unit == "phrase" or (unit == "auto" and m.phrases)
        if use_phrases:
            if not m.phrases:
                continue
            for s, e in m.phrase_spans():
                if min_len <= e - s <= max_len:
                    out.append(Unit(i, s, e, rhythm_key(m.onsets[s:e])))
        else:
            for s in range(0, len(m) - window + 1, stride):
                out.append(Unit(i, s, s + window, rhythm_key(m.onsets[s:s + window])))
    return out


def mechanical(p: Sequence[int], max_period: int = STRINGS) -> bool:
    """<= 2 distinct pitches, or a figure repeating with a period of at most
    ``max_period`` notes over >= 80% of the phrase (Alberti bass, arpeggio,
    ostinato, trill)."""
    if len(set(p)) <= 2:
        return True
    n = len(p)
    return any(n >= 2 * k and sum(p[i] == p[i + k] for i in range(n - k)) >= 0.8 * (n - k)
               for k in range(1, max_period + 1))


def distinct_pairs(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    """Distinct aligned (a, b) pitch pairs per row -- an upper bound on richness."""
    S = np.sort(A.astype(np.int64) * 256 + B, axis=1)
    return 1 + (S[:, 1:] != S[:, :-1]).sum(1)


@dataclass
class LengthStats:
    units: int = 0
    pairs: int = 0             # same-rhythm pairs from different works, compared
    excluded: int = 0          # ... same labelled tune family (not compared)
    sampled_out: int = 0       # pairs skipped because a bucket exceeded BUCKET_CAP
    transposed: int = 0        # richness 1
    eligible: int = 0          # 2 <= richness <= max_richness
    trivial: int = 0           # ... but with <= max_richness distinct (a, b) pairs
    distinct: int = 0          # eligible, non-trivial, C1 <= 1/2, neither phrase mechanical
    with_partner: int = 0      # units with >= 1 such partner
    richness: Counter = field(default_factory=Counter)


@dataclass
class Candidate:
    a: str                     # corpus:id@start-end (1-based, inclusive)
    b: str
    length: int
    richness: int
    c1: float
    titles: Tuple[str, str]
    offsets: List[int]
    pairs: int = 0             # distinct aligned (a, b) pitch pairs
    solved: Optional[dict] = None

    @property
    def sort_key(self):
        return (self.pairs, self.length, -self.c1)


def _modal_share(D: np.ndarray) -> np.ndarray:
    """C1 for each row of an offsets matrix."""
    S = np.sort(D, axis=1)
    best = np.ones(len(S), dtype=np.int64)
    run = np.ones(len(S), dtype=np.int64)
    for j in range(1, S.shape[1]):
        run = np.where(S[:, j] == S[:, j - 1], run + 1, 1)
        best = np.maximum(best, run)
    return best / S.shape[1]


def _ref(m: Melody, u: Unit) -> str:
    return f"{m.ref}@{u.start + 1}-{u.end}"


def scan(melodies: Sequence[Melody], *, unit: str = "auto", max_richness: int = STRINGS,
         min_len: int = 5, max_len: int = 64, window: int = 16, stride: int = 4,
         keep: int = 300, min_keep_len: int = 8, sample_per_length: int = 0,
         cross_corpus: bool = False, seed: int = 20260926
         ) -> Tuple[Dict[int, LengthStats], List[Candidate], Dict[int, List[Candidate]]]:
    """Returns (per-length statistics, the best ``keep`` candidates -- one per
    pair of works, longest then least similar -- and up to ``sample_per_length``
    random distinct-sounding eligible pairs per length). ``cross_corpus``: only
    pair units from different corpora."""
    rng = random.Random(seed)
    units = units_of(melodies, unit, min_len, max_len, window, stride)
    work = [work_key(m) for m in melodies]
    fam = [m.family for m in melodies]
    buckets: Dict[Tuple[int, Tuple[int, ...]], List[int]] = defaultdict(list)
    for ui, u in enumerate(units):
        buckets[(u.length, u.rhythm)].append(ui)
    stats: Dict[int, LengthStats] = defaultdict(LengthStats)
    partnered = np.zeros(len(units), dtype=bool)
    best: Dict[Tuple[str, str], Candidate] = {}
    heap: List[Tuple[Tuple, Tuple[str, str]]] = []
    samples: Dict[int, List[Candidate]] = defaultdict(list)
    seen: Counter = Counter()

    def cand(i_unit: int, j_unit: int, r: int, c1: float, offsets, npairs: int) -> Candidate:
        ua, ub = units[i_unit], units[j_unit]
        ma, mb = melodies[ua.mel], melodies[ub.mel]
        return Candidate(_ref(ma, ua), _ref(mb, ub), ua.length, r, float(c1),
                         (ma.title, mb.title), [int(x) for x in offsets], int(npairs))

    for (L, _), members in buckets.items():
        st = stats[L]
        st.units += len(members)
        if len(members) < 2:
            continue
        if len(members) > BUCKET_CAP:
            k = len(members)
            st.sampled_out += k * (k - 1) // 2 - BUCKET_CAP * (BUCKET_CAP - 1) // 2
            members = rng.sample(members, BUCKET_CAP)
        P = np.stack([np.asarray(melodies[units[u].mel].pitches[units[u].start:units[u].end])
                      for u in members])
        wk = np.array([work[units[u].mel] for u in members])
        fm = np.array([fam[units[u].mel] for u in members])
        cp = np.array([melodies[units[u].mel].corpus for u in members])
        mech = np.array([mechanical(row) for row in P.tolist()])
        for i in range(len(members) - 1):
            rest = slice(i + 1, None)
            other = wk[rest] != wk[i]
            if cross_corpus:
                other &= cp[rest] != cp[i]
            same_fam = other & (fm[rest] == fm[i]) & (fm[i] != "")
            use = other & ~same_fam
            st.excluded += int(same_fam.sum())
            n_use = int(use.sum())
            if not n_use:
                continue
            st.pairs += n_use
            D = P[rest][use] - P[i]
            S = np.sort(D, axis=1)
            r = 1 + (S[:, 1:] != S[:, :-1]).sum(1)
            st.richness.update(np.minimum(r, 13).tolist())
            st.transposed += int((r == 1).sum())
            ok = (r >= 2) & (r <= max_richness)
            if not ok.any():
                continue
            st.eligible += int(ok.sum())
            idx = np.flatnonzero(use)[ok]                  # positions within `rest`
            npairs = distinct_pairs(np.broadcast_to(P[i], (len(idx), L)), P[i + 1:][idx])
            st.trivial += int((npairs <= max_richness).sum())
            c1 = _modal_share(D[ok])
            good = ((c1 <= DISTINCT_C1) & (npairs > max_richness)
                    & ~mech[i + 1:][idx] & ~mech[i])
            n_good = int(good.sum())
            if not n_good:
                continue
            st.distinct += n_good
            partnered[members[i]] = True
            partnered[[members[i + 1 + j] for j in idx[good]]] = True
            gi = np.flatnonzero(good)
            if sample_per_length:                          # reservoir sample per length
                for g in gi:
                    seen[L] += 1
                    slot = len(samples[L]) if len(samples[L]) < sample_per_length \
                        else rng.randrange(seen[L])
                    if slot < sample_per_length:
                        c = cand(members[i], members[i + 1 + idx[g]], int(r[ok][g]), c1[g],
                                 D[ok][g], npairs[g])
                        if slot == len(samples[L]):
                            samples[L].append(c)
                        else:
                            samples[L][slot] = c
            if L < min_keep_len:
                continue
            for g in gi:
                key = (int(npairs[g]), L, -float(c1[g]))
                pair = tuple(sorted((wk[i], wk[i + 1 + idx[g]])))
                if pair in best and best[pair].sort_key >= key:
                    continue
                if pair not in best and len(best) >= keep and key <= heap[0][0]:
                    continue
                best[pair] = cand(members[i], members[i + 1 + idx[g]], int(r[ok][g]), c1[g],
                                  D[ok][g], npairs[g])
                heapq.heappush(heap, (key, pair))
                while len(best) > keep:                     # evict the weakest pair
                    k0, p0 = heapq.heappop(heap)
                    if p0 in best and best[p0].sort_key == k0:
                        del best[p0]
    for ui, u in enumerate(units):
        stats[u.length].with_partner += int(partnered[ui])
    top = sorted(best.values(), key=lambda c: c.sort_key, reverse=True)
    return dict(sorted(stats.items())), top, dict(sorted(samples.items()))


# -- the physical check ---------------------------------------------------------------

def _songs(c: Candidate, by_ref: Dict[str, Melody]):
    songs = []
    for ref in (c.a, c.b):
        base, span = ref.rsplit("@", 1)
        s, e = (int(x) for x in span.split("-"))
        songs.append(by_ref[base].slice(s - 1, e).to_song())
    return songs


def solve(c: Candidate, by_ref: Dict[str, Melody]) -> dict:
    """The homograph solver on a candidate: free tunings, anchored to STANDARD
    (A stays an ordinary tab), and middle (both retune one guitar), with string
    physics. Records each mode's tunings, retunes and restrung strings."""
    from ..core.config import MapperConfig
    from ..guitar.homograph import analyze
    rep = analyze(_songs(c, by_ref), anchor=MapperConfig(), anchor_name="STANDARD",
                  mode="anchored")
    out = {"aligned": rep.alignment.ok, "richness": rep.richness}
    for mode in ("free", "anchored", "middle"):
        sol = getattr(rep, mode)
        if sol is None:
            out[mode] = None
            out[mode + "_reason"] = getattr(rep, mode + "_reason", "")
            continue
        out[mode] = {"tunings": [sol.tuning_names(j) for j in range(2)],
                     "shifts": list(sol.shifts),
                     "max_retune": max((abs(x) for j in range(2) for x in sol.retunes(j)),
                                       default=0),
                     "regauges": sol.regauges()}
    return out


def render(c: Candidate, by_ref: Dict[str, Melody], mode: str = "anchored") -> Optional[str]:
    """The shared tab for a candidate, verified to decode to both passages."""
    from ..core.config import MapperConfig
    from ..guitar.homograph import analyze, format_report, render_tab, verify_text
    rep = analyze(_songs(c, by_ref), labels=["A", "B"], titles=[c.a, c.b],
                  anchor=MapperConfig(), anchor_name="STANDARD", mode=mode)
    sol = rep.solution
    if sol is None:
        return None
    text = render_tab(rep, sol, max_line_width=100)
    if verify_text(rep, sol, text):
        return None
    return format_report(rep) + "\n\n" + text


# -- output ------------------------------------------------------------------------------

def format_stats(stats: Dict[int, LengthStats], title: str = "") -> str:
    lines = [f"Same-rhythm pairs from different works{': ' + title if title else ''}",
             "  eligible: 2 <= richness <= 6.  trivial: ... with <= 6 distinct (A,B) pitch pairs.",
             "  different-sounding: eligible, not trivial, C1 <= 1/2, no mechanical figure.",
             "  notes    units       pairs  transposed   eligible   trivial    different-sounding"
             "   units with a partner"]
    for L, s in stats.items():
        if not s.pairs:
            continue
        lines.append(f"  {L:5d} {s.units:8d} {s.pairs:11d}  {100 * s.transposed / s.pairs:9.2f}%"
                     f"  {100 * s.eligible / s.pairs:8.2f}%  {100 * s.trivial / s.pairs:7.2f}%"
                     f"  {s.distinct:10d} "
                     f"{100 * s.distinct / s.pairs:7.2f}%"
                     f"   {s.with_partner:7d} {100 * s.with_partner / max(1, s.units):6.2f}%")
    capped = sum(s.sampled_out for s in stats.values())
    if capped:
        lines.append(f"  ({capped:,} pairs in buckets over {BUCKET_CAP} units were sampled out,"
                     " not compared)")
    return "\n".join(lines)


def format_candidates(cands: Sequence[Candidate], limit: int = 25) -> str:
    """One line per candidate. Solver columns: ok, ok+Ng (N strings need another
    gauge), - (no solution), ? (not solved)."""
    def mark(c: Candidate, mode: str) -> str:
        if not c.solved:
            return "?"
        v = c.solved.get(mode)
        if v is None:
            return "-"
        return "ok" + (f"+{v['regauges']}g" if v["regauges"] else "")

    lines = ["  pairs  notes  rich    C1  anchored  middle  A  /  B"]
    for c in cands[:limit]:
        lines.append(f"  {c.pairs:5d}  {c.length:5d}  {c.richness:4d}  {c.c1:4.2f}  "
                     f"{mark(c, 'anchored'):8}  "
                     f"{mark(c, 'middle'):6}  {c.a} ({c.titles[0]})  /  {c.b} ({c.titles[1]})")
    return "\n".join(lines)


def stats_dict(stats: Dict[int, LengthStats]) -> dict:
    # not dataclasses.asdict: it rebuilds a Counter from (key, count) pairs, counting the pairs
    return {str(L): {k: ({str(r): n for r, n in sorted(v.items())} if isinstance(v, Counter)
                         else v) for k, v in vars(s).items()}
            for L, s in stats.items()}
