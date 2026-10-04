"""Chord identification from a set of pitches — the "solved" part.

Reduce pitches to pitch classes (mod 12) and match against chord templates
across all twelve roots, scoring each candidate by how many template tones are
present vs. missing vs. extra. The lowest note (the bass, which the fretboard
mapper already knows) disambiguates inversions and slash chords.

Names are spelled for a key (C05): pass ``key`` to :func:`identify` (or set it on a
:class:`Chord`) and an A-flat chord in E-flat reads Ab, not G#. With no key, each
root takes the spelling of its own simplest key (Bb, Eb, F#, C#m).

This is pure music theory: no I/O, no fretboard, no dependencies.
"""
from dataclasses import dataclass, field
from typing import Dict, FrozenSet, Iterable, List, Optional, Tuple

from .keys import Key, accidental, note_name, spell_free, position, _positions, _PLAIN

# Pitch-class names with sharps, for code that wants a plain label (tests, debug).
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
]


@dataclass(frozen=True)
class Extended:
    """An extended chord (C04): the tones it must have, the ones it may leave out,
    and a four-note guitar voicing of it (semitones above the root; extensions an
    octave up, as C9 is played x3233x: C E Bb D)."""
    suffix: str
    required: FrozenSet[int]
    optional: FrozenSet[int]
    voicing: Tuple[int, ...]
    shape_only: bool = False


# Three guards keep a melody note from being named as an extension:
# - the chord must be complete: every required tone sounds and nothing outside the
#   chord does. (The fifth is optional throughout, as are a 13th's 9th, an 11th's 3rd
#   and a minor 13th's 11th.)
# - its root must be the bass. The same notes over another bass are a simpler chord with
#   a note added (C-E-G with a D on top), or a slash chord (D11 is C/D).
# - the additions with no seventh to define them (add9, 6/9) are named only for a fret
#   shape, where every note is the chord (``identify(..., shape=True)``). In a bar of
#   music a C triad with a D over it stays C.
EXTENDED: List[Extended] = [
    Extended("7sus4", frozenset({0, 5, 10}), frozenset({7}), (0, 5, 7, 10)),
    Extended("add9", frozenset({0, 4, 2}), frozenset({7}), (0, 4, 7, 14), True),
    Extended("madd9", frozenset({0, 3, 2}), frozenset({7}), (0, 3, 7, 14), True),
    Extended("6/9", frozenset({0, 4, 9, 2}), frozenset({7}), (0, 4, 9, 14), True),
    Extended("9", frozenset({0, 4, 10, 2}), frozenset({7}), (0, 4, 10, 14)),
    Extended("maj9", frozenset({0, 4, 11, 2}), frozenset({7}), (0, 4, 11, 14)),
    Extended("m9", frozenset({0, 3, 10, 2}), frozenset({7}), (0, 3, 10, 14)),
    Extended("7b9", frozenset({0, 4, 10, 1}), frozenset({7}), (0, 4, 10, 13)),
    Extended("7#9", frozenset({0, 4, 10, 3}), frozenset({7}), (0, 4, 10, 15)),
    Extended("11", frozenset({0, 10, 2, 5}), frozenset({7, 4}), (0, 10, 14, 17)),
    Extended("m11", frozenset({0, 3, 10, 5}), frozenset({7, 2}), (0, 3, 10, 17)),
    Extended("13", frozenset({0, 4, 10, 9}), frozenset({7, 2}), (0, 4, 10, 21)),
    Extended("maj13", frozenset({0, 4, 11, 9}), frozenset({7, 2}), (0, 4, 11, 21)),
    Extended("m13", frozenset({0, 3, 10, 9}), frozenset({7, 2, 5}), (0, 3, 10, 21)),
]
_EXTENDED: Dict[str, Extended] = {x.suffix: x for x in EXTENDED}

# Interval set for each quality suffix, for realizing a chord as pitches.
QUALITY_INTERVALS = {suffix: tuple(sorted(template))
                     for template, suffix in CHORD_TEMPLATES}
QUALITY_INTERVALS.update({x.suffix: tuple(sorted(x.required | x.optional)) for x in EXTENDED})

_MINORISH = {"m", "m7", "m6", "dim", "dim7", "m7b5", "madd9", "m9", "m11", "m13"}

# How a chord tone is spelled from its root, in fifths (a major third is four fifths
# up: C -> E; a minor seventh two down: C -> Bb). Overrides where the quality decides.
_TONE_FIFTHS = {0: 0, 1: -5, 2: 2, 3: -3, 4: 4, 5: -1, 6: -6, 7: 1, 8: -4, 9: 3, 10: -2, 11: 5}
_TONE_OVERRIDES = {"aug": {8: 8}, "7#9": {3: 9}}


