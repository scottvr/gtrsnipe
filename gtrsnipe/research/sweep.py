"""The scoring-weights sweep (backlog M01, step 5): which knobs are wired to anything?

Vary one mapper knob at a time over a ladder of values, finger each song under each
setting, and count the *distinct* tabs. A knob that never changes a tab on any input at the
defaults is idle there (its case may not arise: the sweet-spot bonus is the window's
only lower edge, so it needs one), which is why some knobs are also swept in the
context they were designed for (the ``@`` entries); one that changes a tab only past
a threshold is a priority, not a trade-off; one that changes it smoothly is a genuine
exchange rate. The sweep also
checks two things a weight table can't show: that scaling every weight together
leaves every tab unchanged (only ratios matter), and whether a fingering the scorer
calls unplayable (chord span past ``unplayable_fret_span``) is ever chosen anyway:
that is the no-fit case, where no fingering of a chord fits the hand and the mapper
takes the least bad one and says so.

Inputs are anything ``gtrsnipe-research`` reads, plus the built-in probe pieces:
short constructed passages that exercise one scorer question each (an open-string
pedal, a sus shape slid up the neck with its open strings kept, a run inside one
position, an octave leap, a wide chord). They are not music; they are unit tests a
guitarist can read.
"""
from __future__ import annotations

import copy
import os
import logging
from dataclasses import dataclass, field, fields
from typing import Dict, List, Optional, Sequence, Tuple

from ..core.config import MapperConfig
from ..core.types import MusicalEvent, Song, Track
from ..guitar.mapper import GuitarMapper

logger = logging.getLogger(__name__)

Signature = Tuple[Tuple[int, int], ...]        # (string, fret) per note, in (time, pitch) order


# -- knobs ------------------------------------------------------------------------

@dataclass(frozen=True)
class Knob:
    name: str                        # the MapperConfig field
    kind: str                        # "weight" (float), "int", "flag", "choice"
    default: object
    ladder: Tuple[object, ...]       # values tried, default included
    needs: Dict[str, object] = field(default_factory=dict)   # the context it is swept in
    note: str = ""
    alias: str = ""                  # key in KNOBS when the same field is swept in a context

    @property
    def key(self) -> str:
        return self.alias or self.name

    def settings(self, value) -> Dict[str, object]:
        out = dict(self.needs)
        out[self.name] = value
        return out


_SCALE = (0, 0.125, 0.25, 0.5, 1, 2, 4, 8, 16)
_ABS = (0, 1, 3, 10, 30, 100, 300, 1000, 3000)


def _weight(name, default, needs=None, note="", alias=""):
    ladder = tuple(default * s for s in _SCALE) if default else _ABS
    return Knob(name, "weight", default, ladder, needs or {}, note, alias)


KNOBS: Dict[str, Knob] = {k.key: k for k in [
    _weight("movement_penalty", 3.0, note="per fret the average fret moves between fingerings"),
    _weight("string_switch_penalty", 5.0,
            note="per string entering or leaving the set used (a single-note switch counts 2)"),
    _weight("fret_span_penalty", 100.0, note="per fret of span inside a chord"),
    _weight("high_fret_penalty", 5.0, note="per fret the average sits above the sweet spot"),
    _weight("low_string_high_fret_multiplier", 10.0,
            note="times the high-fret penalty when a low string is used"),
    _weight("sweet_spot_bonus", 0.5, note="per fingering whose average fret is in the window"),
    _weight("fretted_open_penalty", 20.0, needs={"prefer_open": True},
            note="per fretted note whose pitch exists as an open string (--prefer-open)"),
    _weight("barre_bonus", 0.0, note="per extra note on the chord's commonest fret"),
    _weight("barre_penalty", 0.0, note="the same count, subtracted; only bonus-penalty matters"),
    _weight("let_ring_bonus", 0.0, note="per string of the previous fingering left free"),
    Knob("unplayable_fret_span", "int", 4, (2, 3, 4, 5, 6, 8), note="chord span past which a fingering returns -1000"),
    Knob("sweet_spot_low", "int", 0, (0, 2, 5, 7, 9, 12)),
    Knob("sweet_spot_high", "int", 12, (5, 7, 9, 12, 15, 17, 24)),
    Knob("prefer_open", "flag", False, (False, True)),
    Knob("ignore_open", "flag", False, (False, True), note="open strings leave the chord-span check"),
    Knob("diagonal_span_penalty", "flag", False, (False, True),
         note="-1000 when the span across consecutive fingerings exceeds the limit"),
    Knob("optimizer", "choice", "viterbi", ("viterbi", "greedy"), note="M02: the legacy mapper"),
    # The same knobs in the context they were designed for. A knob can be idle at the
    # defaults because its case never arises there, not because it does nothing:
    # the sweet-spot bonus is the window's only lower edge, so it needs one; the
    # high-fret penalty needs a high edge the piece actually crosses.
    _weight("sweet_spot_bonus", 0.5, needs={"sweet_spot_low": 4}, alias="sweet_spot_bonus@low4",
            note="the bonus with a lower edge (the Asturias steps used 4)"),
    _weight("high_fret_penalty", 5.0, needs={"sweet_spot_high": 7}, alias="high_fret_penalty@high7",
            note="the penalty with a high edge at the 7th fret"),
    _weight("low_string_high_fret_multiplier", 10.0, needs={"sweet_spot_high": 7},
            alias="low_string_high_fret_multiplier@high7"),
    _weight("barre_bonus", 0.0, needs={"barre_penalty": 10.0}, alias="barre_bonus@penalty10",
            note="the bonus against a standing penalty of 10"),
]}

