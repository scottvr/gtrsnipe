"""Published tabs, as written: can a real fingering be retuned into another song?
(backlog R05)

R04 let the solver choose which notes share a string. Here a tab's own
fingering is fixed: every note the tab puts on one string must move by the same
interval, so song B, note for note, must satisfy

    b_t - a_t = constant for all t on the same string        (per-string constancy)

-- much stricter than "richness <= 6", because the tab, not the solver, decides
which notes are grouped.

The scan slides windows over a tab, finds corpus passages with the same number
of evenly spaced notes (ASCII tab carries only rough timing: the column spacing
wobbles at barlines and two-digit frets, so the tab is treated as steady notes,
which suits Bach's Prelude and Asturias), and tests every one. For comparison it
also counts the candidates that would share *some* tab (richness <= 6). Hits
that are plain transpositions of the tab's own passage (the piece itself, found
in a corpus) are counted apart. The best hits go through the homograph solver's
as-written check, which adds string physics.
"""
from __future__ import annotations

import heapq
import itertools
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

from .corpus import Melody
from .scan import DISTINCT_C1, UNRELATED_CONTOUR, _modal_share, distinct_pairs, mechanical

STANDARD_OPEN = [64, 59, 55, 50, 45, 40]      # high -> low, as gtrsnipe indexes strings


@dataclass
class TabLine:
    """A tab read as single notes in order (chord onsets split the line)."""
    name: str
    pitches: np.ndarray
    strings: np.ndarray
    frets: np.ndarray
    chord_at: np.ndarray            # True where the onset has more than one note
    open_pitches: List[int]
    events: list                    # the parsed MusicalEvents, for the solver


def read_tab(path: str, name: Optional[str] = None) -> TabLine:
    from ..formats.tab.parser import AsciiTabParser
    with open(path, encoding="utf-8") as f:
        text = f.read()
    opens = AsciiTabParser.header_tuning(text) or STANDARD_OPEN
    song = AsciiTabParser.parse(text, open_string_pitches=opens)
    evs = sorted((e for t in song.tracks for e in t.events), key=lambda e: (e.time, e.pitch))
    by_onset: Dict[float, list] = defaultdict(list)
    for e in evs:
        by_onset[round(e.time, 6)].append(e)
    line, chord = [], []
    for t in sorted(by_onset):
        g = by_onset[t]
        line.append(max(g, key=lambda e: e.pitch))
        chord.append(len(g) > 1)
    return TabLine(name or path, np.array([e.pitch for e in line]),
                   np.array([e.string for e in line]), np.array([e.fret for e in line]),
                   np.array(chord), list(opens), line)


def even_windows(melodies: Sequence[Melody], L: int) -> Tuple[np.ndarray, np.ndarray]:
    """Every L-note window of evenly spaced notes (equal inter-onset intervals) in
    the corpus: (pitch matrix, N x 2 array of (melody index, start))."""
    rows, refs = [], []
    for mi, m in enumerate(melodies):
        n = len(m)
        if n < L:
            continue
        on = np.asarray(m.onsets)
        same = np.diff(on, 2) == 0 if n >= 3 else np.zeros(0, bool)   # ioi[i+1] == ioi[i]
        # window [s, s+L) is even iff same[s .. s+L-3] are all True
        need = L - 2
        if need <= 0:
            starts = np.arange(n - L + 1)
        else:
            c = np.concatenate([[0], np.cumsum(~same)])
            starts = np.flatnonzero(c[need:] - c[:-need] == 0)
            starts = starts[starts <= n - L]
        if not len(starts):
            continue
        p = np.asarray(m.pitches, dtype=np.int16)
        rows.append(np.stack([p[s:s + L] for s in starts]))
        refs.append(np.column_stack([np.full(len(starts), mi), starts]))
    P = np.concatenate(rows) if rows else np.zeros((0, L), np.int16)
    R = np.concatenate(refs).astype(np.int32) if refs else np.zeros((0, 2), np.int32)
    return P, R


@dataclass
class Hit:
    tab: str
    tab_span: Tuple[int, int]        # 1-based inclusive note span of the tab
    ref: str                         # corpus:id@start-end
    title: str
    richness: int
    strings: int
    c1: float
    contour: float
    pairs: int
    mechanical: bool
    offsets: List[int]
    solved: Optional[dict] = None


@dataclass
class LengthResult:
    windows: int = 0                 # tab windows tested (no chords)
    candidates: int = 0              # window x corpus-passage pairs compared
    free: int = 0                    # ... that would share *some* tab (2 <= richness <= 6)
    as_written: int = 0              # ... that the tab's own fingering plays (not transpositions)
    trivial: int = 0                 # ... with no more distinct pitch pairs than strings used:
                                     #     every string maps one pitch to one pitch, so the frets
                                     #     carry nothing but which string to pluck
    itself: int = 0                  # ... plain transpositions of the tab's passage
    unrelated: int = 0               # non-trivial as-written hits that sound unrelated (R04)
    tab_windows_with_hit: int = 0
    itself_found: List[str] = field(default_factory=list)   # a sample of where the passage recurs


