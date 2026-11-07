"""M03: per-onset difficulty descriptors of a fingered tab, and their profile.

A tab is read as a sequence of *onsets* (the notes struck together), each with the
fingering the tab states (or the mapper chose). Each onset gets a handful of numbers a
guitarist would recognise (where the hand is, how many fingers are down, how far they
stretch, how far and how fast the hand just moved), and the tab's profile is the mean,
quadratic mean and maximum of each over the tab, plus a few whole-tab counts.

The design follows the literature survey (``docs/research/literature/LITERATURE-difficulty.md``):
hand position is the index finger (the lowest fretted fret: Ariga et al. 2017, Hori & Sagayama
2016); a hand move is charged against the time available for it (Hori scales by the
onset-to-onset interval; scottvr's rule, 2026-11-07, is the gap from the end of the previous
note to the next onset, because lifting the finger is what ends a fretted note, so both are
implemented and compared: M08); per-tab summaries are means and maxima, not totals (Rodríguez
& Klapuri 2025, Vélez Vásquez et al. 2023); and repetitiveness is the Lempel-Ziv complexity of
the shape sequence (after Ramoneda et al. 2024's pitch-set LZ).

Nothing here is a verdict on difficulty yet: the weights of the provisional index are
hand-set and the validation against graded repertoire (backlog M03) is what will set them.
"""
from __future__ import annotations

import copy
import logging
import math
import statistics as st
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Sequence, Tuple

from ..core.config import MapperConfig
from ..core.types import MusicalEvent, Song
from ..guitar.mapper import GuitarMapper
from .sweep import _groups

TIME_BASES = ("end", "onset")
# The hand cannot use less than this much time for a move, whatever the notation says.
# Score-derived MIDI holds most notes to the next onset, so without a floor the end-to-start
# gap is zero almost everywhere.
MIN_GAP_SECONDS = 0.05
SHIFT_FRETS = 2       # a change of hand position this large or more counts as a shift
REACH_FRETS = 3       # frets above the index finger the hand covers without moving (four fingers, one per fret)


@dataclass
class Onset:
    """One struck moment of a tab and what it asks of the fretting hand."""
    time: float                     # beats
    seconds: float                  # time at the song's tempo
    notes: int                      # pitches struck together
    fretted: int                    # of which fretted (not open)
    index_fret: Optional[int]       # the lowest fretted fret of this onset; None if all open
    position: Optional[float]       # where the hand is: the index finger's fret. A shape (two or more
                                    # fretted notes) puts it at the lowest fretted fret; a single note
                                    # follows the lazy hand model: the hand stays put while the note lies
                                    # within REACH_FRETS above it, else moves the least distance that fits
    fingers: int                    # fingers down, the lowest fret's notes counted once (an index barre)
    span: int                       # highest fretted fret minus lowest; 0 under two fretted notes
    barre: bool                     # two or more notes on the lowest fretted fret
    shift: float                    # |position - previous position| in frets; 0 at the start or across all-open onsets
    gap: float                      # seconds the hand had for that shift (by the time base), floored
    move_rate: float                # shift / gap, frets per second
    shape_change: int               # (string, fret) pairs that differ from the previous onset
    ioi: float                      # seconds to the next onset (the last onset: its own duration)
    technique: int                  # notes carrying a technique mark (hammer-on, pull-off, bend, slide, tap)


@dataclass
class Profile:
    """A tab's difficulty profile: per-descriptor mean / quadratic mean / max, and counts."""
    label: str
    onsets: int
    notes: int
    seconds: float
    tempo: float
    rhythm_approximate: bool
    time_base: str
    fingering: str                  # "as written" or "mapper"
    stats: Dict[str, Tuple[float, float, float]]   # descriptor -> (mean, quadratic mean, max)
    shifts: int                     # position changes of SHIFT_FRETS or more
    shifts_per_minute: float
    position_range: float           # highest minus lowest hand position used
    max_position: float
    chord_share: float              # onsets with two or more notes
    barre_share: float
    repetitiveness: float           # 1 - normalised Lempel-Ziv complexity of the shape sequence (1 = all repeats)
    notes_per_second: float
    index: float                    # the provisional single number; see index()

    def to_dict(self) -> dict:
        d = asdict(self)
        d["stats"] = {k: list(v) for k, v in self.stats.items()}
        return d