WEIGHT_NAMES = sorted({k.name for k in KNOBS.values() if k.kind == "weight"})


# -- one run ----------------------------------------------------------------------

JUMP_FRETS = 5.0                     # a change of average fret this big counts as a big jump


@dataclass
class Run:
    signature: Signature
    score: Optional[float]           # path score summed over tracks, under either optimizer (same objective)
    notes: int
    placed: int
    travel: float                    # mean |change of average fret| between fingerings
    switches: int                    # string-set changes, counted as the scorer counts them
    max_fret: int
    max_span: int                    # widest chord span chosen (fretted and open, as scored)
    open_share: float
    unplayable_chosen: int           # chords chosen with span > unplayable_fret_span
    jumps: int = 0                   # position changes of JUMP_FRETS frets or more

    def metrics(self) -> dict:
        d = vars(self).copy()
        d.pop("signature")
        return d


def _groups(events: Sequence[MusicalEvent], resolution: float = 0.0) -> List[List[MusicalEvent]]:
    """Events grouped the way the mapper groups them: by time quantized to ``resolution``
    (the config's ``quantization_resolution``; 0 means exact time)."""
    def q(t: float) -> float:
        return round(t / resolution) * resolution if resolution else t
    out: List[List[MusicalEvent]] = []
    for e in sorted(events, key=lambda e: (q(e.time), e.pitch)):
        if out and abs(q(out[-1][0].time) - q(e.time)) < 1e-9:
            out[-1].append(e)
        else:
            out.append([e])
    return out


def finger(song: Song, cfg: MapperConfig) -> Run:
    """Finger every track of ``song`` under ``cfg`` and summarize what was chosen."""
    mapper_log = logging.getLogger(GuitarMapper.__module__)
    saved = mapper_log.level
    mapper_log.setLevel(logging.ERROR)
    sig: List[Tuple[int, int]] = []
    score, have_score = 0.0, True
    notes = placed = switches = max_fret = max_span = unplayable = jumps = 0
    travel_sum, travel_n, opens = 0.0, 0, 0
    try:
        for track in song.tracks:
            events = [copy.copy(e) for e in track.events]
            for e in events:
                e.string = e.fret = None
            if not events:
                continue
            notes += len(events)
            mapper = GuitarMapper(copy.deepcopy(cfg))
            mapped = mapper.map_events_to_fretboard(events, no_articulations=True)
            if mapper.last_path_score is None:
                have_score = False
            else:
                score += mapper.last_path_score
            ok = [e for e in mapped if e.string is not None and e.fret is not None]
            placed += len(ok)
            prev_avg, prev_strings = None, None
            for g in _groups(ok, cfg.quantization_resolution):
                sig += [(e.string, e.fret) for e in sorted(g, key=lambda e: (e.time, e.pitch))]
                frets = [e.fret for e in g]
                strings = {e.string for e in g}
                if cfg.ignore_open:
                    span_frets = [f for f in frets if f > 0]
                else:
                    span_frets = frets
                span = (max(span_frets) - min(span_frets)) if span_frets else 0
                max_span = max(max_span, span)
                if span > cfg.unplayable_fret_span:
                    unplayable += 1
                max_fret = max(max_fret, max(frets))
                opens += sum(1 for f in frets if f == 0)
                avg = sum(frets) / len(frets)
                if prev_avg is not None:
                    travel_sum += abs(avg - prev_avg)
                    travel_n += 1
                    jumps += 1 if abs(avg - prev_avg) >= JUMP_FRETS else 0
                    switches += len(strings.symmetric_difference(prev_strings))
                prev_avg, prev_strings = avg, strings
    finally:
        mapper_log.setLevel(saved)
    return Run(tuple(sig), score if have_score else None, notes, placed,
               travel_sum / travel_n if travel_n else 0.0, switches, max_fret, max_span,
               opens / placed if placed else 0.0, unplayable, jumps)


