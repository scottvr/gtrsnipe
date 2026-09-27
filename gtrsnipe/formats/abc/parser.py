"""ABC notation -> Song.

Reads the FIRST tune in the text (up to the next ``X:`` line) and handles what ABC
in the wild actually uses:

- the key signature (``K:``), including modes (``Dmix``, ``Ador``, ``E minor``),
  explicit accidentals (``K:D exp ^c``), ``HP``/``Hp`` and ``none``;
- accidentals (``^ ^^ _ __ =``), carried through the bar as the ABC version says
  (see ``AbcParser.parse``; ``%%propagate-accidentals`` is honored);
- ties (``C2-C2``, and the detached ``C2 -C2`` legacy files use), broken rhythm (``A>B``, ``A<B``, ``A>>B``), tuplets (``(3abc``,
  ``(p:q:r``), chords (``[CEG]2``), rests (``z``, ``x``), multi-bar rests (``Z4``);
- field lines and inline fields that change the key, unit length or meter
  mid-tune (``K:``, ``L:``, ``M:``; ``[K:G]``);

and skips what isn't music: chord symbols and annotations in quotes, decorations
(``!trill!``, ``+fermata+``, ``~ . H`` ...), grace notes ``{...}``, comments, and
other field lines (lyrics ``w:``, ``W:``, ``P:``, ``T:`` ...). A multi-voice tune
yields its first voice only. Repeats are read as written (not expanded).

Pitch convention: ``C`` is middle C (MIDI 60), ``c`` is C5; ``'`` raises and ``,``
lowers an octave. Time is in beats (quarter notes).
"""
import re
from typing import Dict, List, Optional, Tuple

from ...core.types import MusicalEvent, Song, Track

_LETTER_PC = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
_TONIC_FIFTHS = {"C": 0, "G": 1, "D": 2, "A": 3, "E": 4, "B": 5, "F": -1}
_MODE_FIFTHS = {"maj": 0, "ion": 0, "mix": -1, "dor": -2, "min": -3, "aeo": -3,
                "phr": -4, "loc": -5, "lyd": 1}
_SHARPS, _FLATS = "FCGDAEB", "BEADGCF"
_ACC = {"^^": 2, "^": 1, "=": 0, "_": -1, "__": -2}

_FIELD_LINE = re.compile(r"^([A-Za-z]):(.*)$")
_NOTE = r"(\^\^|\^|__|_|=)?([A-Ga-g])([,']*)(\d*/*\d*)(-?)"
_NOTE_RE = re.compile(_NOTE)
_TOKEN = re.compile(r"""
    (?P<ws>\s+|\\)
  | (?P<quote>"[^"]*"?)                                   # chord symbol / annotation
  | (?P<deco>![^!]*!|\+[^+]*\+)                           # decorations
  | (?P<grace>\{[^}]*\}?)                                 # grace notes
  | (?P<inline>\[[A-Za-z]:[^\]]*\])                       # inline field
  | (?P<bar>::|:*\[?\|+\]?:*[\d,\-]*|\[\d+[\d,\-]*)        # bar lines, repeats, endings
  | (?P<chord>\[(?P<cbody>[^\]\[|]*)\](?P<clen>\d*/*\d*)(?P<ctie>-?))
  | (?P<note>""" + _NOTE + r""")
  | (?P<rest>[zx](?P<rlen>\d*/*\d*))
  | (?P<mrest>Z(?P<mlen>\d*))
  | (?P<broken>>+|<+)
  | (?P<tuplet>\((?P<tp>\d)(?::(?P<tq>\d*))?(?::(?P<tr>\d*))?)
  | (?P<tie>-)                                            # a tie written apart ("B3 -B2")
  | (?P<other>.)
""", re.VERBOSE)


