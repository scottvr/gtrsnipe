"""Render a per-measure chord progression as a Markdown/ASCII chord sheet.

Segments the song into measures, names each chord, voices every *unique* chord
with the real fretboard mapper (so the diagrams match the song's tuning), and
lays it out as: a monospace bar-by-bar progression grid, followed by a "Chords
used" legend of ASCII chord diagrams (the vertical renderer, reused verbatim).
"""
from typing import Dict, List, Optional, Tuple

from ..core.config import MapperConfig
from ..core.types import FretPosition, MusicalEvent
from ..core.types import Song
from ..guitar.mapper import GuitarMapper
from ..player.frame import Frame
from ..player.render.ascii import AsciiFretboardRenderer
from .segment import ChordSpan, beats_per_measure, segment_by_measure

DEFAULT_MEASURES_PER_LINE = 4
DIAGRAM_WINDOW = 5


def _voice_positions(mapper: GuitarMapper, pitches: Tuple[int, ...]) -> List[FretPosition]:
    """Map a chord's representative pitches to fret positions."""
    events = [MusicalEvent(time=0.0, pitch=p, duration=1.0, velocity=100)
              for p in pitches]
    mapped = mapper.map_events_to_fretboard(events, no_articulations=True)
    return [FretPosition(e.string, e.fret)
            for e in mapped if e.string is not None and e.fret is not None]


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
            positions = _voice_positions(mapper, span.pitches)
            window = _chord_window(positions)
            frame = Frame(time=span.start_beat, duration=0.0,
                          positions=tuple(positions), window=window)
            parts += [f"**{label}**", "", "```", renderer.render(frame), "```", ""]

    return "\n".join(parts).rstrip() + "\n"
