"""Keys and enharmonic spelling (C05, F02).

The same black key is C# in A major and Db in A-flat major. A key decides the
spelling: notes of its scale are spelled as the scale spells them, and a note
outside it takes the spelling nearer the key on the line of fifths (ties go to the
flat, as borrowed chords mostly come from the flat side). In a minor key the raised
seventh is the leading tone (G# in A minor). Odd spellings (Cb, Fb, E#, B#) appear
only where the key's own scale has them.

Spellings are positions on the line of fifths: C = 0, G = 1, F = -1, F# = 6, Bb = -2.
A key signature with k sharps (negative: flats) holds the positions k-1 .. k+5.

Where a song's key comes from, in order: ``--key``, the file's own key signature
(MIDI key-signature event, ABC ``K:``), else an estimate from the notes
(:func:`estimate_key`). Whatever writes a spelled name says which.

Pure: no I/O, no dependencies.
"""
import re
from dataclasses import dataclass
from typing import Iterable, List, Optional, Tuple

_FIFTHS = "FCGDAEB"                       # natural letters in line-of-fifths order
_MODE_OFFSET = {"major": 0, "mixolydian": 1, "dorian": 2, "minor": 3, "phrygian": 4,
                "locrian": 5, "lydian": -1}
_MODE_WORDS = {"maj": "major", "ion": "major", "min": "minor", "aeo": "minor",
               "dor": "dorian", "phr": "phrygian", "lyd": "lydian", "mix": "mixolydian",
               "loc": "locrian"}
_ABC_MODE = {"major": "", "minor": "m", "dorian": "dor", "phrygian": "phr", "lydian": "lyd",
             "mixolydian": "mix", "locrian": "loc"}

ESTIMATED = "estimated from the notes"
FROM_FILE = "from the file"
FROM_OPTION = "from --key"
DOUBTED = "from the file (doubted)"       # a MIDI file's C major: see song_key


def note_name(pos: int) -> str:
    """The note at line-of-fifths position ``pos``: 0 -> 'C', -2 -> 'Bb', 6 -> 'F#'."""
    letter = _FIFTHS[(pos + 1) % 7]
    acc = (pos + 1) // 7
    return letter + ("#" * acc if acc > 0 else "b" * -acc)


def position(name: str) -> int:
    """Line-of-fifths position of a spelled note ('Bb' -> -2); octave digits ignored."""
    m = re.fullmatch(r"([A-Ga-g])([#b]*)-?\d*", name.strip())
    if not m:
        raise ValueError(f"not a note name: {name!r}")
    acc = m.group(2)
    return _FIFTHS.index(m.group(1).upper()) - 1 + 7 * (acc.count("#") - acc.count("b"))


def pitch_class(pos: int) -> int:
    return (7 * pos) % 12


def accidental(pos: int) -> int:
    """Sharps (+) or flats (-) on the note at ``pos``."""
    return (pos + 1) // 7


def _positions(pc: int, lo: int, hi: int) -> List[int]:
    """Every spelling of pitch class ``pc`` with its position in [lo, hi]."""
    p0 = (7 * pc) % 12
    return [p for p in (p0 - 24, p0 - 12, p0, p0 + 12, p0 + 24) if lo <= p <= hi]


# Positions of the everyday spellings: naturals and single sharps/flats, but not
# Cb, Fb, E# or B# (those only when a key's own scale spells them).
_PLAIN = (-6, 10)