def key_accidentals(value: str) -> Dict[str, int]:
    """Letter -> semitone offset implied by a ``K:`` field value."""
    toks = [t for t in value.split() if "=" not in t or t.startswith("=")]  # drop clef=...
    acc: Dict[str, int] = {}
    if not toks:
        return acc
    head, rest = toks[0], toks[1:]
    if head == "Hp":                                    # Highland pipes, written with F# C#
        acc = {"F": 1, "C": 1}
    m = re.match(r"^([A-Ga-g])([#b]?)(.*)$", head)
    if m and head not in ("HP", "Hp"):
        mode = m.group(3).lower()
        if not mode and rest and rest[0][:3].lower() in _MODE_FIFTHS.keys() | {"m", "maj", "min"}:
            mode = rest.pop(0).lower()
        mode_key = "maj" if mode in ("", "major") else "min" if mode in ("m", "minor") else mode[:3]
        fifths = (_TONIC_FIFTHS[m.group(1).upper()] + {"#": 7, "b": -7}.get(m.group(2), 0)
                  + _MODE_FIFTHS.get(mode_key, 0))
        for i in range(abs(fifths)):
            letter = (_SHARPS if fifths > 0 else _FLATS)[i % 7]
            acc[letter] = acc.get(letter, 0) + (1 if fifths > 0 else -1)
    for t in rest:
        if t.lower() == "exp":                          # the listed accidentals ARE the key
            acc = {}
            continue
        am = re.fullmatch(r"(\^\^|\^|__|_|=)([A-Ga-g])", t)
        if am:
            acc[am.group(2).upper()] = _ACC[am.group(1)]
    return acc


def _slot(letter: str, octs: str) -> Tuple[str, int]:
    """(letter, octave) of a note -- what a tie continues."""
    return letter.upper(), (72 if letter.islower() else 60) + 12 * (octs.count("'") - octs.count(","))


def _length(s: str) -> float:
    """An ABC length suffix (``2``, ``/``, ``//``, ``3/2``, ``/4``) as a multiple
    of the unit note length."""
    if not s:
        return 1.0
    m = re.fullmatch(r"(\d*)(/*)(\d*)", s)
    num = int(m.group(1)) if m.group(1) else 1
    if not m.group(2):
        return float(num)
    den = int(m.group(3)) if m.group(3) else 2 ** len(m.group(2))
    return num / den if den else float(num)


def _meter(value: str) -> Optional[Tuple[int, int]]:
    v = value.strip()
    if v == "C":
        return 4, 4
    if v == "C|":
        return 2, 2
    m = re.match(r"\(?([\d+]+)\)?\s*/\s*(\d+)", v)
    if not m:
        return None
    return sum(int(x) for x in m.group(1).split("+") if x), int(m.group(2))


class AbcParser:
    @staticmethod
    def parse(abc_string: str, propagate_accidentals: Optional[str] = None) -> Song:
        """``propagate_accidentals``: how far an accidental carries within its bar --
        'not' (that note only), 'octave' (same letter and octave) or 'pitch' (same
        letter, any octave). By default it follows the ABC version, as music21
        does: before 2.0 (including files with no ``%abc-x.y`` line, i.e. most
        legacy collections) an accidental affects only its own note; from 2.0 on
        it carries to the same letter for the rest of the bar ('pitch', the 2.1
        default) unless a ``%%propagate-accidentals`` directive says otherwise."""
        song = Song()
        track = Track()
        st = _State()
        if propagate_accidentals is None:
            ver = re.search(r"%abc-(\d+)\.(\d+)", abc_string)
            propagate_accidentals = "pitch" if ver and int(ver.group(1)) >= 2 else "not"
        st.propagate = propagate_accidentals

        lines = abc_string.splitlines()
        has_key = any(_FIELD_LINE.match(ln) and ln[0] == "K" for ln in lines)
        in_body = not has_key                           # no K: at all -> everything is body
        seen_tune = False
        for raw in lines:
            directive = re.match(r"\s*%%propagate-accidentals\s+(not|octave|pitch)\b", raw)
            if directive:
                st.propagate = directive.group(1)
                continue
            line = re.sub(r"(?<!\\)%.*", "", raw)       # comments
            field = _FIELD_LINE.match(line)
            if field and not re.match(r"^[A-Ga-g]:[|:]", line):
                name, value = field.group(1), field.group(2).strip()
                if name == "X":
                    if seen_tune and in_body:
                        break                            # the next tune starts here
                    seen_tune = True
                    continue
                if name == "T" and song.title == "Untitled" and value:
                    song.title = value
                st.field(name, value, song)
                if name == "K" and not in_body:
                    in_body = True
                continue
            if in_body:
                st.music(line, track)
        st.finish()
        song.tracks.append(track)
        return song

    # -- kept for callers (the ABC generator) ---------------------------------
    @staticmethod
    def _abc_note_to_midi(note_str: str) -> Optional[int]:
        """An ABC note (e.g. ``^C``, ``g'``) as a MIDI pitch, ignoring any key."""
        m = _NOTE_RE.fullmatch(note_str)
        if not m:
            return None
        acc, letter, octs = m.group(1), m.group(2), m.group(3)
        base = 72 if letter.islower() else 60
        return (base + _LETTER_PC[letter.upper()] + (_ACC[acc] if acc else 0)
                + 12 * (octs.count("'") - octs.count(",")))

    @staticmethod
    def _abc_duration_to_beats(duration_str: str) -> float:
        """Converts an ABC duration string (e.g., 2, /2, 3/2) to a float multiplier."""
        if not duration_str:
            return 1.0
        try:
            if "/" in duration_str:
                if duration_str.startswith("/"):
                    return 1 / float(duration_str[1:])
                num, den = duration_str.split("/")
                return float(num) / float(den)
            return float(duration_str)
        except (ValueError, ZeroDivisionError):
            return 1.0