# -- M02: Viterbi vs greedy, one objective --------------------------------------------

@dataclass
class OptimizerPair:
    label: str
    group: str                       # corpus name, "probe", or "file"
    viterbi: Run
    greedy: Run
    seconds: Tuple[float, float]     # (viterbi, greedy)

    @property
    def gain_per_note(self) -> float:
        if self.viterbi.score is None or self.greedy.score is None or not self.viterbi.placed:
            return 0.0
        return (self.viterbi.score - self.greedy.score) / self.viterbi.placed

    def to_dict(self) -> dict:
        return {"label": self.label, "group": self.group, "gain_per_note": self.gain_per_note,
                "seconds": self.seconds, "same_tab": self.viterbi.signature == self.greedy.signature,
                "viterbi": self.viterbi.metrics(), "greedy": self.greedy.metrics()}


def compare_optimizers(song: Song, label: str, base: Optional[MapperConfig] = None) -> OptimizerPair:
    """Finger ``song`` under both optimizers of ``base`` (defaults if None); both report
    their path score under the one objective, so the pair is comparable."""
    import time
    base = base or MapperConfig()
    runs, secs = [], []
    for opt in ("viterbi", "greedy"):
        t0 = time.perf_counter()
        runs.append(finger(song, configured(base, optimizer=opt)))
        secs.append(time.perf_counter() - t0)
    group = "probe" if label.startswith("probe:") else (label.partition(":")[0] if ":" in label and not os.path.exists(label) else "file")
    return OptimizerPair(label, group, runs[0], runs[1], (secs[0], secs[1]))


def summarize_optimizers(pairs: Sequence[OptimizerPair]) -> dict:
    n = len(pairs) or 1
    gains = [p.gain_per_note for p in pairs]
    return {
        "tunes": len(pairs),
        "notes": sum(p.viterbi.placed for p in pairs),
        "same_tab": sum(1 for p in pairs if p.viterbi.signature == p.greedy.signature) / n,
        "viterbi_better": sum(1 for p in pairs if p.gain_per_note > 1e-9) / n,
        "viterbi_worse": sum(1 for p in pairs if p.gain_per_note < -1e-9) / n,
        "gain_per_note_mean": sum(gains) / n,
        "gain_per_note_max": max(gains) if pairs else 0.0,
        "travel": (sum(p.greedy.travel for p in pairs) / n, sum(p.viterbi.travel for p in pairs) / n),
        "jumps": (sum(p.greedy.jumps for p in pairs), sum(p.viterbi.jumps for p in pairs)),
        "switches": (sum(p.greedy.switches for p in pairs), sum(p.viterbi.switches for p in pairs)),
        "seconds": (sum(p.seconds[1] for p in pairs), sum(p.seconds[0] for p in pairs)),
    }


