"""Tab homographs: one tab that plays a different song in each tuning.

A tab is a sequence of (string, fret) positions; it only becomes pitches once a
tuning is supplied (pitch = open[string] + fret). So one tab can spell several
songs, one per tuning -- a homograph (same writing, different sound, like
"bass" the fish and "bass" the guitar).

Eligibility (the theorem this module implements)
------------------------------------------------
Align songs A and B note-for-note (same onset skeleton). On any one string
a = openA + fret and b = openB + fret, so  b - a = openB - openA :  the
interval between the two songs is a property of the *string*, not the note.
Hence A and B share a tab on an N-string, F-fret instrument iff their aligned
notes split into <= N classes ("strings") where, within each class,
  (1) the difference d = b - a is constant,
  (2) no two notes sound together (a string plays one note at a time),
  (3) A's pitches span <= F semitones (every fret fits on the neck).
Conversely every such split IS a tab: openA = the class's lowest A pitch,
openB = openA + d, fret = a - openA.

So neither note count nor overall range alone decides the problem. A first lower
bound is *richness*: the number of distinct note-for-note intervals B - A. Richness 1
means B is just A transposed (a capo, not a homograph). Additional strings may still
be required when one interval class spans more than F semitones or contains simultaneous
notes. F = 0 recovers the all-open solver (each string then holds one pitch pair).
Richness is transposition-invariant (transposing B adds a constant to every d), so the
pure free-tuning richness condition depends only on melodic shape, not key; anchored and
physical modes can still depend on absolute pitch. For K songs the class key is the
vector of differences to song 0.

Modes
-----
free     : no instrument -- any tunings at all (the pure math).
anchored : song 0 keeps a real instrument's own tuning (e.g. STANDARD), so the
           shared tab is an ordinary tab of A; the other songs are retunes.
middle   : every song's tuning is a retune of the same strung instrument (each
           string may move in both -- "meeting in the middle"), so tensions stay
           balanced but the tab is in tuning A rather than STANDARD.
The physical modes search which strings each interval class owns (exactly), cost
every retune with string physics (guitar/strings.py: tightening weighted over
slackening, a penalty per string that needs another gauge, and pitches no steel
string can hold excluded), and let the Viterbi mapper pick the playable tab.
Song 0 may itself be transposed when that is what makes a pair work at all.

Re-rhythming (tabs carry little rhythm)
---------------------------------------
Onsets must line up. ``rhythm`` = 'strict' (identical, or the same rhythm at
another note value), a RATIO (each inter-onset interval may differ by up to
that factor after a global tempo scale), or 'sequence' (order only).
``subdivide`` = K additionally lets one note stand for up to K notes of the
other song ("ta" ~ "ti ti"): repeated same-pitch notes are smeared into one
held note, otherwise the single note is re-struck -- song 0 is kept intact
wherever possible. Every edit is disclosed in the report.

See docs/dev/DESIGN-homograph.md.
"""
from __future__ import annotations

import copy
import logging
import math
import re
import statistics
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from itertools import combinations, combinations_with_replacement, groupby, permutations, product
from typing import Dict, List, Optional, Sequence, Tuple, Union

import numpy as np

from ..core.config import MapperConfig
from ..core.theory import note_name_to_pitch, pitch_to_note_name
from ..core.types import MusicalEvent, Song, Track
from .mapper import GuitarMapper
from .strings import Instrument

logger = logging.getLogger(__name__)

Key = Tuple[int, ...]
Rhythm = Union[str, float]
INF = float("inf")

PERM_CAP = 720          # max chord-voice pairings tried per onset group
ENUM_CAP = 20000        # max string assignments enumerated (physical modes)
MAP_TOP = 64            # assignments re-scored with the real (Viterbi) mapper
EXTRA_STRINGS = 1       # redundant strings a class may take beyond a minimal set
UP_WEIGHT = 1.5         # tightening a string costs more than slackening (down never snaps)
REGAUGE_PENALTY = 10.0  # per string that must be swapped for another gauge
PROXY_COMFORT = (-5, 2) # no instrument model: semitone window treated as comfortable
RETUNE_WEIGHT = 5.0     # objective: per unit of retune cost vs per-note playability
A_SHIFT_COST = 2.0      # per semitone song 0 is moved from its own key
K_RANGE = 12            # transposition search half-width (semitones)
X_RANGE = 12            # middle mode: per-string offset search half-width
KVEC_CAP = 2000         # max joint transposition vectors (3+ songs)
SPLIT_COST = 1.0        # re-rhythm: per extra note a split covers
DIFF_PITCH_COST = 2.0   # ... when the covered notes differ in pitch (may add a class)
ALTER_A_COST = 1.0      # ... when it re-strikes song 0 (the tab's own song)


# -- data -------------------------------------------------------------------

@dataclass
class TabOnset:
    """One onset of the shared tab: the notes each song sounds there (equal
    counts), at song 0's time frame."""
    time: float
    duration: float
    groups: Tuple[List[MusicalEvent], ...]


@dataclass
class Slot:
    """One aligned note: sounds ``pitches[j]`` in song j (song 0 = the tab's
    own song). ``time``/``duration`` are the tab's, re-based to start at 0."""
    group: int
    time: float
    duration: float
    pitches: Tuple[int, ...]
    src: Optional[MusicalEvent] = None   # song 0's source event (as-written check)

    @property
    def key(self) -> Key:
        """The interval class: differences of every other song to song 0."""
        return tuple(p - self.pitches[0] for p in self.pitches[1:])


@dataclass
class Alignment:
    ok: bool
    reason: str = ""
    rhythm: str = "identical"            # identical | proportional | loose | sequence-only
    detail: str = ""                     # e.g. 'x2', 'worst x1.33 at onset 7'
    onsets: List[TabOnset] = field(default_factory=list)
    edits: List[str] = field(default_factory=list)


@dataclass
class Solution:
    """A shared tab: string/fret per slot plus one tuning per song.

    ``opens[j][s]`` is string s's open pitch in song j's tuning (s = 0 is the
    highest string, as everywhere in gtrsnipe). Song j decodes to its input
    pitches shifted by ``shifts[j]`` semitones."""
    mode: str                            # free | anchored | middle | as-written
    opens: List[List[int]]
    used: List[bool]
    positions: List[Tuple[int, int]]
    shifts: List[int]
    retune_cost: float = 0.0
    playability: Optional[float] = None
    instrument: Optional[Instrument] = None
    note: str = ""

    @property
    def num_strings(self) -> int:
        return len(self.opens[0])

    def tuning_names(self, j: int) -> List[str]:
        """Song j's tuning as note names, LOW -> high (the canonical order)."""
        return [pitch_to_note_name(p) for p in reversed(self.opens[j])]

    def retunes(self, j: int) -> List[int]:
        """Semitones each string moves for song j, from the instrument's own
        tuning (or from song 0's tuning when there's no instrument)."""
        ref = self.instrument.nominal if self.instrument else self.opens[0]
        return [self.opens[j][s] - ref[s] for s in range(self.num_strings)]

    def regauges(self) -> int:
        """Distinct strings outside their safe tension range in some song's tuning."""
        if self.instrument is None:
            return 0
        return sum(1 for s in range(self.num_strings) if self.used[s]
                   and any(not self.instrument.assess(s, self.opens[j][s]).ok
                           for j in range(len(self.opens))))


@dataclass
class HomographReport:
    labels: List[str]
    titles: List[str]
    note_counts: List[int]
    onset_counts: List[int]
    alignment: Alignment
    mode: str = "free"
    slots: List[Slot] = field(default_factory=list)
    classes: Dict[Key, List[int]] = field(default_factory=dict)
    richness_mod12: int = 0
    displaced: List[int] = field(default_factory=list)
    max_fret: int = 24
    max_strings: int = 12
    free: Optional[Solution] = None
    free_needed: Optional[int] = None
    free_reason: str = ""
    anchor_name: Optional[str] = None
    instrument: Optional[Instrument] = None
    anchored: Optional[Solution] = None
    anchored_reason: str = ""
    middle: Optional[Solution] = None
    middle_reason: str = ""
    as_written: Optional[Solution] = None
    as_written_reason: str = ""

    @property
    def richness(self) -> int:
        return len(self.classes)

    @property
    def solution(self) -> Optional[Solution]:
        """The solution for the requested mode."""
        return {"free": self.free, "anchored": self.anchored, "middle": self.middle}[self.mode]

    @property
    def eligible(self) -> bool:
        return self.solution is not None


# -- alignment + re-rhythming -------------------------------------------------------

def onset_groups(events: Sequence[MusicalEvent], resolution: float = 0.125
                 ) -> List[List[MusicalEvent]]:
    """Events grouped by quantized onset (a chord = one group), each group
    sorted low -> high (voice order)."""
    evs = sorted(events, key=lambda e: (e.time, e.pitch))
    return [sorted(g, key=lambda e: e.pitch)
            for _, g in groupby(evs, key=lambda e: round(e.time / resolution))]


def _parse_rhythm(rhythm: Rhythm) -> Rhythm:
    if rhythm in ("strict", "sequence"):
        return rhythm
    r = float(rhythm)
    if r < 1:
        raise ValueError("a rhythm slop ratio must be >= 1 (e.g. 1.5)")
    return r