def scan_tab(tab: TabLine, melodies: Sequence[Melody], lengths: Sequence[int], *,
             keep: int = 50, max_richness: int = 6,
             window_cache: Optional[dict] = None) -> Tuple[Dict[int, LengthResult], List[Hit]]:
    """``window_cache``: a dict reused across tabs, so each length's corpus
    windows are collected once."""
    results: Dict[int, LengthResult] = {}
    heap: list = []                     # the best hits: (key, tiebreak, Hit), bounded
    tiebreak = itertools.count()
    cap = max(keep * 40, 2000)
    for L in lengths:
        res = results.setdefault(L, LengthResult())
        if len(tab.pitches) < L:
            continue
        if window_cache is not None and L in window_cache:
            P, refs = window_cache[L]
        else:
            P, refs = even_windows(melodies, L)
            P = P.astype(np.int32)
            if window_cache is not None:
                window_cache[L] = (P, refs)
        if not len(P):
            continue
        mech_b = None
        for s in range(len(tab.pitches) - L + 1):
            if tab.chord_at[s:s + L].any():
                continue
            res.windows += 1
            a = tab.pitches[s:s + L].astype(np.int32)
            st = tab.strings[s:s + L]
            D = P - a
            res.candidates += len(D)
            S = np.sort(D, axis=1)
            r = 1 + (S[:, 1:] != S[:, :-1]).sum(1)
            res.free += int(((r >= 2) & (r <= max_richness)).sum())
            ok = np.ones(len(D), bool)
            for u in np.unique(st):
                pos = np.flatnonzero(st == u)
                ok &= (D[:, pos] == D[:, pos[:1]]).all(1)
            itself = ok & (r == 1)
            res.itself += int(itself.sum())
            for j in np.flatnonzero(itself):
                if len(res.itself_found) >= 12:
                    break
                ref = melodies[int(refs[j, 0])].ref
                if ref not in res.itself_found:
                    res.itself_found.append(ref)
            ok &= r >= 2
            n_ok = int(ok.sum())
            if not n_ok:
                continue
            res.as_written += n_ok
            res.tab_windows_with_hit += 1
            idx = np.flatnonzero(ok)
            c1 = _modal_share(D[idx])
            contour = (np.sign(np.diff(P[idx], axis=1)) == np.sign(np.diff(a))).mean(1)
            npairs = distinct_pairs(np.broadcast_to(a, (len(idx), L)), P[idx])
            n_str = len(np.unique(st))
            res.trivial += int((npairs <= n_str).sum())
            for j, cj, co, npj in zip(idx, c1, contour, npairs):
                mi, start = int(refs[j, 0]), int(refs[j, 1])
                m = melodies[mi]
                trivial = npj <= n_str
                mech = mechanical(P[j].tolist())
                unrelated = (cj <= DISTINCT_C1 and co <= UNRELATED_CONTOUR and not mech
                             and not trivial)
                res.unrelated += int(unrelated)
                key = (int(unrelated), int(not trivial), int(npj), L, -float(cj))
                if len(heap) >= cap and key <= heap[0][0]:
                    continue
                hit = Hit(tab.name, (s + 1, s + L), f"{m.ref}@{start + 1}-{start + L}",
                          m.title, int(r[j]), int(len(np.unique(st))), float(cj),
                          round(float(co), 3), int(npj), bool(mech), (P[j] - a).tolist())
                item = (key, next(tiebreak), hit)
                if len(heap) < cap:
                    heapq.heappush(heap, item)
                else:
                    heapq.heapreplace(heap, item)
    # best first: sounding unrelated, non-trivial, most distinct pitch pairs, longest, least similar
    hits = [h for _, _, h in sorted(heap, reverse=True)]
    seen, top = set(), []
    for h in hits:                      # one per (tab span, corpus melody)
        k = (h.tab_span, h.ref.rsplit("@", 1)[0])
        if k in seen:
            continue
        seen.add(k)
        top.append(h)
        if len(top) >= keep:
            break
    return results, top


def solve_hit(tab: TabLine, h: Hit, by_ref: Dict[str, Melody]) -> dict:
    """The homograph solver's as-written check (with string physics) on a hit."""
    import copy
    from ..core.config import MapperConfig
    from ..core.types import Song, Track
    from ..guitar.homograph import analyze
    s, e = h.tab_span
    evs = [copy.copy(ev) for ev in tab.events[s - 1:e]]
    t0 = evs[0].time
    step = (evs[-1].time - t0) / max(1, len(evs) - 1)
    for k, ev in enumerate(evs):                 # steady notes, as the scan assumed
        ev.time = k * step
        ev.duration = step
    base, span = h.ref.rsplit("@", 1)
    b0, b1 = (int(x) for x in span.split("-"))
    mb = by_ref[base].slice(b0 - 1, b1)
    songB = mb.to_song()
    bev = sorted(songB.tracks[0].events, key=lambda x: x.time)
    for k, ev in enumerate(bev):
        ev.time = k * step
        ev.duration = step
    songA = Song(tracks=[Track(events=evs)], title=tab.name)
    rep = analyze([songA, Song(tracks=[Track(events=bev)])], anchor=MapperConfig(),
                  anchor_name="STANDARD", tab_tuning=tab.open_pitches)
    aw = rep.as_written
    out = {"aligned": rep.alignment.ok, "as_written": aw is not None,
           "reason": rep.as_written_reason}
    if aw is not None:
        out["tuning_b"] = aw.tuning_names(1)
        out["retunes"] = aw.retunes(1)
        out["regauges"] = aw.regauges()
    return out