@dataclass(frozen=True)
class Key:
    """A key: its spelled tonic and mode (major, minor, or a church mode)."""
    tonic: str
    mode: str = "major"

    @property
    def fifths(self) -> int:
        """The key signature: sharps (+) or flats (-)."""
        return position(self.tonic) - _MODE_OFFSET[self.mode]

    @property
    def tonic_pc(self) -> int:
        return pitch_class(position(self.tonic))

    @property
    def minor(self) -> bool:
        return self.mode == "minor"

    @property
    def name(self) -> str:
        return f"{self.tonic} {self.mode}"

    @property
    def abc(self) -> str:
        """The ``K:`` field value (``Eb``, ``F#m``, ``Ddor``)."""
        return self.tonic + _ABC_MODE[self.mode]

    def __str__(self) -> str:                  # what parse_key reads back (profiles save it)
        return self.name

    def signature(self) -> dict:
        """Letter -> accidental in the key signature (``{'B': -1, 'E': -1}`` for Bb major)."""
        k = self.fifths
        letters = _FIFTHS[::-1][:-k] if k < 0 else _FIFTHS[:k]
        return {letter: (1 if k > 0 else -1) for letter in letters}

    def position_of(self, pc: int) -> int:
        """The spelling of pitch class ``pc`` in this key, as a line-of-fifths position."""
        k = self.fifths
        scale = _positions(pc, k - 1, k + 5)
        if scale:
            return scale[0]
        tonic = position(self.tonic)
        if self.minor and pitch_class(tonic + 5) == pc:
            return tonic + 5                                 # the leading tone
        centre = k + (3 if self.minor else 2)
        return min(_positions(pc, *_PLAIN), key=lambda p: (abs(p - centre), p))

    def spell(self, pc: int) -> str:
        return note_name(self.position_of(pc))

    def transposed(self, semitones: int) -> "Key":
        """The same mode on a tonic ``semitones`` away, spelled with the fewest accidentals."""
        return key_on(self.tonic_pc + semitones, self.mode)


def key_on(pc: int, mode: str = "major") -> "Key":
    """The key of ``mode`` on pitch class ``pc`` with the fewest sharps or flats (a tie,
    such as F# vs Gb major, goes to the sharps)."""
    off = _MODE_OFFSET[mode]
    cands = _positions(pc, off - 7, off + 7)
    pos = min(cands, key=lambda p: (abs(p - off), -p))
    return Key(note_name(pos), mode)


def parse_key(text: str) -> Optional[Key]:
    """A key from text such as ``Eb``, ``F#m``, ``Bbmin``, ``D dorian``, ``Amix`` or
    ``C major`` (the forms ``--key`` and ABC's ``K:`` use). ``None`` for ABC's
    ``none``/``HP``/``Hp``; ``ValueError`` for anything else it can't read, or a key
    with more than seven sharps or flats."""
    t = text.strip()
    if t.lower() in ("", "none") or t in ("HP", "Hp"):
        return None
    m = re.fullmatch(r"([A-Ga-g])([#b]?)\s*([A-Za-z]*)", t)
    if not m:
        raise ValueError(f"can't read the key {text!r} (try Eb, F#m or 'D dorian')")
    word = m.group(3).lower()
    if word in ("", "major"):
        mode = "major"
    elif word in ("m", "minor"):
        mode = "minor"
    elif word[:3] in _MODE_WORDS:
        mode = _MODE_WORDS[word[:3]]
    else:
        raise ValueError(f"can't read the mode in {text!r} (major, minor, dorian, ...)")
    key = Key(m.group(1).upper() + m.group(2), mode)
    if abs(key.fifths) > 7:
        better = key_on(key.tonic_pc, mode)
        raise ValueError(f"{key.name} would need {abs(key.fifths)} "
                         f"{'sharps' if key.fifths > 0 else 'flats'}; use {better.name}")
    return key


def parse_abc_key(value: str) -> Optional[Key]:
    """The key of an ABC ``K:`` field value, ignoring clef and explicit accidentals;
    ``None`` when it names no key."""
    toks = [t for t in value.split() if "=" not in t]
    if not toks:
        return None
    head = toks[0]
    if len(toks) > 1 and re.fullmatch(r"[A-Ga-g][#b]?", head) and toks[1][:3].lower() in (
            set(_MODE_WORDS) | {"m", "maj", "min", "major", "minor"}):
        head += toks[1]
    try:
        return parse_key(head)
    except ValueError:
        return None