def _fit(dur_a: float, dur_b: float, c: float, rhythm: Rhythm, tol: float) -> Tuple[bool, float]:
    """Do two spans agree (B scaled by 1/c)? Returns (ok, deviation factor >= 1)."""
    if dur_a <= 0 or dur_b <= 0:
        return rhythm == "sequence", INF
    q = dur_b / (c * dur_a)
    dev = max(q, 1 / q)
    exact = abs(dur_b - c * dur_a) <= tol * max(1.0, c)
    if rhythm == "sequence":
        return True, (1.0 if exact else dev)
    if rhythm == "strict":
        return exact, (1.0 if exact else dev)
    return exact or dev <= rhythm + 1e-9, (1.0 if exact else dev)


def _pitch_sets(groups: Sequence[List[MusicalEvent]]) -> List[Tuple[int, ...]]:
    return [tuple(e.pitch for e in g) for g in groups]


def _names(g: List[MusicalEvent]) -> str:
    return "+".join(pitch_to_note_name(e.pitch) for e in g)


def align(event_lists: Sequence[Sequence[MusicalEvent]], *, rhythm: Rhythm = "strict",
          resolution: float = 0.125, labels: Optional[Sequence[str]] = None,
          subdivide: int = 1) -> Alignment:
    """Line the songs' onsets up into one tab onset sequence.

    Every tab onset must sound the same number of notes in each song. With
    ``subdivide`` > 1 (two songs only) one note may stand for up to that many
    notes of the other song -- see the module docstring."""
    labels = list(labels or [chr(65 + i) for i in range(len(event_lists))])
    rhythm = _parse_rhythm(rhythm)
    groups = [onset_groups(evs, resolution) for evs in event_lists]
    for j, g in enumerate(groups):
        if not g:
            return Alignment(False, f"{labels[j]} has no notes")
    if subdivide > 1 and len(groups) == 2:
        if len(groups[0]) == len(groups[1]):
            plain = _align_linear(groups, rhythm, resolution, labels)
            if plain.ok:                     # a 1:1 alignment needs no re-rhythm
                return plain
        return _align_dp(groups, rhythm, resolution, labels, subdivide)
    return _align_linear(groups, rhythm, resolution, labels)


def _rel(gs: List[List[MusicalEvent]]) -> List[float]:
    t0 = gs[0][0].time
    return [g[0].time - t0 for g in gs]


def _align_linear(groups, rhythm, resolution, labels) -> Alignment:
    g0 = groups[0]
    for j in range(1, len(groups)):
        gj = groups[j]
        for t in range(min(len(g0), len(gj))):
            if len(g0[t]) != len(gj[t]):
                return Alignment(False, (
                    f"onset {t + 1}: {labels[0]} sounds {len(g0[t])} note(s), "
                    f"{labels[j]} sounds {len(gj[t])}"))
        if len(gj) != len(g0):
            n = min(len(g0), len(gj))
            return Alignment(False, (
                f"{labels[0]} has {len(g0)} onsets, {labels[j]} has {len(gj)} (their "
                f"shapes agree for the first {n}; --homograph-subdivide can re-rhythm)"))

    tol = resolution / 2 + 1e-9
    r0 = _rel(g0)
    order = ["identical", "proportional", "loose", "sequence-only"]
    worst_kind, details = "identical", []
    for j in range(1, len(groups)):
        rj = _rel(groups[j])
        if all(abs(a - b) <= tol for a, b in zip(r0, rj)):
            continue
        c = rj[-1] / r0[-1] if r0[-1] > 0 else 1.0
        if c > 0 and all(abs(c * a - b) <= tol * max(1.0, c) for a, b in zip(r0, rj)):
            worst_kind = max(worst_kind, "proportional", key=order.index)
            details.append(f"{labels[j]} x{c:g}")
            continue
        if rhythm == "sequence":
            worst_kind = "sequence-only"
            continue
        if rhythm == "strict":
            t = next(i for i, (a, b) in enumerate(zip(r0, rj))
                     if abs(c * a - b) > tol * max(1.0, c))
            return Alignment(False, (
                f"rhythms differ at onset {t + 1} ({labels[0]} beat {r0[t]:g}, "
                f"{labels[j]} beat {rj[t]:g}); --homograph-rhythm RATIO (e.g. 1.5) "
                "tolerates loose spacing; 'sequence' ignores timing"))
        worst, at = 1.0, 0
        for t in range(len(r0) - 1):
            ok, dev = _fit(r0[t + 1] - r0[t], rj[t + 1] - rj[t], c, rhythm, tol)
            if not ok:
                return Alignment(False, (
                    f"rhythms differ at onset {t + 2} ({labels[0]} beat {r0[t + 1]:g}, "
                    f"{labels[j]} beat {rj[t + 1]:g}); beyond the x{rhythm:g} slop"))
            if dev > worst:
                worst, at = dev, t + 2
        worst_kind = max(worst_kind, "loose", key=order.index)
        details.append(f"worst x{worst:.2f} at onset {at}" if at else
                       "every gap within the grid, onsets drifting")
    onsets = []
    t0 = g0[0][0].time
    for t in range(len(g0)):
        dur = max(e.duration for e in g0[t])
        onsets.append(TabOnset(g0[t][0].time - t0, dur, tuple(g[t] for g in groups)))
    return Alignment(True, rhythm=worst_kind, detail=", ".join(details), onsets=onsets)


def _align_dp(groups, rhythm, resolution, labels, kmax) -> Alignment:
    """Two songs, with 1:k / k:1 re-rhythm steps (dynamic programming)."""
    A, B = groups
    TA, TB = len(A), len(B)
    tol = resolution / 2 + 1e-9
    ta, tb = _rel(A), _rel(B)
    end_a = ta[-1] + max(e.duration for e in A[-1])
    end_b = tb[-1] + max(e.duration for e in B[-1])
    ta_x, tb_x = ta + [end_a], tb + [end_b]
    # Tempo-scale candidates: splits/merges at either end make the first or last
    # onsets unreliable, so pair each end's last few onsets (and the note ends).
    cs = {1.0}
    if end_a > 0:
        cs.add(end_b / end_a)
    for p_ in range(1, kmax + 1):
        for q_ in range(1, kmax + 1):
            if TA - p_ > 0 and TB - q_ > 0 and ta[TA - p_] > 0:
                cs.add(tb[TB - q_] / ta[TA - p_])
            if p_ < TA and q_ < TB and ta[p_] > 0:
                cs.add(tb[q_] / ta[p_])
    cs = sorted({round(c, 9) for c in cs if c > 0}, key=lambda c: (abs(math.log(c)), c))

    moves = [(1, 1)] + [(1, k) for k in range(2, kmax + 1)] + [(k, 1) for k in range(2, kmax + 1)]

    def run(c):
        best: Dict[Tuple[int, int], Tuple[float, Optional[Tuple[int, int, int, int]]]] = {(0, 0): (0.0, None)}
        for i in range(TA + 1):
            for j in range(TB + 1):
                if (i, j) not in best:
                    continue
                base = best[(i, j)][0]
                for p, q in moves:
                    ni, nj = i + p, j + q
                    if ni > TA or nj > TB:
                        continue
                    one, many = (A[i], B[j:nj]) if p == 1 else (B[j], A[i:ni])
                    if any(len(g) != len(one) for g in many):
                        continue
                    final = ni == TA and nj == TB
                    if final:
                        # last notes: durations are unreliable; only require that
                        # the many-side's re-strikes fall inside the held note
                        if p == q:
                            ok, dev = True, 1.0
                        else:
                            starts = (ta_x if p > 1 else tb_x)
                            first = i if p > 1 else j
                            last = (ni if p > 1 else nj) - 1
                            inner = starts[last] - starts[first]
                            held = (end_b - tb[j]) if p > 1 else (end_a - ta[i])
                            span = inner * (c if p > 1 else 1 / c)
                            ok, dev = (span < held + tol or rhythm == "sequence"), 1.0
                    else:
                        ok, dev = _fit(ta_x[ni] - ta_x[i], tb_x[nj] - tb_x[j], c, rhythm, tol)
                    if not ok:
                        continue
                    cost = math.log2(dev) if dev < INF else 0.0
                    if p != q:
                        k = max(p, q)
                        cost += SPLIT_COST * (k - 1)
                        if len(set(_pitch_sets(many))) > 1:
                            cost += DIFF_PITCH_COST
                            if q > 1:
                                cost += ALTER_A_COST          # A must be re-struck
                    if (ni, nj) not in best or base + cost < best[(ni, nj)][0] - 1e-12:
                        best[(ni, nj)] = (base + cost, (i, j, p, q))
        return best

    runs = [(c, run(c)) for c in cs]
    done = [(b[(TA, TB)][0], c, b) for c, b in runs if (TA, TB) in b]
    if not done:
        fi, fj = max((ij for _c, b in runs for ij in b), key=lambda ij: (ij[0] + ij[1], ij))
        return Alignment(False, (
            f"no re-rhythm with subdivision <= {kmax} lines them up: stuck after "
            f"{labels[0]} onset {fi} and {labels[1]} onset {fj} of {TA}/{TB}"))
    _cost, c, best = min(done, key=lambda x: x[0])

    steps = []
    ij = (TA, TB)
    while best[ij][1] is not None:
        i, j, p, q = best[ij][1]
        steps.append((i, j, p, q))
        ij = (i, j)
    steps.reverse()

    onsets, edits, worst, worst_at, exact = [], [], 1.0, 0, True
    for i, j, p, q in steps:
        ni, nj = i + p, j + q
        if p == q:
            onsets.append(TabOnset(ta[i], ta_x[ni] - ta[i], (A[i], B[j])))
        elif p == 1:                           # one A note vs q B notes
            many = B[j:nj]
            if len(set(_pitch_sets(many))) == 1:
                onsets.append(TabOnset(ta[i], ta_x[ni] - ta[i], (A[i], B[j])))
                edits.append(f"{labels[1]}'s {' '.join(_names(g) for g in many)} "
                             f"(onsets {j + 1}-{nj}) smeared into one held note")
            else:
                span_a, span_b = ta_x[ni] - ta[i], tb_x[nj] - tb[j]
                if ni == TA and nj == TB or span_b <= 0:
                    # the final block: map B's re-strikes through the tempo scale
                    # (as the DP checked), never by how long B's last note rings
                    offs = [min((tb[j + u] - tb[j]) / c, span_a * (1 - (q - u) * 1e-3))
                            for u in range(q)]
                else:
                    offs = [(tb[j + u] - tb[j]) * (span_a / span_b) for u in range(q)]
                for u in range(q):
                    nxt = offs[u + 1] if u + 1 < q else span_a
                    onsets.append(TabOnset(ta[i] + offs[u], nxt - offs[u], (A[i], B[j + u])))
                edits.append(f"{labels[0]}'s {_names(A[i])} (onset {i + 1}) re-struck x{q} to "
                             f"cover {labels[1]}'s {' '.join(_names(g) for g in many)}")
        else:                                  # p A notes vs one B note: keep A intact
            many = A[i:ni]
            for u in range(p):
                onsets.append(TabOnset(ta[i + u], ta_x[i + u + 1] - ta[i + u], (A[i + u], B[j])))
            edits.append(f"{labels[1]}'s {_names(B[j])} (onset {j + 1}) re-struck x{p} to "
                         f"follow {labels[0]}'s {' '.join(_names(g) for g in many)}")
        if ni < TA or nj < TB:
            ok, dev = _fit(ta_x[ni] - ta_x[i], tb_x[nj] - tb_x[j], c, rhythm, tol)
            if dev > 1.0 + 1e-9:
                exact = False
                if dev > worst:
                    worst, worst_at = dev, len(onsets)
    if exact and not edits:
        kind, detail = ("identical", "") if abs(c - 1) < 1e-9 else ("proportional", f"x{c:g}")
    elif rhythm == "sequence" and not exact:
        kind, detail = "sequence-only", ""
    else:
        kind = "loose" if not exact else ("identical" if abs(c - 1) < 1e-9 else "proportional")
        detail = (f"worst x{worst:.2f} at tab onset {worst_at}" if not exact
                  else "" if abs(c - 1) < 1e-9 else f"x{c:g}")
    return Alignment(True, rhythm=kind, detail=detail, onsets=onsets, edits=edits)


