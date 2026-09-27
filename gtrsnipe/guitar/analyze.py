"""Which tuning makes a song easiest to play? (backlog F03)

`--analyze` used to list the tunings whose range fits the song. This fingers the
song in each of them with the user's own mapper settings and ranks them by the
mapper's path score per note -- the same yardstick as the homograph discomfort
(F06): higher is easier, and "vs best" is how many points per note a tuning
costs compared with the easiest one. Alongside, the numbers a player can read
directly: the frets used, the average hand travel between consecutive fretted
notes, and the share of open strings.
"""
from __future__ import annotations

import copy
import logging
from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

from ..core.config import MapperConfig
from ..core.types import Song
from .mapper import GuitarMapper

logger = logging.getLogger(__name__)


@dataclass
class TuningScore:
    name: str
    strings: int
    notes: int
    placed: int                      # notes the mapper found a position for
    score: Optional[float]           # Viterbi path score summed over tracks (None: greedy)
    lo_fret: int = 0
    hi_fret: int = 0
    travel: float = 0.0              # mean |fret change| between consecutive fretted notes
    open_share: float = 0.0

    @property
    def per_note(self) -> Optional[float]:
        return None if self.score is None or not self.placed else self.score / self.placed


def score_tuning(song: Song, cfg: MapperConfig, name: str) -> TuningScore:
    """Finger every track of ``song`` in ``cfg``'s tuning and summarize the result."""
    total, placed, notes, score = 0, 0, 0, 0.0
    frets: List[int] = []
    travel_sum, travel_n = 0, 0
    have_score = True
    mapper_log = logging.getLogger(GuitarMapper.__module__)
    saved = mapper_log.level
    mapper_log.setLevel(logging.WARNING)
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
            ok = sorted((e for e in mapped if e.string is not None and e.fret is not None),
                        key=lambda e: (e.time, e.pitch))
            placed += len(ok)
            frets += [e.fret for e in ok]
            prev = None
            for e in ok:
                if e.fret > 0:
                    if prev is not None:
                        travel_sum += abs(e.fret - prev)
                        travel_n += 1
                    prev = e.fret
    finally:
        mapper_log.setLevel(saved)
    return TuningScore(name, cfg.num_strings, notes, placed, score if have_score else None,
                       min(frets, default=0), max(frets, default=0),
                       travel_sum / travel_n if travel_n else 0.0,
                       sum(1 for f in frets if f == 0) / len(frets) if frets else 0.0)


def rank_tunings(song: Song, candidates: Sequence[Tuple[str, MapperConfig]]) -> List[TuningScore]:
    """Score every candidate; easiest first, tunings that dropped notes last. Equal
    scores (the default weights don't prefer open strings to a barre) are broken by
    less hand travel, then more open strings."""
    scored = [score_tuning(song, cfg, name) for name, cfg in candidates]
    return sorted(scored, key=lambda s: (s.placed < s.notes,
                                         -round(s.per_note if s.per_note is not None
                                                else -1e18, 2),
                                         round(s.travel, 2), -s.open_share))


def format_ranking(scores: Sequence[TuningScore]) -> str:
    if not scores:
        return "No tuning fits the song's range."
    best = next((s.per_note for s in scores if s.per_note is not None and s.placed == s.notes),
                None)
    lines = ["Tunings ranked by playability (the mapper's score per note with your current",
             "settings; higher is easier; 'vs best' = points per note harder than the easiest;",
             "ties go to less hand travel, then more open strings):",
             "  rank  tuning                  strings  score/note  vs best   frets   "
             "travel/note  open"]
    for k, s in enumerate(scores, 1):
        pn = "      -" if s.per_note is None else f"{s.per_note:7.2f}"
        vs = ("      -" if s.per_note is None or best is None else
              "   best" if abs(s.per_note - best) < 5e-3 else f"{best - s.per_note:+7.2f}")
        note = "" if s.placed == s.notes else f"   ({s.notes - s.placed} notes not placed)"
        lines.append(f"  {k:4d}  {s.name:22}  {s.strings:7d}  {pn:>10}  {vs:>7}   "
                     f"{s.lo_fret:2d}-{s.hi_fret:<2d}   {s.travel:11.2f}  {100 * s.open_share:3.0f}%"
                     f"{note}")
    return "\n".join(lines)