# Key profiles: how much each pitch class (tonic first) belongs to a major or a minor
# key. Krumhansl & Kessler's probe-tone ratings (1982), and Temperley's profile from the
# Kostka-Payne corpus; the numbers are as given in music21's ``analysis.discrete``.
_KK = ((6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88),
       (6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17))
_TKP = ((0.748, 0.060, 0.488, 0.082, 0.670, 0.460, 0.096, 0.715, 0.104, 0.366, 0.057, 0.400),
        (0.712, 0.084, 0.474, 0.618, 0.049, 0.460, 0.105, 0.747, 0.404, 0.067, 0.133, 0.330))


def _correlation(xs, ys) -> float:
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    return sxy / (sxx * syy) ** 0.5 if sxx and syy else 0.0


def _fit(hist, tonic: int, mode: str, profiles) -> float:
    return _correlation(hist[tonic:] + hist[:tonic], profiles[0 if mode == "major" else 1])


def estimate_key(events: Iterable) -> Optional[Key]:
    """The best-fitting major or minor key for some notes (objects with ``pitch`` and
    ``duration``); ``None`` with no notes.

    The notes' duration-weighted pitch-class histogram is correlated with a key profile
    in all 24 keys (the Krumhansl-Schmuckler method). The key signature comes from
    Temperley's profile; between that key and its relative (C major or A minor),
    Krumhansl & Kessler's decides. Measured on songs with known keys: the key was
    right for 88% of 1,034 Nottingham folk tunes and 91% of 709 single-key POP909 pop
    songs, and the key signature, which is all that spelling depends on, for 93% and
    99%. (This pairing was the best of a handful tried on those same two sets, so
    expect a little less elsewhere.) A piece that changes key gets one key."""
    hist = [0.0] * 12
    for e in events:
        hist[e.pitch % 12] += max(getattr(e, "duration", 1.0) or 0.0, 0.05)
    if not any(hist):
        return None
    keys = [(t, m) for t in range(12) for m in ("major", "minor")]
    tonic, mode = max(keys, key=lambda k: _fit(hist, k[0], k[1], _TKP))
    relative = ((tonic + 9) % 12, "minor") if mode == "major" else ((tonic + 3) % 12, "major")
    tonic, mode = max(((tonic, mode), relative), key=lambda k: _fit(hist, k[0], k[1], _KK))
    return key_on(tonic, mode)


def song_key(song) -> Tuple[Optional[Key], str]:
    """The key a song's names are spelled in, and where it came from: the song's own
    (set by ``--key`` or read from the file), else an estimate from its notes.

    A MIDI file's C major is the exception (``DOUBTED``): sequencers write it by
    default, and it is usually wrong (of 112 POP909 files that declare a key, all say C
    major, and 10 are in it). So it is kept only if the notes agree."""
    key = getattr(song, "key", None)
    doubted = getattr(song, "key_source", "") == DOUBTED
    if key is not None and not doubted:
        return key, song.key_source or FROM_FILE
    estimate = estimate_key(e for t in song.tracks for e in t.events)
    if doubted:
        if estimate is None or estimate == key:
            return key, FROM_FILE
        return estimate, f"{ESTIMATED}; the file's own {key.name} looks like a default"
    return (estimate, ESTIMATED) if estimate else (None, "")


def spell_free(pc: int, minor: bool = False) -> str:
    """A chord root's spelling with no key to go by: the spelling whose own key, major
    (or minor, for a minor chord), has fewer sharps or flats; ties go to the sharp.
    So Bb, Eb, Ab and Db, but F#; C#m, F#m, G#m and D#m, but Bbm."""
    centre = 3 if minor else 0
    return note_name(min(_positions(pc, *_PLAIN), key=lambda p: (abs(p - centre), -p)))