# -- pairing chord voices -------------------------------------------------------------

def _key(pitches: Tuple[int, ...]) -> Key:
    return tuple(p - pitches[0] for p in pitches[1:])


def _inversions(perm: Tuple[int, ...]) -> int:
    return sum(1 for a, b in combinations(perm, 2) if a > b)


def pair_slots(onsets: List[TabOnset], permute: bool = True) -> List[Slot]:
    """Pair the notes of each tab onset across songs.

    Single notes pair themselves. Within a chord, which voice of B answers which
    voice of A is a free choice (the tab only fixes strings), so pick the pairing
    that adds the least string demand given what's already committed -- new
    interval classes, or more simultaneous notes in one class -- tie-breaking
    toward plain voice order (low with low). Greedy, small chords first."""
    K = len(onsets[0].groups)
    maxmult: Dict[Key, int] = {}
    chosen: Dict[int, List[Tuple[int, ...]]] = {}

    def commit(tups):
        for k, m in Counter(_key(t) for t in tups).items():
            maxmult[k] = max(maxmult.get(k, 0), m)

    multi = []
    for g, on in enumerate(onsets):
        if len(on.groups[0]) == 1:
            tup = tuple(on.groups[j][0].pitch for j in range(K))
            chosen[g] = [tup]
            commit([tup])
        else:
            multi.append(g)

    for g in sorted(multi, key=lambda g: (len(onsets[g].groups[0]), g)):
        base = [e.pitch for e in onsets[g].groups[0]]
        others = [[e.pitch for e in onsets[g].groups[j]] for j in range(1, K)]
        m = len(base)
        ident = tuple(range(m))
        if permute and math.factorial(m) ** (K - 1) <= PERM_CAP:
            options = product(*[list(permutations(range(m))) for _ in others])
        else:
            options = [tuple(ident for _ in others)]
        best = None
        for combo in options:
            tups = [tuple([base[v]] + [others[j][combo[j][v]] for j in range(K - 1)])
                    for v in range(m)]
            demand = sum(max(0, n - maxmult.get(k, 0))
                         for k, n in Counter(_key(t) for t in tups).items())
            score = (demand, sum(_inversions(p) for p in combo))
            if best is None or score < best[0]:
                best = (score, tups)
        chosen[g] = best[1]
        commit(best[1])

    slots = []
    for g, on in enumerate(onsets):
        for v, tup in enumerate(chosen[g]):
            slots.append(Slot(g, on.time, on.duration, tup, on.groups[0][v]))
    return slots


def classes_of(slots: Sequence[Slot]) -> Dict[Key, List[int]]:
    out: Dict[Key, List[int]] = defaultdict(list)
    for i, s in enumerate(slots):
        out[s.key].append(i)
    return dict(sorted(out.items()))


# -- retune costs -------------------------------------------------------------------------

class RetuneCost:
    """Cost of tuning string s to a pitch: semitones from its nominal pitch
    (tightening weighted over slackening), plus REGAUGE_PENALTY if the string
    must be swapped for another gauge; INF when no steel string can hold the
    pitch at this scale, or beyond ``max_retune``. Without an instrument the
    PROXY_COMFORT semitone window stands in for the physics."""

    def __init__(self, nominal: Sequence[int], instrument: Optional[Instrument] = None,
                 max_retune: Optional[int] = None):
        self.nominal = list(nominal)
        self.instrument = instrument
        self.max_retune = max_retune
        self._cache: Dict[Tuple[int, int], float] = {}

    def __call__(self, s: int, pitch: int) -> float:
        k = (s, pitch)
        if k not in self._cache:
            self._cache[k] = self._cost(s, pitch)
        return self._cache[k]

    def _cost(self, s: int, pitch: int) -> float:
        if not 0 <= pitch <= 127:
            return INF
        d = pitch - self.nominal[s]
        if self.max_retune is not None and abs(d) > self.max_retune:
            return INF
        v = d * UP_WEIGHT if d > 0 else float(-d)
        if self.instrument is not None:
            st = self.instrument.assess(s, pitch).status
            if st == "impossible":
                return INF
            if st != "ok":
                v += REGAUGE_PENALTY
        elif not PROXY_COMFORT[0] <= d <= PROXY_COMFORT[1]:
            v += REGAUGE_PENALTY
        return v


def _k_candidates(transpose, center: int = 0, half: int = K_RANGE) -> List[int]:
    """Transpositions to try: 'keep' -> [0]; an int -> [it]; 'auto' -> a window
    around ``center``, small |k| first (and down before up: down never snaps)."""
    if transpose == "keep":
        return [0]
    if isinstance(transpose, int) and not isinstance(transpose, bool):
        return [transpose]
    return sorted(range(center - half, center + half + 1), key=lambda k: (abs(k), k))


def _center(values: Sequence[int]) -> int:
    return -int(round(statistics.median(values))) if values else 0


def _best_shift(bases: Sequence[Tuple[int, int]], cost: RetuneCost, transpose
                ) -> Optional[Tuple[int, float]]:
    """k minimizing sum cost(s, base + k) over (string, base pitch) pairs."""
    best = None
    center = _center([b - cost.nominal[s] for s, b in bases])
    for k in _k_candidates(transpose, center):
        v = sum(cost(s, b + k) for s, b in bases)
        if v < INF and (best is None or v < best[1]):
            best = (k, v)
    return best


def fold_octaves(slots: List[Slot], transpose="auto") -> List[int]:
    """Arrangement liberty: displace individual notes of songs 1.. by octaves so
    each interval class mod 12 collapses to one class. Which octave each class
    keeps is chosen jointly to minimize (retune cost + notes displaced) -- a
    plain majority vote can widen the retune spread and break a signature leap.
    Mutates ``slots``; returns how many notes were displaced per song."""
    K = len(slots[0].pitches)
    displaced = [0] * K
    for j in range(1, K):
        by_res: Dict[int, Counter] = defaultdict(Counter)
        for s in slots:
            d = s.pitches[j] - s.pitches[0]
            by_res[d % 12][d] += 1
        residues = sorted(by_res)
        options = [[d for d, _ in by_res[r].most_common(3)] for r in residues]
        if math.prod(len(o) for o in options) > 4096:
            options = [o[:1] for o in options]           # too many: majority vote
        proxy = RetuneCost([0] * len(residues))
        best = None
        for reps in product(*options):
            moved = sum(n for r, rep_d in zip(residues, reps)
                        for d, n in by_res[r].items() if d != rep_d)
            shift = _best_shift(list(enumerate(reps)), proxy, transpose)
            cost = (shift[1] if shift else 1e6) + moved
            if best is None or (cost, moved, reps) < best[0]:
                best = ((cost, moved, reps), reps)
        rep = dict(zip(residues, best[1]))
        for s in slots:
            d = s.pitches[j] - s.pitches[0]
            nd = rep[d % 12]
            if nd != d:
                p = list(s.pitches)
                p[j] = s.pitches[0] + nd
                s.pitches = tuple(p)
                displaced[j] += 1
    return displaced