DESCRIPTORS = ("fingers", "span", "shift", "move_rate", "shape_change", "notes", "technique")


def _seconds_per_beat(song: Song) -> float:
    tempo = song.tempo if song.tempo and song.tempo > 0 else 120.0
    return 60.0 / tempo


def finger_song(song: Song, cfg: Optional[MapperConfig] = None) -> Song:
    """A copy of ``song`` whose events the mapper has fingered (its own fingering dropped)."""
    cfg = cfg or MapperConfig()
    out = copy.deepcopy(song)
    log = logging.getLogger(GuitarMapper.__module__)
    saved = log.level
    log.setLevel(logging.ERROR)
    try:
        for track in out.tracks:
            for e in track.events:
                e.string = e.fret = None
            if track.events:
                track.events = GuitarMapper(copy.deepcopy(cfg)).map_events_to_fretboard(
                    track.events, no_articulations=True)
    finally:
        log.setLevel(saved)
    return out


def fingered_events(song: Song) -> List[MusicalEvent]:
    """The events of the first track that carry a string and a fret."""
    if not song.tracks:
        return []
    return [e for e in song.tracks[0].events if e.string is not None and e.fret is not None]


def onsets(song: Song, *, time_base: str = "end", min_gap: float = MIN_GAP_SECONDS,
           resolution: float = 0.0, reach: int = REACH_FRETS) -> List[Onset]:
    """The per-onset descriptors of a fingered song (first track). ``reach`` is the lazy hand
    model's span above the index finger; 0 puts the hand at every onset's lowest fretted fret
    (the plain index-finger proxy)."""
    if time_base not in TIME_BASES:
        raise ValueError(f"time_base must be one of {TIME_BASES}, got {time_base!r}")
    spb = _seconds_per_beat(song)
    events = fingered_events(song)
    groups = _groups(events, resolution)
    out: List[Onset] = []
    prev: Optional[Onset] = None
    prev_pairs: set = set()
    prev_end_beats: Optional[float] = None
    hand: Optional[float] = None       # the lazy hand's position, carried across all-open onsets
    for i, g in enumerate(groups):
        t = g[0].time
        frets = [e.fret for e in g]
        fretted = sorted(f for f in frets if f > 0)
        idx = fretted[0] if fretted else None
        if idx is None:
            pos = None                                  # nothing to hold; the hand stays where it was
        elif len(fretted) >= 2:
            pos = float(idx)                            # a shape anchors the index finger at its lowest fret
        elif hand is None or hand > idx:
            pos = float(idx)                            # down the neck to the lowest fretted note
        elif fretted[-1] <= hand + reach:
            pos = hand                                  # everything is within reach: no move
        else:
            pos = float(min(idx, fretted[-1] - reach))  # up the neck, the least that fits
        if pos is not None:
            hand = pos
        lowest_count = fretted.count(fretted[0]) if fretted else 0
        fingers = len(fretted) - max(0, lowest_count - 1)
        span = (fretted[-1] - fretted[0]) if len(fretted) >= 2 else 0
        barre = lowest_count >= 2
        pairs = {(e.string, e.fret) for e in g}
        shape_change = len(pairs ^ prev_pairs) if prev is not None else 0
        prev_pos = next((o.position for o in reversed(out) if o.position is not None), None)
        if prev is not None and pos is not None and prev_pos is not None:
            shift = abs(pos - prev_pos)
        else:
            shift = 0.0
        if prev is None:
            gap = math.inf
        elif time_base == "onset":
            gap = (t - prev.time) * spb
        else:
            gap = (t - prev_end_beats) * spb
        gap = max(gap, min_gap)
        move_rate = shift / gap if math.isfinite(gap) else 0.0
        if i + 1 < len(groups):
            ioi = (groups[i + 1][0].time - t) * spb
        else:
            ioi = max(e.duration for e in g) * spb
        tech = sum(1 for e in g if e.technique and str(e.technique).lower() not in ("pick", "technique.pick", "none"))
        o = Onset(time=t, seconds=t * spb, notes=len(g), fretted=len(fretted), index_fret=idx, position=pos,
                  fingers=fingers, span=span, barre=barre, shift=shift,
                  gap=gap if math.isfinite(gap) else 0.0, move_rate=move_rate,
                  shape_change=shape_change, ioi=max(ioi, 0.0), technique=tech)
        out.append(o)
        prev, prev_pairs = o, pairs
        prev_end_beats = max(e.time + e.duration for e in g)
    return out


