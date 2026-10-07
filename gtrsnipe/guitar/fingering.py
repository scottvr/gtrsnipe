"""Whose fingering: the source tab's, or the mapper's.

A tab states where each note is played. Unless the user asks for it to be re-fingered
(or changes the notes), that is kept: every place that shows strings and frets (tab
and VexTab output, the player, chord-chart diagrams) takes its positions from
:func:`positioned`.
"""
import copy
from typing import List, Optional

from ..core.types import MusicalEvent, Song, Technique


def positioned(song: Song, events: List[MusicalEvent], mapper, *, no_articulations: bool = False,
               single_string: Optional[int] = None) -> List[MusicalEvent]:
    """``events`` (one track of ``song``) with a string and fret each: the source
    tab's own when the song is kept as written, else the mapper's choice."""
    if not getattr(song, "as_written", False):
        return mapper.map_events_to_fretboard(events, no_articulations=no_articulations,
                                              single_string=single_string)
    kept = sorted((copy.copy(e) for e in events if e.string is not None and e.fret is not None),
                  key=lambda e: e.time)
    for e in kept:
        if no_articulations or not e.technique:
            e.technique = Technique.PICK.value
    return kept


def slide(song: Song, semitones: int, max_fret: int) -> List[str]:
    """Transpose a tab without re-fingering it (``--transpose`` with ``--no-refinger``):
    every note stays on its string and moves ``semitones`` frets. Returns the notes
    that can't (a fret below the nut or past the last fret); nothing is changed then."""
    stuck = []
    for track in song.tracks:
        for e in track.events:
            if e.fret is None or e.string is None:
                continue
            if not 0 <= e.fret + semitones <= max_fret:
                stuck.append(f"beat {e.time:g}: string {e.string + 1}, fret {e.fret} -> {e.fret + semitones}")
    if stuck:
        return stuck
    for track in song.tracks:
        for e in track.events:
            if e.fret is not None and e.string is not None:
                e.fret += semitones
                e.pitch = max(0, min(127, e.pitch + semitones))
    return []
