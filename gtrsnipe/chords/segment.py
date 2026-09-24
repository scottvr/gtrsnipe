"""Segment a Song into one chord per measure.

Harmonic rhythm at the bar level: for each measure, sum how long each pitch
class sounds, keep the ones that sound long enough to be chord tones (dropping
fleeting passing/melody notes), take the lowest sounding note as the bass, and
name the result with :func:`gtrsnipe.core.chords.identify`.

Pure: Song in, ``ChordSpan`` list out. No fretboard, no I/O.
"""
import math
from collections import defaultdict
from dataclasses import dataclass
from typing import List, Optional, Tuple

from ..core.chords import Chord, identify
from ..core.types import Song

# A pitch class must sound for at least this fraction of a measure to count as a
# chord tone. Tunable; 0.15 keeps sustained harmony and drops quick runs.
DEFAULT_CHORD_TONE_THRESHOLD = 0.15


@dataclass
class ChordSpan:
    """One measure's harmonic content."""
    index: int                       # 0-based measure number
    start_beat: float                # measure start, in beats
    chord: Optional[Chord]           # None => no chord / rest (N.C.)
    pitches: Tuple[int, ...]         # representative voicing (one MIDI pitch per chord tone)

    @property
    def label(self) -> str:
        return self.chord.name if self.chord else "N.C."


def beats_per_measure(time_signature: str) -> float:
    """Beats (quarter-note beats) per measure from a "num/den" signature."""
    try:
        num, den = (int(x) for x in time_signature.split("/"))
        if num <= 0 or den <= 0:
            raise ValueError
        return num * (4.0 / den)
    except (ValueError, AttributeError):
        return 4.0  # default to 4/4


def segment_by_measure(
    song: Song,
    chord_tone_threshold: float = DEFAULT_CHORD_TONE_THRESHOLD,
) -> List[ChordSpan]:
    """Return one :class:`ChordSpan` per measure spanned by the song."""
    events = sorted(
        (e for track in song.tracks for e in track.events),
        key=lambda e: e.time,
    )
    if not events:
        return []

    bpm = beats_per_measure(song.time_signature)
    end_beat = max(e.time + max(e.duration, 0.0) for e in events)
    n_measures = max(1, math.ceil((end_beat - 1e-9) / bpm))

    spans: List[ChordSpan] = []
    for m in range(n_measures):
        lo = m * bpm
        hi = lo + bpm
        in_measure = [e for e in events if lo <= e.time < hi]
        spans.append(_span_for_measure(m, lo, hi, in_measure, chord_tone_threshold))
    return spans


def _span_for_measure(index, start, end, events, threshold) -> ChordSpan:
    if not events:
        return ChordSpan(index=index, start_beat=start, chord=None, pitches=())

    measure_len = end - start
    # Total sounding duration per pitch class (clipped to the measure).
    pc_duration: dict = defaultdict(float)
    lowest_pitch_for_pc: dict = {}
    for e in events:
        dur = min(e.time + max(e.duration, 0.0), end) - e.time
        pc = e.pitch % 12
        pc_duration[pc] += max(dur, 0.0)
        # Track the lowest actual pitch seen for each kept pitch class (for voicing).
        if pc not in lowest_pitch_for_pc or e.pitch < lowest_pitch_for_pc[pc]:
            lowest_pitch_for_pc[pc] = e.pitch

    min_dur = threshold * measure_len
    kept = [pc for pc, d in pc_duration.items() if d >= min_dur]
    # Fall back to every sounding pitch class if the threshold filtered too hard
    # (e.g. a bar of short notes) so we still name something.
    if len(kept) < 2:
        kept = list(pc_duration.keys())

    voicing = sorted(lowest_pitch_for_pc[pc] for pc in kept)
    bass = min(e.pitch for e in events)
    chord = identify(voicing, bass=bass)
    return ChordSpan(index=index, start_beat=start, chord=chord,
                     pitches=tuple(voicing))