def lz_complexity(tokens: Sequence) -> int:
    """Lempel-Ziv (LZ76) phrase count of a sequence: the number of new phrases a left-to-right
    parse needs. Low for repetitive sequences, about n/log n for random ones."""
    s = list(tokens)
    n = len(s)
    if n == 0:
        return 0
    i, c = 0, 0
    while i < n:
        l = 1
        # longest prefix of s[i:] that occurs in s[:i+l-1] (overlap allowed, as in LZ76)
        while i + l <= n and _occurs(s, i, l):
            l += 1
        c += 1
        i += l
    return c


def _occurs(s: list, i: int, l: int) -> bool:
    pat = s[i:i + l]
    for j in range(0, i):
        if s[j:j + l] == pat and j + l <= i + l - 1:
            return True
    return False


def repetitiveness(onsets_: Sequence[Onset], song: Song) -> float:
    """1 minus the LZ complexity of the shape sequence, normalised by that of a sequence with
    no repeats (every onset new). 0 means nothing repeats; near 1 means it all does."""
    events = fingered_events(song)
    groups = _groups(events, 0.0)
    shapes = [tuple(sorted((e.string, e.fret) for e in g)) for g in groups]
    n = len(shapes)
    if n < 2:
        return 0.0
    c = lz_complexity(shapes)
    return max(0.0, min(1.0, 1.0 - (c - 1) / (n - 1)))


# Provisional weights for the single index. Units: each term is a per-onset mean (or a rate),
# scaled so that one "unit" is roughly one grade's worth in the survey's terms. These are
# hand-set placeholders until the M03 validation sets them; nothing downstream depends on them.
INDEX_WEIGHTS = {
    "move_rate": 0.25,     # frets per second of hand movement, mean
    "fingers": 1.0,        # fingers down, mean
    "span": 0.5,           # fret span, mean
    "shape_change": 0.25,  # pairs changed per onset, mean
    "notes_per_second": 0.5,
    "shifts_per_minute": 0.05,
    "max_move_rate": 0.05,  # the hardest move
}


def index(p: "Profile") -> float:
    s = p.stats
    return (INDEX_WEIGHTS["move_rate"] * s["move_rate"][0]
            + INDEX_WEIGHTS["fingers"] * s["fingers"][0]
            + INDEX_WEIGHTS["span"] * s["span"][0]
            + INDEX_WEIGHTS["shape_change"] * s["shape_change"][0]
            + INDEX_WEIGHTS["notes_per_second"] * p.notes_per_second
            + INDEX_WEIGHTS["shifts_per_minute"] * p.shifts_per_minute
            + INDEX_WEIGHTS["max_move_rate"] * s["move_rate"][2]) * (1.0 - 0.5 * p.repetitiveness)


def _mqm(xs: Sequence[float]) -> Tuple[float, float, float]:
    xs = list(xs)
    if not xs:
        return (0.0, 0.0, 0.0)
    return (st.fmean(xs), math.sqrt(st.fmean(x * x for x in xs)), max(xs))


