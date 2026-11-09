"""Score a fingering bar by bar with the mapper's own objective (``gtrsnipe-research score``).

A tab's fingering, as written, is walked as a path through the mapper's trellis: each onset
group becomes the fingering the tab gives it, and every step is scored with
``GuitarMapper.step_features`` x ``step_weights``, the arithmetic the Viterbi mapper itself
uses. Summing the steps of a bar gives that bar's score inside the whole path, so a passage
can be inspected without cutting it out of the piece (the first step into a bar keeps its
real predecessor). Beside the tab's own path, the same notes are fingered by the mapper
under the same configuration, so where an editor and gtrsnipe differ the difference shows
up as a feature vector, and the weight change that would make a bar tie is read off it.

Bars are numbered from 1 at the first bar written, as the tab generator's ``--number-bars``
and the rhythm legend number them; a pickup is bar 1.
"""
from __future__ import annotations

import copy
import logging
from dataclasses import dataclass, field
from itertools import groupby
from typing import Dict, List, Optional, Sequence, Tuple

from ..core.config import MapperConfig
from ..core.types import FretPosition, MusicalEvent, Song, Tuning
from ..guitar.mapper import Fingering, GuitarMapper

# feature -> (MapperConfig field, sign of the weight it sets). The weight for a feature is
# sign x field; structural features (span_break, diagonal_break) have no knob to turn.
KNOB_OF: Dict[str, Tuple[str, float]] = {
    "span": ("fret_span_penalty", -1.0),
    "in_sweet_spot": ("sweet_spot_bonus", 1.0),
    "over_sweet_spot": ("high_fret_penalty", -1.0),
    "barre": ("barre_bonus", 1.0),
    "move": ("movement_penalty", -1.0),
    "string_switch": ("string_switch_penalty", -1.0),
    "ringing": ("let_ring_bonus", 1.0),
    "fretted_open": ("fretted_open_penalty", -1.0),
}


@dataclass
class Step:
    """One onset group of a path: its fingering, feature vector and score."""
    index: int
    time: float                 # beats
    bar: int                    # 1-based
    beat: float                 # beat within the bar, 0-based
    fingering: Fingering
    features: Tuple[float, ...]
    score: float
    gap: Optional[float]        # seconds the hand had for the move (M08), None when time-blind


@dataclass
class PathScore:
    label: str
    steps: List[Step]
    weights: Tuple[float, ...]
    names: Tuple[str, ...] = GuitarMapper.FEATURE_NAMES
    total: float = 0.0
    last_bar: int = 0

    def in_bars(self, lo: int, hi: Optional[int]) -> List[Step]:
        return [s for s in self.steps if lo <= s.bar and (hi is None or s.bar <= hi)]

    def bar_totals(self) -> Dict[int, float]:
        out: Dict[int, float] = {}
        for s in self.steps:
            out[s.bar] = out.get(s.bar, 0.0) + s.score
        return out

    def features_in(self, lo: int, hi: Optional[int]) -> Tuple[float, ...]:
        acc = [0.0] * len(self.names)
        for s in self.in_bars(lo, hi):
            for i, f in enumerate(s.features):
                acc[i] += f
        return tuple(acc)

    def score_in(self, lo: int, hi: Optional[int]) -> float:
        return sum(s.score for s in self.in_bars(lo, hi))

    def to_dict(self) -> dict:
        return {"label": self.label, "total": self.total, "weights": list(self.weights),
                "features": list(self.names),
                "steps": [{"bar": s.bar, "beat": s.beat, "time": s.time,
                           "fingering": [[p.string, p.fret] for p in s.fingering],
                           "features": list(s.features), "score": s.score, "gap": s.gap}
                          for s in self.steps]}


def bar_length(song: Song) -> float:
    """Beats (quarter notes) per bar from the song's time signature."""
    try:
        num, den = map(int, song.time_signature.split("/"))
    except (ValueError, AttributeError):
        return 4.0
    return num * 4.0 / den if den else float(num)


def parse_bars(spec: Optional[str]) -> Tuple[int, Optional[int]]:
    """'23' -> (23, 23); '23-25' -> (23, 25); '23-' -> (23, None); None -> (1, None)."""
    if not spec:
        return 1, None
    text = spec.strip()
    if "-" in text:
        a, _, b = text.partition("-")
        lo = int(a) if a.strip() else 1
        hi = int(b) if b.strip() else None
    else:
        lo = hi = int(text)
    if lo < 1 or (hi is not None and hi < lo):
        raise ValueError(f"--bars wants START[-END] with 1 <= START <= END, got {spec!r}")
    return lo, hi