# -- shared helpers -------------------------------------------------------------------------

def _match(options: List[List[int]]) -> Optional[List[int]]:
    """Injective choice of one option per item (tiny bipartite matching)."""
    order = sorted(range(len(options)), key=lambda i: len(options[i]))
    pick: Dict[int, int] = {}
    used = set()

    def bt(k):
        if k == len(order):
            return True
        i = order[k]
        for o in options[i]:
            if o not in used:
                used.add(o)
                pick[i] = o
                if bt(k + 1):
                    return True
                used.discard(o)
        return False

    return [pick[i] for i in range(len(options))] if bt(0) else None


def _popcount(x: int) -> int:
    return bin(x).count("1")


def fmt_interval(d: int) -> str:
    return f"{d:+d}" if d else "0"


def fmt_key(key: Key) -> str:
    return (fmt_interval(key[0]) if len(key) == 1
            else "(" + ",".join(fmt_interval(x) for x in key) + ")")


def _names_of(pitches: Sequence[int]) -> Tuple[str, ...]:
    return tuple(pitch_to_note_name(p) for p in pitches)


# -- free mode: both tunings free -------------------------------------------------------------

def _pack_class(items: List[Tuple[int, int, int]], max_fret: int, max_bins: int
                ) -> Optional[List[List[int]]]:
    """Fewest strings for one interval class. ``items`` = (slot, group, pitch).
    Each string covers a window of max_fret+1 semitones and plays one note per
    onset. Exact for melodies (a greedy window cover); with chords inside the
    class, the best found on a fixed budget, never worse than a greedy bound.
    Returns the slot indices per string, or None past ``max_bins``."""
    by_group: Dict[int, List[Tuple[int, int, int]]] = defaultdict(list)
    for it in items:
        by_group[it[1]].append(it)
    mult = max(len(v) for v in by_group.values())
    pitches = sorted({it[2] for it in items})

    if pitches[-1] - pitches[0] <= max_fret:       # common case: one window fits all
        if mult > max_bins:
            return None
        bins: List[List[int]] = [[] for _ in range(mult)]
        for its in by_group.values():
            for b, it in enumerate(sorted(its, key=lambda x: x[2])):
                bins[b].append(it[0])
        return bins

    # Greedy window cover (interval point cover): optimal when no two notes of
    # the class sound together, which is every melody.
    windows = []
    for pch in pitches:
        if not windows or pch > windows[-1] + max_fret:
            windows.append(pch)

    def window_of(pch):
        return max(i for i, lo in enumerate(windows) if lo <= pch)

    if mult == 1:
        if len(windows) > max_bins:
            return None
        bins = [[] for _ in windows]
        for it in items:
            bins[window_of(it[2])].append(it[0])
        return bins

    # Chords inside the class: each window replicated once per simultaneous voice
    # is always feasible, so search (on a fixed budget) only for something smaller.
    upper = len(windows) * mult
    budget = 20000
    for k in range(max(mult, len(windows)), min(upper, max_bins + 1)):
        for los in combinations_with_replacement(pitches, k):
            budget -= 1
            if budget < 0:
                break
            assign: Dict[int, int] = {}
            for its in by_group.values():
                m = _match([[b for b, lo in enumerate(los) if lo <= it[2] <= lo + max_fret]
                            for it in its])
                if m is None:
                    break
                assign.update({it[0]: b for it, b in zip(its, m)})
            else:
                bins = [[] for _ in range(k)]
                for idx, b in assign.items():
                    bins[b].append(idx)
                return [b for b in bins if b]
        if budget < 0:
            break
    if upper > max_bins:
        return None
    bins = [[] for _ in range(upper)]
    for its in by_group.values():
        used: Dict[int, int] = defaultdict(int)
        for it in its:
            w = window_of(it[2])
            bins[w * mult + used[w]].append(it[0])
            used[w] += 1
    return [b for b in bins if b]


def solve_free(slots: List[Slot], *, max_fret: int = 24, max_strings: int = 12,
               transpose="auto", max_retune: Optional[int] = None
               ) -> Tuple[Optional[Solution], Optional[int], str]:
    """Both tunings free. Returns (solution | None, strings needed | None, reason)."""
    strings = []                                   # (open0, key, [slot idx])
    for key, idxs in classes_of(slots).items():
        items = [(i, slots[i].group, slots[i].pitches[0]) for i in idxs]
        bins = _pack_class(items, max_fret, 64)
        if bins is None:
            return None, None, f"interval class {fmt_key(key)} needs more than 64 strings"
        for members in bins:
            strings.append((min(slots[i].pitches[0] for i in members), key, members))
    needed = len(strings)
    if needed > max_strings:
        return None, needed, (f"needs {needed} strings (max {max_strings}; "
                              "raise --max-strings)")

    strings.sort(key=lambda s: (-s[0], s[1]))       # index 0 = highest string
    K = len(slots[0].pitches)
    open0 = [s[0] for s in strings]
    cost = RetuneCost(open0, None, max_retune)
    shifts, total = [0], 0.0
    for j in range(1, K):
        res = _best_shift([(si, s[0] + s[1][j - 1]) for si, s in enumerate(strings)],
                          cost, transpose)
        if res is None:
            return None, needed, f"no transposition keeps every retune within ±{max_retune}"
        shifts.append(res[0])
        total += res[1]
    opens = [open0] + [[s[0] + s[1][j - 1] + shifts[j] for s in strings] for j in range(1, K)]
    positions: List[Tuple[int, int]] = [(0, 0)] * len(slots)
    for si, (o, _key_, members) in enumerate(strings):
        for i in members:
            positions[i] = (si, slots[i].pitches[0] - o)
    sol = Solution("free", opens, [True] * needed, positions, shifts, retune_cost=total)
    return sol, needed, ""


# -- physical modes: a real strung instrument ----------------------------------------------------

class _PinnedMapper(GuitarMapper):
    """The fretboard mapper, restricted to the strings each note's class owns."""

    def __init__(self, config: MapperConfig, allowed: Dict[int, int]):
        super().__init__(config)
        self._allowed = allowed                      # id(event) -> string bitmask

    def _positions_for(self, note):
        pos = super()._positions_for(note)
        mask = self._allowed.get(id(note))
        if not pos or mask is None:
            return pos
        return {p for p in pos if (mask >> p.string) & 1}


def _config_for_tuning(config: MapperConfig, open_high_to_low: Sequence[int]) -> MapperConfig:
    cfg = copy.deepcopy(config)
    cfg.capo = 0
    cfg.deduplicate_pitches = False
    cfg.tuning = "CUSTOM"
    cfg.custom_tuning = tuple(reversed(_names_of(open_high_to_low)))
    cfg.num_strings = len(open_high_to_low)
    return cfg


def _map_pinned(slots: List[Slot], cfg: MapperConfig, string_key: List[Optional[Key]]
                ) -> Tuple[Optional[List[Tuple[int, int]]], float]:
    """Most playable fingering of song 0 with every note on a string of its own
    class. Returns (positions per slot, mapper path score)."""
    events, allowed = [], {}
    for s in slots:
        ev = MusicalEvent(s.time, s.pitches[0], s.duration, 100)
        allowed[id(ev)] = sum(1 << st for st, k in enumerate(string_key) if k == s.key)
        events.append(ev)
    groups: Dict[int, List[MusicalEvent]] = defaultdict(list)
    for s, ev in zip(slots, events):
        groups[s.group].append(ev)
    mapper = _PinnedMapper(cfg, allowed)
    mapper.map_multi_string([groups[g] for g in sorted(groups)])
    if any(ev.string is None for ev in events):
        return None, float("-inf")
    return [(ev.string, ev.fret) for ev in events], mapper.last_path_score or 0.0


def _proxy_cost(slots: List[Slot], open0: List[int], string_key: List[Optional[Key]]) -> float:
    """Cheap playability estimate used to score assignments before the real
    mapper runs: hand movement + high frets (first string of each class)."""
    first = {}
    for st, k in enumerate(string_key):
        if k is not None and k not in first:
            first[k] = st
    cost, prev = 0.0, None
    for s in slots:
        st = first[s.key]
        f = s.pitches[0] - open0[st]
        if prev is not None:
            cost += 3 * abs(f - prev[1]) + (5 if st != prev[0] else 0)
        cost += max(0, f - 12) * 5
        prev = (st, f)
    return cost