def profile(song: Song, label: str = "", *, time_base: str = "end", min_gap: float = MIN_GAP_SECONDS,
            refinger: bool = False, cfg: Optional[MapperConfig] = None, reach: int = REACH_FRETS) -> Profile:
    """The difficulty profile of a song: its own fingering if it has one (a tab), else the
    mapper's; ``refinger`` forces the mapper's."""
    own = bool(fingered_events(song)) and not refinger
    fingered = song if own else finger_song(song, cfg)
    os_ = onsets(fingered, time_base=time_base, min_gap=min_gap, reach=reach)
    events = fingered_events(fingered)
    spb = _seconds_per_beat(fingered)
    if not os_:
        seconds = 0.0
    else:
        seconds = max(e.time + e.duration for e in events) * spb - os_[0].seconds
    stats = {
        "fingers": _mqm([o.fingers for o in os_]),
        "span": _mqm([o.span for o in os_]),
        "shift": _mqm([o.shift for o in os_]),
        "move_rate": _mqm([o.move_rate for o in os_]),
        "shape_change": _mqm([o.shape_change for o in os_]),
        "notes": _mqm([o.notes for o in os_]),
        "technique": _mqm([o.technique for o in os_]),
    }
    positions = [o.position for o in os_ if o.position is not None]
    shifts = sum(1 for o in os_ if o.shift >= SHIFT_FRETS)
    p = Profile(
        label=label or fingered.title, onsets=len(os_), notes=len(events), seconds=seconds,
        tempo=fingered.tempo, rhythm_approximate=bool(getattr(fingered, "rhythm_approximate", False)),
        time_base=time_base, fingering="as written" if own else "mapper", stats=stats,
        shifts=shifts, shifts_per_minute=(shifts / seconds * 60.0) if seconds > 0 else 0.0,
        position_range=(max(positions) - min(positions)) if positions else 0.0,
        max_position=max(positions) if positions else 0.0,
        chord_share=(sum(1 for o in os_ if o.notes > 1) / len(os_)) if os_ else 0.0,
        barre_share=(sum(1 for o in os_ if o.barre) / len(os_)) if os_ else 0.0,
        repetitiveness=repetitiveness(os_, fingered),
        notes_per_second=(len(events) / seconds) if seconds > 0 else 0.0,
        index=0.0,
    )
    p.index = index(p)
    return p


def format_profiles(profiles: Sequence[Profile]) -> str:
    head = (f"{'piece':36s} {'ons':>4s} {'sec':>6s} {'fing':>5s} {'span':>5s} {'shift':>5s} "
            f"{'mv/s':>6s} {'max':>6s} {'chg':>5s} {'n/s':>5s} {'sh/m':>5s} {'rep':>4s} {'brr':>4s} "
            f"{'pos':>5s} {'index':>6s}  fingering/time")
    rows = [head]
    for p in profiles:
        s = p.stats
        rows.append(f"{p.label[:36]:36s} {p.onsets:4d} {p.seconds:6.1f} {s['fingers'][0]:5.2f} "
                    f"{s['span'][0]:5.2f} {s['shift'][0]:5.2f} {s['move_rate'][0]:6.2f} "
                    f"{s['move_rate'][2]:6.1f} {s['shape_change'][0]:5.2f} {p.notes_per_second:5.2f} "
                    f"{p.shifts_per_minute:5.1f} {p.repetitiveness:4.2f} {p.barre_share:4.2f} "
                    f"{p.max_position:5.0f} {p.index:6.2f}  {p.fingering}/{p.time_base}"
                    f"{' ~rhythm' if p.rhythm_approximate else ''}")
    rows.append("mean/max per onset: fing fingers down, span frets, shift frets of hand movement, mv/s frets per "
                "second (max: the hardest move), chg shape pairs changed; n/s notes per second; sh/m shifts "
                "per minute; rep repetitiveness 0-1; brr barre share; pos highest hand position")
    return "\n".join(rows)


def format_onsets(os_: Sequence[Onset]) -> str:
    rows = [f"{'beat':>7s} {'sec':>6s} {'n':>2s} {'idx':>4s} {'pos':>4s} {'fng':>3s} {'spn':>3s} {'brr':>3s} "
            f"{'shift':>5s} {'gap':>6s} {'mv/s':>6s} {'chg':>3s} {'ioi':>5s} {'tech':>4s}"]
    for o in os_:
        pos = f"{o.position:4.0f}" if o.position is not None else "   -"
        idx = f"{o.index_fret:4d}" if o.index_fret is not None else "   -"
        rows.append(f"{o.time:7.3f} {o.seconds:6.2f} {o.notes:2d} {idx} {pos} {o.fingers:3d} {o.span:3d} "
                    f"{'  b' if o.barre else '  .'} {o.shift:5.1f} {o.gap:6.2f} {o.move_rate:6.1f} "
                    f"{o.shape_change:3d} {o.ioi:5.2f} {o.technique:4d}")
    return "\n".join(rows)


def compare_time_bases(song: Song, label: str = "", *, min_gap: float = MIN_GAP_SECONDS,
                       refinger: bool = False) -> Dict[str, Profile]:
    """The same song under both time bases (M08's comparison on the measure side)."""
    return {tb: profile(song, label, time_base=tb, min_gap=min_gap, refinger=refinger) for tb in TIME_BASES}
