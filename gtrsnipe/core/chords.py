"""Chord identification from a set of pitches — the "solved" part.

Reduce pitches to pitch classes (mod 12) and match against chord templates
across all twelve roots, scoring each candidate by how many template tones are
present vs. missing vs. extra. The lowest note (the bass, which the fretboard
mapper already knows) disambiguates inversions and slash chords.

This is pure music theory: no I/O, no fretboard, no dependencies.
"""
from dataclasses import dataclass
from typing import Iterable, List, Optional, Tuple

# Sharp spelling throughout. Enharmonic key-aware spelling (Db vs C#) is a known
# limitation shared with the ABC generator; a chart still reads correctly.
PITCH_CLASS_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

# (intervals-from-root, quality-suffix), most-preferred first. On a score tie the
# earlier entry wins, so common triads beat their rarer supersets/subsets.
CHORD_TEMPLATES: List[Tuple[frozenset, str]] = [
    (frozenset({0, 4, 7}), ""),          # major triad
    (frozenset({0, 3, 7}), "m"),         # minor triad
    (frozenset({0, 7}), "5"),            # power chord (root + fifth)
    (frozenset({0, 4, 7, 10}), "7"),     # dominant 7
    (frozenset({0, 4, 7, 11}), "maj7"),
    (frozenset({0, 3, 7, 10}), "m7"),
    (frozenset({0, 4, 7, 9}), "6"),
    (frozenset({0, 3, 7, 9}), "m6"),
    (frozenset({0, 2, 7}), "sus2"),
    (frozenset({0, 5, 7}), "sus4"),
    (frozenset({0, 3, 6}), "dim"),
    (frozenset({0, 4, 8}), "aug"),
    (frozenset({0, 3, 6, 9}), "dim7"),
    (frozenset({0, 3, 6, 10}), "m7b5"),
    # Extended chords (9/11/13) are intentionally omitted for v1: without their
    # defining 7th they over-fit added melody tones, and a songbook reads fine
    # with the underlying triad/seventh.
]


@dataclass(frozen=True)
class Chord:
    """A named chord: root, quality suffix, and (if inverted) a bass note."""
    root: int                       # pitch class 0-11
    quality: str                    # "" (major), "m", "5", "7", ...
    bass: Optional[int] = None      # pitch class of the lowest note, if not the root

    @property
    def name(self) -> str:
        n = PITCH_CLASS_NAMES[self.root % 12] + self.quality
        if self.bass is not None and self.bass % 12 != self.root % 12:
            n += "/" + PITCH_CLASS_NAMES[self.bass % 12]
        return n

    def __str__(self) -> str:
        return self.name


def identify(pitches: Iterable[int], bass: Optional[int] = None) -> Optional[Chord]:
    """Best-fit chord for a collection of MIDI pitches, or ``None`` (no chord).

    Fewer than two distinct pitch classes is treated as "no chord" (a single
    note or silence isn't a strummable shape). Extra notes (a melody tone over
    the harmony) are tolerated: they cost a little but don't break the match.
    """
    pcs = {p % 12 for p in pitches}
    if len(pcs) < 2:
        return None
    bass_pc = bass % 12 if bass is not None else None

    best_key: Optional[Tuple[int, int]] = None
    best: Optional[Tuple[int, str]] = None
    for root in range(12):
        if root not in pcs:
            continue  # rootless voicings aren't worth the ambiguity for a chart
        for idx, (template, suffix) in enumerate(CHORD_TEMPLATES):
            tset = {(root + iv) % 12 for iv in template}
            present = len(tset & pcs)
            missing = len(tset - pcs)
            extra = len(pcs - tset)
            score = present * 2 - missing * 2 - extra
            if bass_pc is not None and root == bass_pc:
                score += 1  # prefer root-position readings of the bass
            key = (score, -idx)
            if best_key is None or key > best_key:
                best_key = key
                best = (root, suffix)

    if best is None:
        return None
    root, suffix = best
    return Chord(root=root, quality=suffix, bass=bass_pc)