@dataclass
class _Cand:
    """One way to place the interval classes on strings (before fingering)."""
    rc: float                            # physical retune cost
    order: list                          # deterministic tie-break
    string_key: List[Optional[Key]]
    kv: Tuple[int, ...]                  # transpositions of songs 1..
    tau0: List[int]                      # song 0's tuning (high->low)
    t: int                               # song 0's transposition
    slots: List[Slot]                    # the slots with song 0 moved by t
    base_cfg: MapperConfig
    nominal: List[int]
    truncated: bool

    @property
    def primary(self) -> float:
        return RETUNE_WEIGHT * self.rc + A_SHIFT_COST * abs(self.t)


def _placement_candidates(slots: List[Slot], config: MapperConfig, *, mode: str,
                          instrument: Optional[Instrument], transpose, max_retune,
                          t: int = 0) -> Tuple[List[_Cand], str, RetuneCost]:
    """Physical modes on the instrument ``config`` names (its tuning / custom
    tuning / max_fret): 'anchored' pins song 0 to that tuning, 'middle' lets
    every string move for every song. The cheap phase: every way of giving the
    interval classes strings (each inclusion-minimal choice, plus at most one
    redundant string), each with the transpositions -- and in middle mode each
    string's offset -- that minimize its physical retune cost."""
    base_cfg = copy.deepcopy(config)
    base_cfg.capo = 0
    base_cfg.deduplicate_pitches = False
    nominal = GuitarMapper(base_cfg).open_string_pitches
    N, F = len(nominal), base_cfg.max_fret
    cost = RetuneCost(nominal, instrument, max_retune)
    full = (1 << N) - 1
    cls = classes_of(slots)
    keys = list(cls)
    r = len(keys)
    K = len(slots[0].pitches)
    if r > N:
        return [], (f"richness {r} > {N} strings: the songs differ by {r} distinct "
                    f"intervals, each needing its own string"), cost

    # Offsets x per (class, string): song 0's tuning = nominal + x, keeping every
    # note of the class on the neck. Anchored: x = 0 only.
    class_of = {i: c for c, key in enumerate(keys) for i in cls[key]}
    xs: List[List[List[int]]] = []
    for c, key in enumerate(keys):
        ps = [slots[i].pitches[0] for i in cls[key]]
        row = []
        for s in range(N):
            lo, hi = max(ps) - F - nominal[s], min(ps) - nominal[s]
            if mode == "anchored":
                row.append([0] if lo <= 0 <= hi else [])
            else:
                row.append([x for x in range(max(lo, -X_RANGE), min(hi, X_RANGE) + 1)
                            if cost(s, nominal[s] + x) < INF])
        xs.append(row)

    if mode == "anchored":
        reach = [sum(1 << s for s in range(N) if 0 <= sl.pitches[0] - nominal[s] <= F)
                 for sl in slots]
    else:
        cmask = [sum(1 << s for s in range(N) if xs[c][s]) for c in range(r)]
        reach = [cmask[class_of[i]] for i in range(len(slots))]
        for i, m in enumerate(reach):
            a = slots[i].pitches[0]
            if not m and any(0 <= a - nominal[s] - x <= F and cost(s, nominal[s] + x) < INF
                             for s in range(N) for x in range(-X_RANGE, X_RANGE + 1)):
                return [], (f"interval class {fmt_key(keys[class_of[i]])} spans more than "
                            "one retuned string can hold"), cost
    for i, m in enumerate(reach):
        if not m:
            return [], (f"{pitch_to_note_name(slots[i].pitches[0])} (note {i + 1} of "
                        "song A) is out of range of the instrument"), cost

    reqs = []
    for key in keys:
        per_group: Dict[int, List[int]] = defaultdict(list)
        for i in cls[key]:
            per_group[slots[i].group].append(reach[i])
        reqs.append({tuple(sorted(v)) for v in per_group.values()})

    memo: Dict[Tuple[int, int], bool] = {}

    def feasible(c: int, S: int) -> bool:
        k = (c, S)
        if k not in memo:
            ok = True
            for req in reqs[c]:
                if len(req) == 1:
                    if not req[0] & S:
                        ok = False
                        break
                elif _match([[s for s in range(N) if (m & S) >> s & 1] for m in req]) is None:
                    ok = False
                    break
            memo[k] = ok
        return memo[k]

    allowed_sets: List[List[int]] = []
    minimal_union: List[int] = []
    for c in range(r):
        sets, union = [], 0
        for S in range(1, full + 1):
            if not feasible(c, S):
                continue
            redundant = sum(1 for s in range(N) if (S >> s) & 1 and feasible(c, S & ~(1 << s)))
            if redundant == 0:
                union |= S
            if redundant <= EXTRA_STRINGS:
                sets.append(S)
        if not sets:
            return [], (f"interval class {fmt_key(keys[c])} can't be placed on any "
                        "set of strings (too many simultaneous notes in range)"), cost
        sets.sort(key=lambda S: (_popcount(S), S))
        allowed_sets.append(sets)
        minimal_union.append(union)

    min_size = [_popcount(s[0]) for s in allowed_sets]
    order = sorted(range(r), key=lambda c: (len(allowed_sets[c]), c))
    results: List[Dict[int, int]] = []
    truncated = False

    def bt(ci: int, used: int, assign: Dict[int, int]):
        nonlocal truncated
        if len(results) >= ENUM_CAP:
            truncated = True
            return
        if ci == r:
            results.append(dict(assign))
            return
        c = order[ci]
        need_after = sum(min_size[order[x]] for x in range(ci + 1, r))
        for S in allowed_sets[c]:
            if S & used or _popcount(full & ~(used | S)) < need_after:
                continue
            assign[c] = S
            bt(ci + 1, used | S, assign)
            del assign[c]
            if truncated:
                return

    bt(0, 0, {})
    if not results:
        return [], _hall_reason(keys, min_size, minimal_union, nominal), cost

    # Joint transposition vectors for songs 1..K-1, each centred on its median interval.
    half = K_RANGE
    while (2 * half + 1) ** (K - 1) > KVEC_CAP and half > 1:
        half -= 1
    per_song = [_k_candidates(transpose, _center([k[j] for k in keys]), half)
                for j in range(K - 1)]
    kvecs = list(product(*per_song))

    # G[(c, s)]: best cost of string s hosting class c, per kvec (+ the best x).
    G: Dict[Tuple[int, int], Tuple[np.ndarray, List[int]]] = {}

    def g_for(c: int, s: int):
        if (c, s) not in G:
            vals, args = np.full(len(kvecs), INF), [0] * len(kvecs)
            key = keys[c]
            for vi, kv in enumerate(kvecs):
                for x in xs[c][s] if mode == "middle" else [0]:
                    t0 = nominal[s] + x
                    v = cost(s, t0)
                    for j in range(K - 1):
                        v += cost(s, t0 + key[j] + kv[j])
                        if v == INF:
                            break
                    if v < vals[vi]:
                        vals[vi], args[vi] = v, x
            G[(c, s)] = (vals, args)
        return G[(c, s)]

    out: List[_Cand] = []
    for assign in results:
        pairs = [(c, s) for c, S in assign.items() for s in range(N) if (S >> s) & 1]
        tot = np.zeros(len(kvecs))
        for c, s in pairs:
            tot = tot + g_for(c, s)[0]
        vi = int(np.argmin(tot))                    # first min = smallest |k|
        if tot[vi] == INF:
            continue
        string_key: List[Optional[Key]] = [None] * N
        tau0 = list(nominal)
        for c, s in pairs:
            string_key[s] = keys[c]
            tau0[s] = nominal[s] + g_for(c, s)[1][vi]
        out.append(_Cand(float(tot[vi]), sorted(assign.items()), string_key, kvecs[vi],
                         tau0, t, slots, base_cfg, nominal, truncated))
    if not out:
        why = f"within ±{max_retune}" if max_retune is not None else "without breaking a string"
        return [], f"no string assignment can be retuned {why}", cost
    return out, "", cost


def _needs_regauge(c: _Cand, cost: RetuneCost) -> bool:
    if cost.instrument is None:
        return False
    for s, key in enumerate(c.string_key):
        if key is None:
            continue
        pitches = [c.tau0[s]] + [c.tau0[s] + key[j] + c.kv[j] for j in range(len(key))]
        if any(not cost.instrument.assess(s, p).ok for p in pitches):
            return True
    return False


def _finalize(cands: List[_Cand], mode: str, instrument: Optional[Instrument]
              ) -> Optional[Solution]:
    """The expensive phase: finger the most promising placements with the
    Viterbi mapper and keep the best (retune cost vs per-note playability)."""
    cands = sorted(cands, key=lambda c: (c.primary, abs(c.t), c.t, c.order))
    cutoff = cands[min(len(cands), 4 * MAP_TOP) - 1].primary
    pool = [c for c in cands if c.primary <= cutoff][:5000]
    pool.sort(key=lambda c: (c.primary, _proxy_cost(c.slots, c.tau0, c.string_key),
                             abs(c.t), c.t, c.order))
    best = None
    mapper_log = logging.getLogger(GuitarMapper.__module__)
    saved_level = mapper_log.level
    mapper_log.setLevel(logging.WARNING)             # one init line per candidate is noise
    try:
        for c in pool[:MAP_TOP]:
            positions, play = _map_pinned(c.slots, _config_for_tuning(c.base_cfg, c.tau0),
                                          c.string_key)
            if positions is None:
                continue
            obj = c.primary - play / len(c.slots)
            if best is None or obj < best[0]:
                best = (obj, c, play, positions)
    finally:
        mapper_log.setLevel(saved_level)
    if best is None:
        return None
    _obj, c, play, positions = best
    K = len(c.slots[0].pitches)
    opens = [list(c.tau0)]
    for j in range(K - 1):
        opens.append([c.tau0[s] + key[j] + c.kv[j] if key is not None else c.nominal[s]
                      for s, key in enumerate(c.string_key)])
    note = f"search truncated at {ENUM_CAP} assignments" if c.truncated else ""
    return Solution(mode, opens, [k is not None for k in c.string_key], positions,
                    [c.t] + list(c.kv), retune_cost=c.rc, playability=play,
                    instrument=instrument, note=note)