class _State:
    """Everything that carries across tokens while reading a tune body."""

    def __init__(self):
        self.time = 0.0                  # beats
        self.meter: Optional[Tuple[int, int]] = None
        self.unit: Optional[float] = None  # beats per unit note length (L:)
        self.key: Dict[str, int] = {}
        self.bar: Dict[Tuple[str, int], int] = {}   # accidentals until the bar line
        self.ties: Dict[int, MusicalEvent] = {}      # pitch -> note a tie continues
        self.tie_slots: Dict[Tuple[str, int], int] = {}  # (letter, octave) -> tied pitch
        self.last_slots: Dict[Tuple[str, int], int] = {}  # slots of the last group
        self.last: Tuple[List[MusicalEvent], float] = ([], 0.0)  # for broken rhythm
        self.next_mult = 1.0             # broken rhythm owed to the next note
        self.tuplet = (1.0, 0)           # (time factor, notes left)
        self.voice: Optional[str] = None
        self.first_voice: Optional[str] = None
        self.propagate = "not"            # not | octave | pitch (see AbcParser.parse)

    # -- fields --------------------------------------------------------------
    def field(self, name: str, value: str, song: Song) -> None:
        if name == "M":
            self.meter = _meter(value)
            if self.meter:
                song.time_signature = f"{self.meter[0]}/{self.meter[1]}"
        elif name == "L":
            m = re.match(r"(\d+)\s*/\s*(\d+)", value)
            if m and int(m.group(2)):
                self.unit = 4.0 * int(m.group(1)) / int(m.group(2))
        elif name == "Q":
            m = re.search(r"=\s*(\d+(?:\.\d+)?)", value) or re.match(r"\s*(\d+(?:\.\d+)?)", value)
            if m:
                song.tempo = float(m.group(1))
        elif name == "K":
            self.key = key_accidentals(value)
        elif name == "V":
            vid = value.split()[0] if value.split() else ""
            if self.first_voice is None:
                self.first_voice = vid
            self.voice = vid

    def _unit(self) -> float:
        if self.unit is None:            # ABC default: 1/16 if the meter is < 3/4, else 1/8
            short = self.meter is not None and self.meter[0] / self.meter[1] < 0.75
            self.unit = 0.25 if short else 0.5
        return self.unit

    def _active(self) -> bool:
        return self.first_voice is None or self.voice == self.first_voice

    # -- music ---------------------------------------------------------------
    def _pitch(self, acc: str, letter: str, octs: str) -> int:
        octave = (72 if letter.islower() else 60) + 12 * (octs.count("'") - octs.count(","))
        name = letter.upper()
        if not acc and (name, octave) in self.tie_slots:
            return self.tie_slots[(name, octave)]        # a tied note keeps its accidental
        slot = (name, octave if self.propagate == "octave" else 0)
        if acc:
            off = _ACC[acc]
            if self.propagate != "not":
                self.bar[slot] = off
        else:
            off = self.bar.get(slot, self.key.get(name, 0))
        return octave + _LETTER_PC[name] + off

    def _duration(self, length: float) -> float:
        mult = length * self.next_mult
        self.next_mult = 1.0
        factor, left = self.tuplet
        if left > 0:
            mult *= factor
            self.tuplet = (factor, left - 1)
        return mult * self._unit()

    def _group(self, notes: List[Tuple[int, bool, Tuple[str, int]]], length: float,
               track: Track) -> None:
        dur = self._duration(length)
        group, ties, slots = [], {}, {}
        for pitch, tie, slot in notes:
            slots[slot] = pitch
            if pitch in self.ties:           # a tie carries this note on: no new onset
                ev = self.ties[pitch]
                ev.duration += dur
            else:
                ev = MusicalEvent(time=self.time, pitch=pitch, duration=dur, velocity=90)
                track.events.append(ev)
            group.append(ev)
            if tie:
                ties[pitch] = ev
        self.ties = ties
        self.tie_slots = {sl: p for sl, p in slots.items() if p in ties}
        self.last_slots = slots
        self.last = (group, dur)
        self.time += dur

    def _broken(self, symbol: str) -> None:
        n = len(symbol)
        short = 2.0 ** -n
        group, dur = self.last
        long_mult, next_mult = (2 - short, short) if symbol[0] == ">" else (short, 2 - short)
        delta = dur * (long_mult - 1)
        for ev in group:
            ev.duration += delta
        self.time += delta
        self.last = (group, dur + delta)
        self.next_mult = next_mult

    def music(self, line: str, track: Track) -> None:
        for m in _TOKEN.finditer(line):
            kind = m.lastgroup
            if kind == "inline":
                name, value = m.group("inline")[1], m.group("inline")[3:-1]
                self.field(name, value.strip(), _NoSong())
                continue
            if not self._active() or kind in ("ws", "quote", "deco", "grace", "other"):
                continue
            if kind == "bar":
                self.bar.clear()
            elif kind == "note":
                acc, letter, octs, length, tie = _NOTE_RE.fullmatch(m.group("note")).groups()
                self._group([(self._pitch(acc, letter, octs), tie == "-", _slot(letter, octs))],
                            _length(length), track)
            elif kind == "chord":
                inner = list(_NOTE_RE.finditer(m.group("cbody")))
                if not inner:
                    continue
                notes = [(self._pitch(n.group(1), n.group(2), n.group(3)),
                          n.group(5) == "-" or m.group("ctie") == "-",
                          _slot(n.group(2), n.group(3))) for n in inner]
                length = _length(inner[0].group(4)) * _length(m.group("clen"))
                self._group(notes, length, track)
            elif kind == "rest":
                dur = self._duration(_length(m.group("rlen")))
                self.ties, self.tie_slots, self.last_slots = {}, {}, {}
                self.last = ([], dur)
                self.time += dur
            elif kind == "mrest":
                bars = int(m.group("mlen")) if m.group("mlen") else 1
                num, den = self.meter or (4, 4)
                self.time += bars * 4.0 * num / den
                self.ties, self.tie_slots, self.last_slots, self.last = {}, {}, {}, ([], 0.0)
            elif kind == "broken":
                self._broken(m.group("broken"))
            elif kind == "tie":                  # ties the preceding note or chord
                self.ties = {ev.pitch: ev for ev in self.last[0]}
                self.tie_slots = dict(self.last_slots)
            elif kind == "tuplet":
                p = int(m.group("tp"))
                compound = self.meter is not None and self.meter[0] % 3 == 0 and self.meter[0] > 3
                q_default = 3 if p in (2, 4, 8) else 2 if p in (3, 6) else (3 if compound else 2)
                q = int(m.group("tq")) if m.group("tq") else q_default
                r = int(m.group("tr")) if m.group("tr") else p
                self.tuplet = (q / p, r)

    def finish(self) -> None:
        self.ties = {}


class _NoSong:
    """Inline fields may change the key/length/meter but not song metadata."""
    title = "Untitled"
    tempo = 120.0
    time_signature = "4/4"
