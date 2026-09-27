"""The offset profile of two aligned melodies (backlog R02).

Align A and B note for note; the offset sequence is delta_i = b_i - a_i. Its
statistics, from docs/dev/coupled_transposition_structure.md:

richness r       distinct offsets (Hill order 0). log2 r is a metric mod
                 transposition, and r <= 6 is the offset-vocabulary condition
                 for a 6-string tab homograph (necessary, not sufficient).
entropy H        Shannon entropy of the offsets, bits (Hill order 1; a metric
                 mod transposition). R_eff = 2**H is the effective number.
coverage C_k     share of notes covered by the k most common offsets. 1 - C_1
                 is the transposition-invariant Hamming distance; C_6 < 1 rules
                 out a 6-string homograph at this alignment.
switches S       positions where the offset changes = Hamming distance between
                 the two interval sequences.
variation TV     sum |delta_{i+1} - delta_i| = L1 distance between the interval
                 sequences (the only one here that sees offset *size*).
reuse u          S + 1 - r: offset runs that return to an offset already used.
                 A guitar string is free to revisit; switch-penalized alignment
                 is not.

All of them are transposition-invariant. For chords, the offsets follow the
homograph solver's voice pairing, in tab order (by onset, then voice).
"""
from __future__ import annotations

import json
import math
from collections import Counter
from dataclasses import asdict, dataclass
from typing import List, Optional, Sequence, Tuple

K_MAX = 6          # coverage C_1..C_6 (a six-string guitar)


@dataclass
class OffsetProfile:
    n: int
    deltas: List[int]
    richness: int
    richness_mod12: int
    entropy: float
    coverage: List[float]          # C_1 .. C_K_MAX
    switches: int
    total_variation: int
    reuse: int

    @property
    def log_richness(self) -> float:
        return math.log2(self.richness) if self.richness else 0.0

    @property
    def effective(self) -> float:
        """R_eff = 2**H, the effective number of offsets."""
        return 2 ** self.entropy

    @property
    def ti_hamming(self) -> float:
        """1 - C_1: the share of notes the best single transposition misses."""
        return 1 - self.coverage[0] if self.coverage else 0.0

    def as_dict(self) -> dict:
        d = asdict(self)
        d.update(log_richness=self.log_richness, effective=self.effective,
                 ti_hamming=self.ti_hamming)
        return d


def offset_profile(a: Sequence[int], b: Sequence[int]) -> OffsetProfile:
    """The profile of two equal-length, already aligned pitch sequences."""
    if len(a) != len(b):
        raise ValueError(f"aligned melodies must have equal length ({len(a)} vs {len(b)})")
    if not a:
        raise ValueError("empty melodies")
    deltas = [y - x for x, y in zip(a, b)]
    return profile_of_deltas(deltas)


def profile_of_deltas(deltas: Sequence[int]) -> OffsetProfile:
    n = len(deltas)
    counts = Counter(deltas)
    shares = sorted((c / n for c in counts.values()), reverse=True)
    coverage, acc = [], 0.0
    for k in range(K_MAX):
        acc += shares[k] if k < len(shares) else 0.0
        coverage.append(min(1.0, acc))
    steps = [d2 - d1 for d1, d2 in zip(deltas, deltas[1:])]
    switches = sum(1 for s in steps if s)
    r = len(counts)
    return OffsetProfile(
        n=n, deltas=list(deltas), richness=r,
        richness_mod12=len({d % 12 for d in counts}),
        entropy=max(0.0, -sum(p * math.log2(p) for p in (c / n for c in counts.values()))),
        coverage=coverage, switches=switches,
        total_variation=sum(abs(s) for s in steps), reuse=switches + 1 - r)


def align_songs(song_a, song_b, *, rhythm="strict", subdivide: int = 1,
                resolution: float = 0.125) -> Tuple[Optional[List[Tuple[int, int]]], str]:
    """Pair two gtrsnipe Songs note for note with the homograph aligner. Returns
    ([(a, b) pitch pairs] in tab order, "") or (None, why they don't align)."""
    from ..guitar.homograph import align, pair_slots
    evs = [[e for t in s.tracks for e in t.events] for s in (song_a, song_b)]
    al = align(evs, rhythm=rhythm, resolution=resolution, subdivide=subdivide)
    if not al.ok:
        return None, al.reason
    return [(s.pitches[0], s.pitches[1]) for s in pair_slots(al.onsets)], ""


def profile_songs(song_a, song_b, **align_kw) -> Tuple[Optional[OffsetProfile], str]:
    pairs, why = align_songs(song_a, song_b, **align_kw)
    if pairs is None:
        return None, why
    return offset_profile([a for a, _ in pairs], [b for _, b in pairs]), ""


def _runs(deltas: Sequence[int]) -> str:
    """'+5 x4, +7 x2, +5 x3' -- the offset sequence as constant runs."""
    out, i = [], 0
    while i < len(deltas):
        j = i
        while j < len(deltas) and deltas[j] == deltas[i]:
            j += 1
        out.append(f"{deltas[i]:+d} x{j - i}" if j - i > 1 else f"{deltas[i]:+d}")
        i = j
    return ", ".join(out)


def format_profile(p: OffsetProfile, labels: Tuple[str, str] = ("A", "B")) -> str:
    a, b = labels
    cov = "  ".join(f"C{k + 1} {c:.2f}" for k, c in enumerate(p.coverage))
    top = ", ".join(f"{d:+d} ({c})" for d, c in Counter(p.deltas).most_common(8))
    lines = [
        f"Offset profile of {b} - {a}  ({p.n} aligned notes)",
        f"  Richness       {p.richness}   (mod 12: {p.richness_mod12}; log2 = {p.log_richness:.3f})"
        + ("   <= 6: a 6-string homograph is not ruled out" if p.richness <= K_MAX
           else "   > 6: no 6-string homograph at this alignment"),
        f"  Entropy        {p.entropy:.3f} bits   (effective offsets {p.effective:.2f})",
        f"  Coverage       {cov}",
        f"  TI-Hamming     {p.ti_hamming:.3f}   (1 - C1)",
        f"  Switches S     {p.switches}   (interval Hamming distance)",
        f"  Variation TV   {p.total_variation}   (interval L1 distance, semitones)",
        f"  Reuse u        {p.reuse}   (S + 1 - r)",
        f"  Offsets        {top}",
        f"  Sequence       {_runs(p.deltas)}",
    ]
    return "\n".join(lines)


def profile_json(p: OffsetProfile, **extra) -> str:
    d = p.as_dict()
    d.update(extra)
    return json.dumps(d)