def _shift_song0(slots: List[Slot], t: int) -> List[Slot]:
    return [Slot(s.group, s.time, s.duration, (s.pitches[0] + t,) + s.pitches[1:], s.src)
            for s in slots]


def solve_physical(slots: List[Slot], config: MapperConfig, *, mode: str = "anchored",
                   instrument: Optional[Instrument] = None, transpose="auto",
                   transpose_a="auto", max_retune: Optional[int] = None
                   ) -> Tuple[Optional[Solution], str]:
    """Anchored/middle solve, also weighing transpositions of song 0 (the tab's
    own song): 'keep' never moves it, an int moves it that far, 'auto' keeps its
    key when that already works without re-stringing (middle mode: whenever it
    works at all -- each string's own offset already absorbs a transposition)
    and otherwise weighs +-12, moving it at a small cost per semitone."""
    if isinstance(transpose_a, int) and not isinstance(transpose_a, bool):
        first = transpose_a
    else:
        first = 0
    kw = dict(instrument=instrument, transpose=transpose, max_retune=max_retune)

    def gather(t: int):
        sl = slots if t == 0 else _shift_song0(slots, t)
        found, why, cost = _placement_candidates(sl, config, t=t, mode=mode, **kw)
        if mode == "middle":
            # Middle is anchored plus per-string offsets, so anchored's placements
            # (every offset 0, notes routed string by string) are middle solutions
            # too. Adding them keeps middle a superset of anchored even when an
            # interval class spans wider than one retuned string can hold.
            anc, anc_why, _ = _placement_candidates(sl, config, t=t, mode="anchored", **kw)
            if not found and not anc and why.startswith("interval class") and "spans" in why:
                why = anc_why
            found = found + anc
        return found, why, cost

    cands, reason, cost = gather(first)
    if transpose_a == "auto":
        settled = cands and (mode == "middle" or any(not _needs_regauge(c, cost) for c in cands))
        if not settled:
            for t in _k_candidates("auto", 0, K_RANGE)[1:]:
                cands += gather(t)[0]
    if not cands:
        return None, reason
    sol = _finalize(cands, mode, instrument)
    if sol is None:
        return None, "the mapper found no playable fingering for any string assignment"
    return sol, ""


def _hall_reason(keys: List[Key], min_size: List[int], union: List[int],
                 nominal: List[int]) -> str:
    """Explain an infeasible search: the smallest group of interval classes that
    needs more strings than the strings able to host it."""
    names = [pitch_to_note_name(p) for p in nominal]
    for size in range(1, len(keys) + 1):
        for fam in combinations(range(len(keys)), size):
            u = 0
            for c in fam:
                u |= union[c]
            if sum(min_size[c] for c in fam) > _popcount(u):
                strs = ", ".join(names[s] for s in range(len(nominal)) if (u >> s) & 1) or "none"
                cl = ", ".join(fmt_key(keys[c]) for c in fam)
                return (f"interval classes {{{cl}}} need {sum(min_size[c] for c in fam)} "
                        f"string(s) but only these can reach their notes: {strs}")
    return "no assignment of interval classes to the instrument's strings covers every note"


# -- as written: a fixed, given tab -----------------------------------------------------------

def check_as_written(slots: List[Slot], *, tab_tuning: Optional[List[int]] = None,
                     max_fret: int = 24, transpose="auto", max_retune: Optional[int] = None,
                     instrument: Optional[Instrument] = None) -> Tuple[Optional[Solution], str]:
    """When song 0 came from a tab, can its *own* fingering be retuned into the
    other songs? True iff every string carries a single interval class.
    ``tab_tuning``: the tab's open pitches (high->low), for its unused strings."""
    if any(s.src is None or s.src.string is None or s.src.fret is None for s in slots):
        return None, "song A carries no fingering (not a tab)"
    high = max(s.src.fret for s in slots)
    if high > max_fret or min(s.src.fret for s in slots) < 0:
        return None, f"the tab uses fret {high}, beyond --max-fret {max_fret}"
    by_string: Dict[int, set] = defaultdict(set)
    open0: Dict[int, int] = {}
    for s in slots:
        by_string[s.src.string].add(s.key)
        open0[s.src.string] = s.pitches[0] - s.src.fret
    bad = {st: ks for st, ks in by_string.items() if len(ks) > 1}
    if bad:
        st, ks = min(bad.items())
        return None, (f"string {st + 1} carries {len(ks)} different intervals "
                      f"({', '.join(fmt_key(k) for k in sorted(ks))}); one string "
                      "can only shift by one")
    N = max(len(tab_tuning or []), max(by_string) + 1)
    # Strings with notes use the pitch the tab actually decoded to; an unused
    # string keeps the tab's tuning (or, unknown, its neighbour's -- display only).
    base = []
    for s in range(N):
        if s in open0:
            base.append(open0[s])
        elif tab_tuning and s < len(tab_tuning):
            base.append(tab_tuning[s])
        else:
            base.append(open0[min(open0, key=lambda u: abs(u - s))])
    inst = instrument if instrument is not None and len(instrument.nominal) == N else None
    cost = RetuneCost(inst.nominal if inst else base, inst, max_retune)
    K = len(slots[0].pitches)
    shifts, total = [0], sum(cost(s, base[s]) for s in by_string)
    for j in range(1, K):
        res = _best_shift([(s, base[s] + next(iter(by_string[s]))[j - 1])
                           for s in sorted(by_string)], cost, transpose)
        if res is None:
            return None, "no transposition can be tuned without breaking a string" \
                if max_retune is None else f"no transposition keeps every retune within ±{max_retune}"
        shifts.append(res[0])
        total += res[1]
    opens = [base] + [[base[s] + (next(iter(by_string[s]))[j - 1] + shifts[j]
                                  if s in by_string else 0) for s in range(N)]
                      for j in range(1, K)]
    positions = [(s.src.string, s.src.fret) for s in slots]
    return Solution("as-written", opens, [s in by_string for s in range(N)], positions,
                    shifts, retune_cost=total, instrument=inst), ""


# -- verification + rendering -------------------------------------------------------------------

def verify(slots: List[Slot], sol: Solution, max_fret: int = 24) -> List[str]:
    """Independent check: decoding the tab in each song's tuning reproduces that
    song. Returns a list of problems (empty = verified)."""
    problems = []
    by_group: Dict[int, set] = defaultdict(set)
    for i, (sl, (s, f)) in enumerate(zip(slots, sol.positions)):
        if not 0 <= f <= max_fret:
            problems.append(f"note {i + 1}: fret {f} off the neck")
        if s in by_group[sl.group]:
            problems.append(f"note {i + 1}: string {s + 1} already sounding")
        by_group[sl.group].add(s)
        for j, p in enumerate(sl.pitches):
            if sol.opens[j][s] + f != p + sol.shifts[j]:
                problems.append(f"note {i + 1}: song {j} decodes to "
                                f"{sol.opens[j][s] + f}, expected {p + sol.shifts[j]}")
    return problems


def decoded_song(slots: List[Slot], sol: Solution, j: int, *, title: str = "",
                 tempo: float = 120.0, time_signature: str = "4/4") -> Song:
    """The shared tab as a pre-mapped Song sounding song j (for tab/player output)."""
    events = [MusicalEvent(sl.time, sl.pitches[j] + sol.shifts[j], sl.duration, 100,
                           string=s, fret=f)
              for sl, (s, f) in zip(slots, sol.positions)]
    return Song(tracks=[Track(events=events)], tempo=tempo,
                time_signature=time_signature, title=title)


def config_for_song(sol: Solution, j: int, base: Optional[MapperConfig] = None) -> MapperConfig:
    cfg = copy.deepcopy(base) if base else MapperConfig()
    cfg.tuning = "CUSTOM"
    cfg.custom_tuning = tuple(sol.tuning_names(j))
    cfg.num_strings = sol.num_strings
    cfg.capo = 0
    cfg.mono_lowest_only = False     # a render option must never drop notes of the tab
    return cfg


_TAB_LINE = re.compile(r"^\s*[^\s|/]{1,3}\|")