@dataclass(frozen=True)
class Chord:
    """A named chord: root, quality suffix, and (if inverted) a bass note. ``key``
    only decides the spelling of the name; it isn't part of the chord's identity."""
    root: int                       # pitch class 0-11
    quality: str                    # "" (major), "m", "5", "7", "9", ...
    bass: Optional[int] = None      # pitch class of the lowest note, if not the root
    key: Optional[Key] = field(default=None, compare=False)

    @property
    def intervals(self) -> Tuple[int, ...]:
        """Semitone offsets of the chord tones from the root (root-position)."""
        return QUALITY_INTERVALS.get(self.quality, (0,))

    @property
    def optional(self) -> FrozenSet[int]:
        """Chord tones a voicing may leave out: an extended chord's optional tones, or
        the fifth of a four-note chord."""
        ext = _EXTENDED.get(self.quality)
        if ext:
            return ext.optional
        return frozenset({7}) if len(self.intervals) >= 4 and 7 in self.intervals else frozenset()

    @property
    def voicing(self) -> Tuple[int, ...]:
        """Semitones above the root for a compact diagram of the chord."""
        ext = _EXTENDED.get(self.quality)
        return ext.voicing if ext else self.intervals

    @property
    def extended(self) -> bool:
        return self.quality in _EXTENDED

    def root_position(self) -> int:
        """The root's spelling as a line-of-fifths position."""
        if self.key is not None:
            return self.key.position_of(self.root % 12)
        return position(spell_free(self.root % 12, self.quality in _MINORISH))

    def spell(self, pc: int) -> str:
        """Pitch class ``pc`` spelled in this chord: a chord tone as the chord spells it
        (the third of E is G#, of Ab is C), anything else in the key."""
        root = self.root_position()
        iv = (pc - self.root) % 12
        if iv in self.intervals:
            pos = root + _TONE_OVERRIDES.get(self.quality, {}).get(iv, _TONE_FIFTHS[iv])
            if -8 <= pos <= 12:                     # at most one sharp or flat
                return note_name(pos)
        if self.key is not None:
            return self.key.spell(pc % 12)
        return note_name(min(_positions(pc % 12, *_PLAIN), key=lambda p: (abs(p - root), p)))

    @property
    def name(self) -> str:
        n = note_name(self.root_position()) + self.quality
        if self.bass is not None and self.bass % 12 != self.root % 12:
            n += "/" + self.spell(self.bass % 12)
        return n

    def __str__(self) -> str:
        return self.name


def identify(pitches: Iterable[int], bass: Optional[int] = None,
             key: Optional[Key] = None, shape: bool = False) -> Optional[Chord]:
    """Best-fit chord for a collection of MIDI pitches, or ``None`` (no chord).

    Fewer than two distinct pitch classes is treated as "no chord" (a single
    note or silence isn't a strummable shape). Extra notes (a melody tone over
    the harmony) are tolerated: they cost a little but don't break the match.
    An extended chord (9th, 11th, 13th, ...) is a candidate only when it is
    complete (all its required tones and nothing else) and its root is the bass (the
    lowest pitch, when ``bass`` isn't given); see ``EXTENDED``. ``shape``: the pitches
    are one fret shape, not a bar of music, so add9 and 6/9 may be named. ``key``
    spells the name.
    """
    pitches = list(pitches)
    pcs = {p % 12 for p in pitches}
    if len(pcs) < 2:
        return None
    bass_pc = bass % 12 if bass is not None else None
    lowest_pc = bass_pc if bass_pc is not None else min(pitches) % 12

    best_key: Optional[Tuple[int, int]] = None
    best: Optional[Tuple[int, str]] = None
    for root in range(12):
        if root not in pcs:
            continue  # rootless voicings aren't worth the ambiguity for a chart
        rel = {(p - root) % 12 for p in pcs}
        candidates = []
        for idx, (template, suffix) in enumerate(CHORD_TEMPLATES):
            present = len(template & rel)
            missing = len(template - rel)
            extra = len(rel - template)
            candidates.append((present * 2 - missing * 2 - extra, idx, suffix))
        for j, x in enumerate(EXTENDED if root == lowest_pc else ()):
            if x.shape_only and not shape:
                continue
            if x.required <= rel and rel <= x.required | x.optional:
                score = 2 * len(x.required) + len(rel & x.optional)
                candidates.append((score, len(CHORD_TEMPLATES) + j, x.suffix))
        for score, idx, suffix in candidates:
            if bass_pc is not None and root == bass_pc:
                score += 1  # prefer root-position readings of the bass
            rank = (score, -idx)
            if best_key is None or rank > best_key:
                best_key = rank
                best = (root, suffix)

    if best is None:
        return None
    root, suffix = best
    return Chord(root=root, quality=suffix, bass=bass_pc, key=key)


def is_clear(chord: Chord, pitches: Iterable[int]) -> bool:
    """True when ``pitches`` spell ``chord`` plainly: every chord tone present except
    perhaps the fifth, at most one pitch class outside the chord, and at least three
    chord tones. A power chord must be exactly its root and fifth: with anything else
    added it is some other chord with a missing third. An extended chord must be
    complete, with nothing outside it. :func:`identify` always returns its best
    guess, which a chart needs for every bar; this is the stricter test for places
    where no name beats a doubtful one (``--name-chords``)."""
    pcs = {p % 12 for p in pitches}
    tones = {(chord.root + iv) % 12 for iv in chord.intervals}
    if chord.quality == "5":
        return pcs == tones
    if chord.extended:
        optional = {(chord.root + iv) % 12 for iv in chord.optional}
        return tones - optional <= pcs <= tones
    missing = tones - pcs
    if missing - {(chord.root + 7) % 12}:
        return False
    if len(pcs - tones) > 1:
        return False
    return len(pcs & tones) >= 3