def format_optimizers(pairs: Sequence[OptimizerPair]) -> str:
    groups = []
    for p in pairs:
        if p.group not in groups:
            groups.append(p.group)
    lines = [f"Viterbi vs greedy, one objective; g = greedy, v = Viterbi; a jump is >= {JUMP_FRETS:g} frets",
             f"  {'group':12s} tunes   notes  same tab  v better  v worse  gain/note (max)   travel g->v    jumps g->v   switches g->v   secs g->v"]
    for g in groups + (["all"] if len(groups) > 1 else []):
        s = summarize_optimizers([p for p in pairs if g == "all" or p.group == g])
        lines.append(f"  {g:12s} {s['tunes']:5d} {s['notes']:7d}   {s['same_tab']:6.1%}   {s['viterbi_better']:6.1%}   {s['viterbi_worse']:5.1%}"
                     f"   {s['gain_per_note_mean']:6.3f} ({s['gain_per_note_max']:5.2f})   {s['travel'][0]:4.2f}->{s['travel'][1]:4.2f}"
                     f"   {s['jumps'][0]:5d}->{s['jumps'][1]:<5d}  {s['switches'][0]:6d}->{s['switches'][1]:<6d}  {s['seconds'][0]:5.1f}->{s['seconds'][1]:<6.1f}")
    return "\n".join(lines)


def configured(base: MapperConfig, **settings) -> MapperConfig:
    cfg = copy.deepcopy(base)
    names = {f.name for f in fields(MapperConfig)}
    for k, v in settings.items():
        if k not in names:
            raise ValueError(f"MapperConfig has no field {k!r}")
        setattr(cfg, k, v)
    return cfg


# -- the sweep --------------------------------------------------------------------

@dataclass
class KnobResult:
    knob: str
    values: List[object]
    runs: List[Run]
    default_index: int

    @property
    def distinct(self) -> int:
        return len({r.signature for r in self.runs})

    @property
    def breakpoints(self) -> List[object]:
        """Ladder values at which the tab differs from the previous value's."""
        return [v for v, a, b in zip(self.values[1:], self.runs, self.runs[1:])
                if a.signature != b.signature]

    @property
    def differs_from_default(self) -> List[object]:
        d = self.runs[self.default_index].signature
        return [v for v, r in zip(self.values, self.runs) if r.signature != d]

    def to_dict(self) -> dict:
        d = self.runs[self.default_index]
        return {"knob": self.knob, "distinct": self.distinct, "breakpoints": self.breakpoints,
                "differs_from_default": self.differs_from_default,
                "runs": [{"value": v, "same_as_default": r.signature == d.signature,
                          **r.metrics()} for v, r in zip(self.values, self.runs)]}


@dataclass
class SongResult:
    label: str
    base: Run
    knobs: Dict[str, KnobResult]
    scale_invariant: Optional[bool] = None   # every weight x2 leaves the tab unchanged

    def to_dict(self) -> dict:
        return {"label": self.label, "base": self.base.metrics(),
                "scale_invariant": self.scale_invariant,
                "knobs": {k: r.to_dict() for k, r in self.knobs.items()}}


def sweep_song(song: Song, label: str, *, base: Optional[MapperConfig] = None,
               knobs: Optional[Sequence[str]] = None, check_scale: bool = True) -> SongResult:
    base = base or MapperConfig()
    names = list(knobs) if knobs else list(KNOBS)
    out: Dict[str, KnobResult] = {}
    for name in names:
        k = KNOBS[name]
        values = list(k.ladder)
        current = getattr(base, k.name)
        if current not in values:
            values.append(current)
            values.sort(key=lambda v: (str(type(v)), v))
        runs = [finger(song, configured(base, **k.settings(v))) for v in values]
        out[name] = KnobResult(name, values, runs, values.index(current))
    base_run = finger(song, base)
    inv = None
    if check_scale:
        doubled = configured(base, **{n: getattr(base, n) * 2 for n in WEIGHT_NAMES})
        inv = finger(song, doubled).signature == base_run.signature
    return SongResult(label, base_run, out, inv)


# -- pooled summary ---------------------------------------------------------------