def render_tab(report: HomographReport, sol: Solution, *, neutral: bool = False,
               max_line_width: int = 80, command_line: str = "",
               base_config: Optional[MapperConfig] = None, tempo: float = 120.0,
               time_signature: str = "4/4") -> str:
    """ASCII tab of the shared fingering, with every song's tuning key in the
    header. Normal: labeled + '// Tuning:' for song 0, so it reads (and parses)
    as an ordinary tab of A. ``neutral``: strings numbered 1..N and no default
    tuning, so the text privileges no song."""
    from ..formats.tab.generator.ascii import AsciiTabGenerator

    title = report.titles[0] if not neutral else "homograph"
    song = decoded_song(report.slots, sol, 0, title=title, tempo=tempo,
                        time_signature=time_signature)
    cfg = config_for_song(sol, 0, base_config)
    # no_articulations: an 'h'/'p' prefix shifts a chord note's digits one column
    # right, so the parser would split the chord (the digits' column is the time).
    text = AsciiTabGenerator.generate(song, command_line=command_line,
                                      max_line_width=max_line_width, no_articulations=True,
                                      mapper_config=cfg, premapped=True)
    keys = ["// Homograph: this one tab plays a different song in each tuning (low->high):"]
    for j, lab in enumerate(report.labels):
        shift = sol.shifts[j]
        tail = f" (transposed {fmt_interval(shift)})" if shift else ""
        keys.append(f"//   Key {lab}: {','.join(sol.tuning_names(j))}  = {report.titles[j]}{tail}")
    if report.alignment.edits:
        keys.append("// Re-rhythmed: " + "; ".join(report.alignment.edits))

    out, run = [], 0
    for line in text.split("\n"):
        if line.startswith("// Tuning:"):
            if not neutral:
                out.append(line)
            out.extend(keys)
            continue
        if neutral and _TAB_LINE.match(line):
            line = f"{run % sol.num_strings + 1}|" + line.split("|", 1)[1]
            run += 1
        out.append(line)
    return "\n".join(out)


def verify_text(report: HomographReport, sol: Solution, text: str) -> List[str]:
    """Re-parse the RENDERED tab in each song's tuning and compare it, onset by
    onset, with the songs -- so "Verified" covers the text actually written, not
    just the solver's positions. Returns a list of problems (empty = verified)."""
    from ..formats.tab.parser import AsciiTabParser

    by_group: Dict[int, List[int]] = defaultdict(list)
    for i, sl in enumerate(report.slots):
        by_group[sl.group].append(i)
    problems = []
    for j, lab in enumerate(report.labels):
        parsed = AsciiTabParser.parse(text, open_string_pitches=sol.opens[j])
        got = [sorted(e.pitch for e in g) for g in
               onset_groups([e for t in parsed.tracks for e in t.events], 1e-6)]
        want = [sorted(report.slots[i].pitches[j] + sol.shifts[j] for i in by_group[g])
                for g in sorted(by_group)]
        if got != want:
            k = next((n for n, (x, y) in enumerate(zip(got, want)) if x != y),
                     min(len(got), len(want)))
            problems.append(f"song {lab}: tab onset {k + 1} decodes to "
                            f"{got[k] if k < len(got) else 'nothing'}, expected "
                            f"{want[k] if k < len(want) else 'nothing'}")
    return problems


# -- the one-call analysis ----------------------------------------------------------------------

def analyze(songs: Sequence[Song], *, labels: Optional[Sequence[str]] = None,
            titles: Optional[Sequence[str]] = None,
            anchor: Optional[MapperConfig] = None, anchor_name: Optional[str] = None,
            mode: Optional[str] = None, instrument: Optional[Instrument] = None,
            max_fret: int = 24, max_strings: int = 12, rhythm: Rhythm = "strict",
            subdivide: int = 1, transpose="auto", transpose_a="auto",
            max_retune: Optional[int] = None, octaves: bool = False,
            permute: bool = True, resolution: float = 0.125,
            tab_tuning: Optional[List[int]] = None, physical: bool = True,
            string_physics: bool = True) -> HomographReport:
    """Eligibility + solutions for a set of songs (song 0 = the tab's own song).

    ``anchor``: the instrument's tuning (a MapperConfig); without it only free
    mode runs. ``mode``: which solution ``report.solution`` returns (default
    'anchored' with an anchor, else 'free'). ``instrument``: its strings (default:
    the conventional set for the anchor tuning). ``physical=False`` skips the
    anchored/middle searches (a quick richness/free check); ``string_physics=False``
    costs retunes in bare semitones (no breaking limits). ``tab_tuning``: if song
    0 was read from a tab, the open pitches (high->low) it was decoded in."""
    from .strings import default_instrument

    mode = mode or ("anchored" if anchor is not None else "free")
    if mode != "free" and anchor is None:
        anchor = MapperConfig()
    if anchor is not None:
        anchor = copy.deepcopy(anchor)
        anchor.max_fret = max_fret
        if not anchor_name:
            anchor_name = ",".join(anchor.custom_tuning) if anchor.custom_tuning else anchor.tuning
        if instrument is None and string_physics:
            instrument = default_instrument(anchor.tuning,
                                            GuitarMapper(_quiet(anchor)).open_string_pitches)
    labels = list(labels or [chr(65 + i) for i in range(len(songs))])
    titles = list(titles or [s.title for s in songs])
    event_lists = [[e for t in s.tracks for e in t.events] for s in songs]
    rep = HomographReport(labels=labels, titles=titles,
                          note_counts=[len(evs) for evs in event_lists],
                          onset_counts=[len(onset_groups(evs, resolution)) for evs in event_lists],
                          alignment=align(event_lists, rhythm=rhythm, resolution=resolution,
                                          labels=labels, subdivide=subdivide),
                          mode=mode, max_fret=max_fret, max_strings=max_strings,
                          anchor_name=anchor_name if anchor is not None else None,
                          instrument=instrument if anchor is not None and string_physics else None)
    if not rep.alignment.ok:
        return rep

    rep.slots = pair_slots(rep.alignment.onsets, permute=permute)
    rep.displaced = fold_octaves(rep.slots, transpose) if octaves else [0] * len(songs)
    rep.classes = classes_of(rep.slots)
    rep.richness_mod12 = len({tuple(x % 12 for x in k) for k in rep.classes})

    rep.free, rep.free_needed, rep.free_reason = solve_free(
        rep.slots, max_fret=max_fret, max_strings=max_strings,
        transpose=transpose, max_retune=max_retune)
    if anchor is not None and physical:
        for m in ("anchored", "middle"):
            sol, why = solve_physical(rep.slots, anchor, mode=m, instrument=rep.instrument,
                                      transpose=transpose, transpose_a=transpose_a,
                                      max_retune=max_retune)
            setattr(rep, m, sol)
            setattr(rep, f"{m}_reason", why)
    rep.as_written, rep.as_written_reason = check_as_written(
        rep.slots, tab_tuning=tab_tuning, max_fret=max_fret, transpose=transpose,
        max_retune=max_retune, instrument=rep.instrument)
    for level in ("free", "anchored", "middle", "as_written"):
        sol = getattr(rep, level)
        problems = verify(rep.slots, sol, max_fret) if sol is not None else []
        if not problems:
            continue
        if level == mode:                        # a solver bug; never ship a wrong tab
            raise AssertionError(f"{sol.mode} homograph failed verification: {problems[:3]}")
        # an informational level must not sink the requested one: report, don't crash
        setattr(rep, level, None)
        setattr(rep, f"{level}_reason",
                f"internal check failed (please report): {problems[0]}")
    return rep


def _quiet(cfg: MapperConfig) -> MapperConfig:
    c = copy.deepcopy(cfg)
    c.capo = 0
    return c


def richness(song_a: Song, song_b: Song, *, rhythm: Rhythm = "strict", subdivide: int = 1,
         octaves: bool = False, resolution: float = 0.125) -> Optional[int]:
    """The retuning richness of two songs under the selected alignment/pairing
    (distinct note-for-note intervals), or None if they don't align. Cheap: no tab solved."""
    evs = [[e for t in s.tracks for e in t.events] for s in (song_a, song_b)]
    al = align(evs, rhythm=rhythm, resolution=resolution, subdivide=subdivide)
    if not al.ok:
        return None
    slots = pair_slots(al.onsets)
    if octaves:
        fold_octaves(slots)
    return len(classes_of(slots))


# -- report text ------------------------------------------------------------------------------

def _string_label(names_high_to_low: List[str], s: int) -> str:
    lab = re.sub(r"-?\d+$", "", names_high_to_low[s])
    return lab.lower() if s == 0 else lab            # tab convention: high string lowercase


_STATUS_WORDS = {
    "slack": lambda st: "too slack",
    "tight": lambda st: ("too tight" if st.ratio > 1.45 or st.stress is None
                         else "at risk of snapping"),
    "breaks": lambda st: ("dangerously tight (2x or more its normal tension)"
                          if st.ratio >= 2.0 else "at its breaking point"),
    "impossible": lambda st: "beyond what any steel string can hold at this scale length",
}