def _configured(cfg: Optional[MapperConfig], song: Song) -> MapperConfig:
    out = copy.deepcopy(cfg) if cfg else MapperConfig()
    out.tempo_bpm = song.tempo if song.tempo and song.tempo > 0 else 120.0
    return out


def fingered(song: Song) -> List[MusicalEvent]:
    """The first track's events that carry a string and a fret (a tab's own fingering)."""
    if not song.tracks:
        return []
    return [e for e in song.tracks[0].events if e.string is not None and e.fret is not None]


def time_groups(events: Sequence[MusicalEvent], resolution: float) -> List[List[MusicalEvent]]:
    """Onset groups exactly as the mapper forms them (quantized time, stable order)."""
    def q(beat):
        return round(beat / resolution) * resolution
    ordered = sorted(events, key=lambda e: e.time)
    return [list(g) for _, g in groupby(ordered, key=lambda e: q(e.time))]


def score_path(song: Song, cfg: Optional[MapperConfig] = None, label: str = "as written",
               events: Optional[Sequence[MusicalEvent]] = None) -> PathScore:
    """Walk ``events`` (default: the song's own fingering) as a path and score every step
    with the mapper's features x weights under ``cfg``. The running sum is accumulated in
    time order, as the Viterbi DP accumulates it, so a mapped path's total equals the
    mapper's ``last_path_score``."""
    mcfg = _configured(cfg, song)
    mapper = GuitarMapper(mcfg)
    weights = mapper.step_weights()
    evs = list(events) if events is not None else fingered(song)
    groups = time_groups(evs, mcfg.quantization_resolution)
    blen = bar_length(song)
    steps: List[Step] = []
    total = 0.0
    prev: Optional[Fingering] = None
    prev_prev: Optional[Fingering] = None
    prev_group: Optional[List[MusicalEvent]] = None
    for i, g in enumerate(groups):
        fing: Fingering = tuple(sorted((FretPosition(e.string, e.fret) for e in g),
                                       key=lambda p: (p.string, p.fret)))
        gap = mapper._gap_seconds(prev_group, g)
        feats = mapper.step_features(fing, prev, prev_prev, gap)
        s = mapper.score_features(feats, weights)
        total += s
        t = g[0].time
        steps.append(Step(i, t, int(t // blen) + 1, t - int(t // blen) * blen, fing, feats, s, gap))
        prev_prev, prev, prev_group = prev, fing, g
    return PathScore(label, steps, weights, GuitarMapper.FEATURE_NAMES, total,
                     steps[-1].bar if steps else 0)


def mapper_path(song: Song, cfg: Optional[MapperConfig] = None, label: str = "gtrsnipe") -> PathScore:
    """The mapper's own fingering of the song's notes under ``cfg``, scored the same way.
    The returned path's ``total`` is the DP's path score recomputed step by step."""
    mcfg = _configured(cfg, song)
    log = logging.getLogger(GuitarMapper.__module__)
    saved = log.level
    log.setLevel(logging.ERROR)
    try:
        notes = [copy.copy(e) for e in (song.tracks[0].events if song.tracks else [])]
        for e in notes:
            e.string = e.fret = None
        mapped = GuitarMapper(copy.deepcopy(mcfg)).map_events_to_fretboard(notes, no_articulations=True)
    finally:
        log.setLevel(saved)
    return score_path(song, mcfg, label, events=mapped)


# -- the report -------------------------------------------------------------------

def string_names(cfg: MapperConfig) -> List[str]:
    """String names by mapper index (0 = highest), as the tab staff labels them."""
    if getattr(cfg, "custom_tuning", None):
        notes = list(reversed(cfg.custom_tuning))
    else:
        try:
            notes = list(reversed(Tuning[cfg.tuning].value))
        except KeyError:
            notes = list(reversed(Tuning.STANDARD.value))
    bass = cfg.tuning.startswith("BASS_")
    return [(n[0].upper() if bass or i else n[0].lower()) for i, n in enumerate(notes)]


def fingering_text(f: Fingering, names: Sequence[str]) -> str:
    """'B:0 G:4' for a fingering, lowest string first."""
    def name(s):
        return names[s] if s < len(names) else f"s{s + 1}"
    return " ".join(f"{name(p.string)}:{p.fret}" for p in sorted(f, key=lambda p: -p.string))


def _terms(step: Step, names: Sequence[str], weights: Sequence[float]) -> str:
    parts = []
    for n, f, w in zip(names, step.features, weights):
        if f and w:
            parts.append(f"{n} {f:g}x{w:g}")
    return "  ".join(parts) if parts else "(nothing scored)"


def format_report(paths: Sequence[PathScore], cfg: MapperConfig, lo: int = 1, hi: Optional[int] = None,
                  detail: bool = True) -> str:
    """Per-bar totals for every path (the range, then the whole piece), the per-step terms
    inside the range, and, for the first two paths, the feature difference over the range
    and the single-knob changes that would make them tie there."""
    if not paths:
        return "(no paths)"
    names = string_names(cfg)
    last = max(p.last_bar for p in paths)
    top = last if hi is None else min(hi, last)
    out: List[str] = []
    labels = [p.label for p in paths]
    width = max(12, *(len(l) for l in labels))
    head = f"{'bar':>5} " + " ".join(f"{l:>{width}}" for l in labels)
    if len(paths) > 1:
        head += f" {'delta':>9}"
    out.append(head)
    totals = [p.bar_totals() for p in paths]
    for b in range(lo, top + 1):
        row = f"{b:>5} " + " ".join(f"{t.get(b, 0.0):>{width}.1f}" for t in totals)
        if len(paths) > 1:
            row += f" {totals[0].get(b, 0.0) - totals[1].get(b, 0.0):>+9.1f}"
        out.append(row)
    span = "all bars" if (lo, top) == (1, last) else (f"bar {lo}" if lo == top else f"bars {lo}-{top}")
    row = f"{span:>5} " + " ".join(f"{p.score_in(lo, hi):>{width}.1f}" for p in paths)
    if len(paths) > 1:
        row += f" {paths[0].score_in(lo, hi) - paths[1].score_in(lo, hi):>+9.1f}"
    out.append(row)
    if (lo, top) != (1, last):
        row = f"{'piece':>5} " + " ".join(f"{p.total:>{width}.1f}" for p in paths)
        if len(paths) > 1:
            row += f" {paths[0].total - paths[1].total:>+9.1f}"
        out.append(row)
    out.append("(higher is better: penalties are negative; delta = first path minus second)")

    if detail:
        for p in paths:
            steps = p.in_bars(lo, hi)
            if not steps:
                continue
            out.append("")
            out.append(f"== {p.label}: {len(steps)} onset(s) in {span}")
            for s in steps:
                gap = f"  gap {s.gap:.2f}s" if s.gap is not None else ""
                out.append(f"  bar {s.bar:>3} beat {s.beat:>5.2f}  {fingering_text(s.fingering, names):<24} "
                           f"{s.score:>8.1f}  {_terms(s, p.names, p.weights)}{gap}")

    if len(paths) > 1:
        a, b = paths[0], paths[1]
        fa, fb = a.features_in(lo, hi), b.features_in(lo, hi)
        margin = a.score_in(lo, hi) - b.score_in(lo, hi)
        out.append("")
        out.append(f"== {a.label} minus {b.label} over {span}: {margin:+.1f}")
        diffs = [(n, x - y, w) for n, x, y, w in zip(a.names, fa, fb, a.weights) if abs(x - y) > 1e-9]
        if not diffs:
            out.append("  the two paths have the same features there")
        for n, d, w in diffs:
            line = f"  {n:<16} {d:>+8g} x {w:>7g} = {d * w:>+8.1f}"
            knob = KNOB_OF.get(n)
            if knob and abs(margin) > 1e-9:
                field_name, sign = knob
                now = getattr(cfg, field_name)
                tie = sign * (w - margin / d)          # the knob value at which the range ties
                if tie < 0:
                    line += f"   (no {field_name} >= 0 ties it)"
                elif n == "fretted_open" and not cfg.prefer_open:
                    line += f"   (tie: --prefer-open with {field_name} {tie:g})"
                else:
                    line += f"   (tie: {field_name} {now:g} -> {tie:g})"
            elif knob is None:
                line += "   (structural: no knob)"
            out.append(line)
        if diffs and abs(margin) > 1e-9:
            out.append("  a tie moves that one knob alone, every other weight held; it is a lower bound on the "
                       "change, since the mapper re-optimises the whole piece under the new weight")
    return "\n".join(out)
