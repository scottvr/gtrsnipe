"""Render a per-measure chord progression as a Markdown/ASCII chord sheet.

Segments the song into measures, names each chord, voices every *unique* chord
with the real fretboard mapper (so the diagrams match the song's tuning), and
lays it out as: a monospace bar-by-bar progression grid, followed by a "Chords
used" legend of ASCII chord diagrams (the vertical renderer, reused verbatim).
"""
from typing import Dict, List, Optional, Tuple

from ..core.chords import Chord
from ..core.config import MapperConfig
from ..core.types import FretPosition, MusicalEvent
from ..core.types import Song
from ..guitar.mapper import GuitarMapper
from ..player.frame import Frame
from ..player.render.ascii import AsciiFretboardRenderer
from .segment import ChordSpan, beats_per_measure, segment_by_measure

DEFAULT_MEASURES_PER_LINE = 4
DIAGRAM_WINDOW = 5


def _voice_positions(mapper: GuitarMapper, pitches) -> List[FretPosition]:
    """Map a set of pitches to fret positions (dead-ends dropped)."""
    events = [MusicalEvent(time=0.0, pitch=p, duration=1.0, velocity=100)
              for p in pitches]
    mapped = mapper.map_events_to_fretboard(events, no_articulations=True)
    return [FretPosition(e.string, e.fret)
            for e in mapped if e.string is not None and e.fret is not None]


def _canonical_positions(chord: Chord, mapper: GuitarMapper,
                         octaves: int = 4) -> List[FretPosition]:
    """A compact, playable root-position voicing of a chord for its diagram.

    Builds a close-position voicing (root + chord tones within an octave) and
    searches upward for the lowest register that the mapper can actually finger
    across distinct strings. The rock-bottom octave often crams low notes onto
    strings that can't spread them (they dead-end), so we try successive octaves
    and take the first that fingers completely; failing that, the best partial.
    """
    lowest_open = min(mapper.open_string_pitches)
    root0 = chord.root % 12
    while root0 < lowest_open:
        root0 += 12

    complete: List[tuple] = []
    best_partial: List[FretPosition] = []
    for octave in range(octaves):
        pitches = [root0 + 12 * octave + iv for iv in chord.intervals]
        positions = _voice_positions(mapper, pitches)
        if len(positions) == len(pitches):
            frets = [p.fret for p in positions]
            span = max(frets) - min(frets)
            complete.append((span, min(frets), positions))
        elif len(positions) > len(best_partial):
            best_partial = positions
    if complete:
        # Tightest span wins (a real chord shape), then the lowest register.
        complete.sort(key=lambda c: (c[0], c[1]))
        return complete[0][2]
    return best_partial                # no fully-playable register found


OPEN_MAX_FRET = 4          # the first position: frets 1-4 above the nut (or capo)
OPEN_MAX_FINGERS = 4
OPEN_MAX_STRETCH = 3       # fretted notes within a 4-fret hand span


def open_positions(chord: Chord, open_high_to_low: List[int], capo: int = 0
                   ) -> Optional[List[FretPosition]]:
    """The best open-position shape for ``chord`` (C02, ``--prefer-open-chords``), or
    None if there's none in the first position.

    Each string is muted, open (if its note is a chord tone) or fretted at 1-4 on a
    chord tone; muted strings only at the low end, so the shape strums. The shape
    must contain every chord tone (4-note chords may drop the fifth), have the
    chord's bass on its lowest sounding string, need at most four fretted strings,
    and stretch at most three frets. Doubled tones are welcome: that's what makes
    x32010 a C. One more rule keeps shapes fingerable: two notes on the same fret
    may straddle (by string) a note on a higher fret only if a barre could cover
    them, i.e. no open string lies between (so C7 x32310 passes, but Fmaj7 102210,
    with fret 1 on E and B around fret 2 and an open A, doesn't). Ranked by: most
    strings sounding, fewest fretted strings, most open strings, lowest frets. ``open_high_to_low``: open pitches, index 0 = highest
    string; frets count from the capo."""
    from itertools import product
    tones = {(chord.root + iv) % 12 for iv in chord.intervals}
    fifth = (chord.root + 7) % 12
    required = tones - ({fifth} if len(tones) >= 4 else set())
    bass_pc = chord.bass if chord.bass is not None else chord.root % 12
    opens = [p + capo for p in open_high_to_low]
    n = len(opens)
    options = []
    for o in opens:
        opts = [None]
        opts += [f for f in range(0, OPEN_MAX_FRET + 1) if (o + f) % 12 in tones]
        options.append(opts)
    best, best_key = None, None
    for combo in product(*options):
        # string n-1 is the lowest: muted strings may only form a run from the bottom
        played = [i for i in range(n) if combo[i] is not None]
        if len(played) < 3:
            continue
        lowest = max(played)
        if any(combo[i] is None for i in range(lowest)):
            continue                      # an inner or top string muted: not a strum shape
        if (opens[lowest] + combo[lowest]) % 12 != bass_pc:
            continue
        pcs = {(opens[i] + combo[i]) % 12 for i in played}
        if not required <= pcs:
            continue
        fretted = [combo[i] for i in played if combo[i] > 0]
        if len(fretted) > OPEN_MAX_FINGERS:
            continue
        if fretted and max(fretted) - min(fretted) > OPEN_MAX_STRETCH:
            continue
        opened = sum(1 for i in played if combo[i] == 0)
        if not _fingerable(combo):
            continue
        key = (-len(played), len(fretted), -opened, max(fretted, default=0), sum(fretted))
        if best_key is None or key < best_key:
            best, best_key = combo, key
    if best is None:
        return None
    return [FretPosition(i, f) for i, f in enumerate(best) if f is not None]