def _tuning_table(rep: HomographReport, sol: Solution, indent: str) -> List[str]:
    N, K = sol.num_strings, len(rep.labels)
    inst = sol.instrument
    ref = inst.nominal if inst else sol.opens[0]
    ref_names = [pitch_to_note_name(p) for p in ref]
    w = 17 if inst else 9
    head = f"{indent}string " + ("gauge  " if inst else "") + \
        "".join(f"{lab:<{w + 2}}" for lab in rep.labels)
    lines, notes = [head.rstrip()], []
    for s in range(N):
        row = f"{indent}{s + 1:>2} {_string_label(ref_names, s):<3} " + \
            (f"{str(inst.gauges[s]):<6} " if inst else "")
        if not sol.used[s]:
            lines.append(row + f"{pitch_to_note_name(ref[s]):<4} (unused)")
            continue
        cells = []
        for j in range(K):
            p = sol.opens[j][s]
            d = p - ref[s]
            cell = f"{pitch_to_note_name(p):<4} {('' if d == 0 else f'{d:+d}'):>3}"
            if inst:
                st = inst.assess(s, p)
                cell += f" {st.tension:5.1f}lb" + (" " if st.ok else "!")
                if not st.ok:
                    fix = (f"restring with {st.suggestion[0]} ({st.suggestion[1]:.1f} lb)"
                           if st.suggestion else "no gauge helps at this scale length")
                    stress = ("" if st.stress is None
                              else f", {st.stress * 100:.0f}% of breaking stress")
                    notes.append(f"{indent}! string {s + 1} for {rep.labels[j]}: "
                                 f"{pitch_to_note_name(p)} is {_STATUS_WORDS[st.status](st)} "
                                 f"({st.tension:.1f} lb = {st.ratio * 100:.0f}% of normal"
                                 f"{stress}) - {fix}")
            cells.append(f"{cell:<{w}}")
        lines.append(row + "  ".join(cells).rstrip())
    return lines + notes


def _shift_lines(rep: HomographReport, sol: Solution, indent: str) -> List[str]:
    out = []
    for j in range(len(rep.labels)):
        if sol.shifts[j]:
            why = ("moved so the tab fits the instrument" if j == 0 else
                   "chosen to minimize retuning; --homograph-transpose keep holds it")
            out.append(f"{indent}{rep.labels[j]} sounds {fmt_interval(sol.shifts[j])} "
                       f"semitones from its input key ({why})")
    return out


def format_report(rep: HomographReport) -> str:
    L: List[str] = []
    K = len(rep.labels)
    ind = "             "
    w = max(len(t) for t in rep.titles)
    L.append(f"Tab homograph check: {K} songs")
    for j in range(K):
        L.append(f"  {rep.labels[j]}  {rep.titles[j]:<{w}}  "
                 f"({rep.note_counts[j]} notes, {rep.onset_counts[j]} onsets)")
    al = rep.alignment
    if not al.ok:
        L.append(f"Alignment  NOT ALIGNED - {al.reason}")
        L.append("           A shared tab fixes the note count and chord shape at every "
                 "onset; trim the songs to a common passage.")
        return "\n".join(L)
    rhythm = {"identical": "identical rhythm",
              "proportional": f"same rhythm at another note value ({al.detail})",
              "loose": f"rhythm within tolerance ({al.detail})",
              "sequence-only": "pitch order only - rhythms differ"}[al.rhythm]
    if al.edits:
        rhythm += f" after {len(al.edits)} re-rhythm edit{'s' if len(al.edits) > 1 else ''}"
    if al.rhythm in ("loose", "sequence-only") or al.edits:
        rhythm += f"; the tab carries {rep.labels[0]}'s rhythm"
    L.append(f"Alignment  OK - {len(al.onsets)} tab onsets, {len(rep.slots)} notes, {rhythm}")
    for e in al.edits:
        L.append(f"Re-rhythm  {e}")
    if any(rep.displaced):
        L.append("Octaves    displaced " + ", ".join(
            f"{rep.displaced[j]} note(s) of {rep.labels[j]}" for j in range(1, K)
            if rep.displaced[j]) + " (--homograph-octaves)")

    diffs = [fmt_key(s.key) for s in rep.slots]
    shown = " ".join(diffs[:32]) + (" ..." if len(diffs) > 32 else "")
    what = f"{rep.labels[1]}-{rep.labels[0]}" if K == 2 else \
        "(" + ",".join(f"{lab}-{rep.labels[0]}" for lab in rep.labels[1:]) + ")"
    L.append(f"Intervals  {what} per note: {shown}")
    cls = ", ".join(fmt_key(k) for k in rep.classes)
    L.append(f"Richness   {rep.richness} interval class{'es' if rep.richness != 1 else ''} "
             f"{{{cls}}} -> a shared tab needs >= {rep.richness} strings")
    if rep.richness_mod12 < rep.richness and not any(rep.displaced):
        L.append(f"           ({rep.richness_mod12} if octave displacement is allowed: "
                 "--homograph-octaves)")
    if rep.richness == 1:
        only = next(iter(rep.classes))
        L.append("           Trivial: " + ("the songs are identical." if not any(only) else
                 "the songs are transpositions of each other - a capo, not a homograph."))

    def section(tag: str, sol: Optional[Solution], reason: str, headline: str, full: bool):
        if sol is None:
            L.append(f"{tag:<10} NOT ELIGIBLE - {reason}")
            return
        L.append(f"{tag:<10} ELIGIBLE - {headline}")
        if full:
            L.extend(_tuning_table(rep, sol, ind))
            L.extend(_shift_lines(rep, sol, ind))
            if sol.note:
                L.append(f"{ind}({sol.note})")
        else:
            rg = sol.regauges()
            phys = "" if sol.instrument is None else (
                "every string within safe tension; " if not rg else
                f"{rg} string{'s' if rg > 1 else ''} outside safe tension; ")
            L.append(f"{ind}({phys}--homograph-mode {tag.lower()} for its tab)")

    free_head = (f"{rep.free_needed} strings, any tunings (max {rep.max_strings}, "
                 f"{rep.max_fret} frets)") if rep.free else ""
    section("Free", rep.free, rep.free_reason, free_head, rep.mode == "free")
    if rep.anchor_name:
        inst = rep.instrument.describe() if rep.instrument else ""
        others = ", ".join(rep.labels[1:])
        section("Anchored", rep.anchored, rep.anchored_reason,
                f"an ordinary {rep.anchor_name} tab of {rep.labels[0]}, retuned, plays "
                f"{others} ({inst}):", rep.mode == "anchored")
        section("Middle", rep.middle, rep.middle_reason,
                f"every song a retune of one {rep.anchor_name}-strung guitar ({inst}); the "
                f"tab is in tuning {rep.labels[0]}:", rep.mode == "middle")
    if rep.as_written is not None:
        L.append(f"As written ELIGIBLE - {rep.labels[0]}'s own tab, fingering untouched, "
                 "retunes into the others")
        L.extend(_tuning_table(rep, rep.as_written, ind))
        L.extend(_shift_lines(rep, rep.as_written, ind))
    elif rep.as_written_reason and "not a tab" not in rep.as_written_reason:
        L.append(f"As written NOT ELIGIBLE - {rep.as_written_reason}")
    if rep.solution is not None:
        L.append("Verified   decoding the tab in each tuning reproduces every note "
                 "of every song")
    return "\n".join(L)


# -- inline melodies -------------------------------------------------------------------------

_NOTE = r"[A-Ga-g][#b]?-?\d+"
_TOKEN = re.compile(rf"^(?P<notes>{_NOTE}(?:\+{_NOTE})*|[rRzZ])(?::(?P<dur>\d+(?:\.\d+)?(?:/\d+)?))?$")


def _parse_duration(s: Optional[str]) -> float:
    if not s:
        return 1.0
    if "/" in s:
        num, den = s.split("/")
        v = float(num) / float(den) if float(den) else 0.0
    else:
        v = float(s)
    if v <= 0:                  # a zero length would silently fuse notes into a chord
        raise ValueError(f"bad duration {s!r} (must be > 0 beats)")
    return v


def window(song: Song, start: int, end: int, resolution: float = 0.125) -> Song:
    """Onsets ``start``..``end`` (1-based, inclusive) of a song, re-based to 0."""
    groups = onset_groups([e for t in song.tracks for e in t.events], resolution)
    if not 1 <= start <= end <= len(groups):
        raise ValueError(f"onset window {start}-{end} is outside 1-{len(groups)}")
    keep = groups[start - 1:end]
    t0 = keep[0][0].time
    events = [copy.copy(e) for g in keep for e in g]
    for e in events:
        e.time -= t0
    return Song(tracks=[Track(events=events)], tempo=song.tempo,
                time_signature=song.time_signature, title=song.title)


def parse_inline(spec: str, title: str = "inline") -> Song:
    """A melody written inline: notes with octave, ``+`` for chords, ``:dur`` in
    beats (default 1), ``r`` for a rest. e.g. ``"C4 C4 G4 G4 A4 A4 G4:2"``,
    ``"C3+E3+G3:2 r:1 D4:1/2"``. Separated by spaces and/or commas."""
    t, events = 0.0, []
    for tok in re.split(r"[,\s]+", spec.strip()):
        if not tok:
            continue
        m = _TOKEN.match(tok)
        if not m:
            raise ValueError(f"bad note token {tok!r} (use e.g. C4, F#3:2, C3+E3+G3, r:1)")
        dur = _parse_duration(m.group("dur"))
        if m.group("notes")[0] not in "rRzZ":
            for n in m.group("notes").split("+"):
                events.append(MusicalEvent(t, note_name_to_pitch(n), dur, 100))
        t += dur
    if not events:
        raise ValueError("no notes in the melody")
    return Song(tracks=[Track(events=events)], title=title)