@dataclass
class KnobSummary:
    knob: str
    songs: int
    live_songs: int                  # songs where some ladder value changes the tab
    distinct_total: int              # sum over songs of distinct tabs
    max_distinct: int
    first_change: Dict[str, int]     # ladder value -> songs whose tab first changes there (vs default)
    unplayable_chosen: int           # runs (any value) where an unplayable span was chosen
    note: str

    @property
    def verdict(self) -> str:
        """``idle``: no ladder value changed any tab *with the other knobs at their
        defaults*. That is a fact about the defaults, not the knob: its case may never
        arise there (see the @context entries). ``rare``: a change on under a quarter
        of the inputs. ``live``: the rest."""
        if self.live_songs == 0:
            return "idle"
        if self.live_songs < max(1, self.songs // 4):
            return "rare"
        return "live"


def summarize(results: Sequence[SongResult]) -> List[KnobSummary]:
    names = []
    for r in results:
        for k in r.knobs:
            if k not in names:
                names.append(k)
    out = []
    for name in names:
        per = [r.knobs[name] for r in results if name in r.knobs]
        first: Dict[str, int] = {}
        for kr in per:
            d = kr.runs[kr.default_index].signature
            # nearest change below and above the default, by ladder order
            lo = [v for v, r in zip(kr.values[:kr.default_index], kr.runs[:kr.default_index])
                  if r.signature != d]
            hi = [v for v, r in zip(kr.values[kr.default_index + 1:], kr.runs[kr.default_index + 1:])
                  if r.signature != d]
            if lo:
                first[str(lo[-1])] = first.get(str(lo[-1]), 0) + 1
            if hi:
                first[str(hi[0])] = first.get(str(hi[0]), 0) + 1
        out.append(KnobSummary(
            name, len(per), sum(1 for kr in per if kr.distinct > 1),
            sum(kr.distinct for kr in per), max((kr.distinct for kr in per), default=0),
            first, sum(r.unplayable_chosen for kr in per for r in kr.runs), KNOBS[name].note))
    return out


def format_summary(summ: Sequence[KnobSummary], results: Sequence[SongResult]) -> str:
    lines = [f"{len(results)} input(s); distinct tabs per knob over its ladder, pooled:", ""]
    lines.append(f"  {'knob':32} {'verdict':8} {'live':>5} {'distinct':>9} {'max':>4}  "
                 f"{'unplayable':>10}  nearest change from default (value: songs)")
    for s in summ:
        fc = ", ".join(f"{v}: {n}" for v, n in sorted(s.first_change.items(),
                                                       key=lambda kv: -kv[1])[:4])
        lines.append(f"  {s.knob:32} {s.verdict:8} {s.live_songs:>3}/{s.songs:<2} {s.distinct_total:>9} "
                     f"{s.max_distinct:>4}  {s.unplayable_chosen:>10}  {fc}")
    bad = [r.label for r in results if r.scale_invariant is False]
    lines.append("")
    if bad:
        lines.append("  NOT scale-invariant (doubling every weight changed the tab): " + ", ".join(bad))
    else:
        lines.append("  scale check: doubling every weight left every tab unchanged (only ratios matter)")
    chosen = [(r.label, r.base.unplayable_chosen) for r in results if r.base.unplayable_chosen]
    if chosen:
        lines.append("  unplayable spans CHOSEN at the defaults: "
                     + ", ".join(f"{l} ({n})" for l, n in chosen))
    return "\n".join(lines)


def format_song(r: SongResult) -> str:
    b = r.base
    lines = [f"{r.label}: {b.notes} notes, {b.placed} placed; defaults: score "
             f"{'-' if b.score is None else round(b.score, 1)}, travel {b.travel:.2f}, "
             f"switches {b.switches}, max fret {b.max_fret}, max span {b.max_span}, "
             f"open {100 * b.open_share:.0f}%"
             + (f", UNPLAYABLE CHOSEN {b.unplayable_chosen}" if b.unplayable_chosen else "")]
    for name, kr in r.knobs.items():
        if kr.distinct == 1:
            lines.append(f"  {name:32} idle here")
            continue
        parts = []
        for v, run in zip(kr.values, kr.runs):
            mark = "=" if run.signature == kr.runs[kr.default_index].signature else "*"
            parts.append(f"{v}{mark}")
        lines.append(f"  {name:32} {kr.distinct} tabs: " + " ".join(parts))
    return "\n".join(lines)


# -- pairs (ablation) --------------------------------------------------------------

@dataclass
class PairResult:
    """A grid over two knobs: for each value of ``a``, the distinct tabs ``b`` produces
    over its ladder. A knob dead at the defaults can be live once another moves
    (sweet_spot_bonus needs a lower edge, sweet_spot_low > 0, to decide anything)."""
    label: str
    a: str
    b: str
    a_values: List[object]
    b_values: List[object]
    signatures: List[List[Signature]]       # [i][j] for a_values[i], b_values[j]

    def distinct_b_at(self, i: int) -> int:
        return len(set(self.signatures[i]))

    def distinct_a_at(self, j: int) -> int:
        return len({row[j] for row in self.signatures})

    @property
    def distinct(self) -> int:
        return len({sig for row in self.signatures for sig in row})

    def to_dict(self) -> dict:
        return {"label": self.label, "a": self.a, "b": self.b, "a_values": self.a_values,
                "b_values": self.b_values, "distinct": self.distinct,
                "distinct_b_at_a": [self.distinct_b_at(i) for i in range(len(self.a_values))],
                "distinct_a_at_b": [self.distinct_a_at(j) for j in range(len(self.b_values))]}


def sweep_pair(song: Song, label: str, a: str, b: str, *,
               base: Optional[MapperConfig] = None) -> PairResult:
    base = base or MapperConfig()
    ka, kb = KNOBS[a], KNOBS[b]
    grid = []
    for va in ka.ladder:
        row = []
        for vb in kb.ladder:
            settings = dict(ka.settings(va))
            settings.update(kb.settings(vb))
            row.append(finger(song, configured(base, **settings)).signature)
        grid.append(row)
    return PairResult(label, a, b, list(ka.ladder), list(kb.ladder), grid)


def format_pair(r: PairResult) -> str:
    head = f"{r.label}: {r.b} over its ladder, at each {r.a} ({r.distinct} distinct tabs in the grid)"
    cells = "  ".join(f"{str(v):>6}" for v in r.a_values)
    counts = "  ".join(f"{r.distinct_b_at(i):>6}" for i in range(len(r.a_values)))
    return f"{head}\n    {r.a:>18}: {cells}\n    {'distinct ' + r.b:>18}: {counts}"

# -- probes -----------------------------------------------------------------------

def _song(title: str, groups: Sequence[Sequence[int]], beat: float = 1.0) -> Song:
    """A Song from pitch groups (a list per onset), one ``beat`` apart."""
    events = [MusicalEvent(i * beat, p, beat, 90) for i, g in enumerate(groups) for p in g]
    return Song(tracks=[Track(events=events)], title=title)


def probes() -> List[Tuple[str, Song]]:
    """Constructed passages, one scorer question each. Pitches are MIDI numbers in
    STANDARD tuning (E2=40 A2=45 D3=50 G3=55 B3=59 E4=64)."""
    sus = [[50, 57, 62, 59, 64]]                       # x-5-7-7-0-0: D3 A3 D4 + open B, E
    slid = [[p + d if p not in (59, 64) else p for p in sus[0]] for d in (0, 2, 5, 7, 5, 2, 0)]
    return [
        ("probe:open-pedal",
         _song("open E pedal under a line at 5-7",
               [[64], [71], [64], [69], [64], [71], [64], [67], [64], [71]], 0.5)),
        ("probe:sus-slide",
         _song("sus shape slid 5-7-10-12 with open B and E kept", slid, 2.0)),
        ("probe:position-run",
         _song("A minor pentatonic at the 5th position, up and down",
               [[p] for p in (45, 48, 50, 52, 55, 57, 60, 62, 64, 67, 64, 62, 60, 57, 55, 52, 50, 48, 45)], 0.5)),
        ("probe:octave-leap",
         _song("low E and the E two octaves up, alternating",
               [[40], [64], [40], [64], [40], [64], [40], [64]], 0.5)),
        ("probe:wide-chord",
         _song("a chord asking for a stretch, then one that doesn't",
               [[45, 55, 64], [45, 52, 64], [45, 55, 64], [48, 55, 64]], 2.0)),
        ("probe:open-vs-fretted",
         _song("E4 G3 B3 D3: every pitch is an open string",
               [[64], [55], [59], [50], [64], [55], [59], [50]], 0.5)),
        ("probe:chromatic-climb",
         _song("a chromatic line from the 1st to the 12th fret",
               [[p] for p in range(41, 53)], 0.5)),
    ]