def _fingerable(combo) -> bool:
    """The straddle rule of ``open_positions`` (string index = position in combo)."""
    by_fret: Dict[int, List[int]] = {}
    for i, f in enumerate(combo):
        if f is not None and f > 0:
            by_fret.setdefault(f, []).append(i)
    for f, strings in by_fret.items():
        lo, hi = min(strings), max(strings)
        between = range(lo + 1, hi)
        if any(combo[k] is not None and combo[k] > f for k in between):
            if any(combo[k] == 0 for k in between):
                return False            # two fingers on fret f around higher frets
    return True


def shape_string(positions: List[FretPosition], n: int) -> str:
    """'x32010'-style shape, low string first (for checks and captions)."""
    frets = {p.string: p.fret for p in positions}
    cells = [frets.get(i) for i in reversed(range(n))]
    sep = "," if any(f is not None and f > 9 for f in cells) else ""
    return sep.join("x" if f is None else str(f) for f in cells)


def _chord_window(positions: List[FretPosition], size: int = DIAGRAM_WINDOW) -> Tuple[int, int]:
    """A compact fret window that contains the fretted notes of a chord."""
    fretted = [p.fret for p in positions if p.fret > 0]
    if not fretted:
        return (1, size)          # all open: show the nut region
    if any(p.fret == 0 for p in positions) and max(fretted) <= size:
        return (1, size)          # an open-position shape: keep the nut in view
    lo = max(1, min(fretted))
    hi = max(lo + size - 1, max(fretted))
    return (lo, hi)


def _progression_grid(spans: List[ChordSpan], per_line: int, label_of=None) -> str:
    """A monospace bar-by-bar grid of chord labels."""
    per_line = max(1, per_line)  # 0/negative would make range() raise
    labels = [(label_of or (lambda s: s.label))(s) for s in spans]
    width = max((len(x) for x in labels), default=4)
    cell = lambda x: x.ljust(width)
    lines: List[str] = []
    for i in range(0, len(labels), per_line):
        row = labels[i:i + per_line]
        lines.append("| " + " | ".join(cell(x) for x in row) + " |")
    return "\n".join(lines)


def _unique_chords(spans: List[ChordSpan], label_of=None) -> Dict[str, ChordSpan]:
    """Unique chord labels in order of first appearance (skips N.C.)."""
    out: Dict[str, ChordSpan] = {}
    for s in spans:
        label = (label_of or (lambda x: x.label))(s)
        if s.chord is not None and label not in out:
            out[label] = s
    return out


def build_chord_sheet(
    song: Song,
    mapper_config: Optional[MapperConfig] = None,
    *,
    measures_per_line: int = DEFAULT_MEASURES_PER_LINE,
    chord_tone_threshold: Optional[float] = None,
    shape_names: bool = False,
    prefer_open_chords: bool = False,
) -> str:
    """Build the full Markdown chord sheet for a song. ``shape_names``: label each
    chord by the standard-tuning shape you finger (C03); the diagrams still show the
    notes actually played, and a banner states the convention. ``prefer_open_chords``:
    draw each chord's open-position shape where one exists (C02; ``open_positions``)."""
    cfg = mapper_config or MapperConfig()
    kw = {} if chord_tone_threshold is None else {"chord_tone_threshold": chord_tone_threshold}
    spans = segment_by_measure(song, **kw)

    title = song.title or "Untitled"
    ts = song.time_signature
    parts: List[str] = [f"# {title}", "", f"*{ts}, {song.tempo:g} BPM*", ""]
    label_of = None
    if shape_names:
        from .shape_names import shape_naming_for_config
        naming = shape_naming_for_config(cfg)
        label_of = lambda s: naming.name(s.chord)
        parts += [f"> {naming.banner}", ""]

    if not spans:
        parts.append("_No notes to analyze._")
        return "\n".join(parts)

    parts += ["## Progression", "", "```", _progression_grid(spans, measures_per_line, label_of),
              "```", ""]

    uniq = _unique_chords(spans, label_of)
    if uniq:
        mapper = GuitarMapper(cfg)
        renderer = AsciiFretboardRenderer(cfg, orientation="vertical")
        n_strings = len(mapper.open_string_pitches)
        parts += ["## Chords used", ""]
        if prefer_open_chords:
            parts += ["_Open-position shapes where one exists; the others are compact "
                      "voicings._", ""]
        for label, span in uniq.items():
            positions = None
            if prefer_open_chords:
                positions = open_positions(span.chord, mapper.open_string_pitches,
                                           cfg.capo or 0)
            if not positions:
                positions = _canonical_positions(span.chord, mapper)
            if not positions:
                parts += [f"**{label}**", "",
                          f"_(no playable voicing in {cfg.tuning})_", ""]
                continue
            window = _chord_window(positions)
            frame = Frame(time=span.start_beat, duration=0.0,
                          positions=tuple(positions), window=window)
            parts += [f"**{label}** `{shape_string(positions, n_strings)}`", "", "```",
                      renderer.render(frame), "```", ""]

    return "\n".join(parts).rstrip() + "\n"
