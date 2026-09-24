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


def _chord_window(positions: List[FretPosition], size: int = DIAGRAM_WINDOW) -> Tuple[int, int]:
    """A compact fret window that contains the fretted notes of a chord."""
    fretted = [p.fret for p in positions if p.fret > 0]
    if not fretted:
        return (1, size)          # all open: show the nut region
    lo = max(1, min(fretted))
    hi = max(lo + size - 1, max(fretted))
    return (lo, hi)


def _progression_grid(spans: List[ChordSpan], per_line: int) -> str:
    """A monospace bar-by-bar grid of chord labels."""
    labels = [s.label for s in spans]
    width = max((len(x) for x in labels), default=4)
    cell = lambda x: x.ljust(width)
    lines: List[str] = []
    for i in range(0, len(labels), per_line):
        row = labels[i:i + per_line]
        lines.append("| " + " | ".join(cell(x) for x in row) + " |")
    return "\n".join(lines)


def _unique_chords(spans: List[ChordSpan]) -> Dict[str, ChordSpan]:
    """Unique chord labels in order of first appearance (skips N.C.)."""
    out: Dict[str, ChordSpan] = {}
    for s in spans:
        if s.chord is not None and s.label not in out:
            out[s.label] = s
    return out


def build_chord_sheet(
    song: Song,
    mapper_config: Optional[MapperConfig] = None,
    *,
    measures_per_line: int = DEFAULT_MEASURES_PER_LINE,
    chord_tone_threshold: Optional[float] = None,
) -> str:
    """Build the full Markdown chord sheet for a song."""
    cfg = mapper_config or MapperConfig()
    kw = {} if chord_tone_threshold is None else {"chord_tone_threshold": chord_tone_threshold}
    spans = segment_by_measure(song, **kw)

    title = song.title or "Untitled"
    ts = song.time_signature
    parts: List[str] = [f"# {title}", "", f"*{ts}, {song.tempo:g} BPM*", ""]

    if not spans:
        parts.append("_No notes to analyze._")
        return "\n".join(parts)

    parts += ["## Progression", "", "```", _progression_grid(spans, measures_per_line), "```", ""]

    uniq = _unique_chords(spans)
    if uniq:
        mapper = GuitarMapper(cfg)
        renderer = AsciiFretboardRenderer(cfg, orientation="vertical")
        parts += ["## Chords used", ""]
        for label, span in uniq.items():
            positions = _canonical_positions(span.chord, mapper)
            if not positions:
                parts += [f"**{label}**", "",
                          f"_(no playable voicing in {cfg.tuning})_", ""]
                continue
            window = _chord_window(positions)
            frame = Frame(time=span.start_beat, duration=0.0,
                          positions=tuple(positions), window=window)
            parts += [f"**{label}**", "", "```", renderer.render(frame), "```", ""]

    return "\n".join(parts).rstrip() + "\n"
