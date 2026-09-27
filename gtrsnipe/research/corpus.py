"""Melody corpora in one format (backlog R01).

Every corpus is read into ``Melody`` records: one monophonic line per tune, with
onsets and durations as integer ticks (``TPQ`` per quarter note) so rhythms
compare exactly. A corpus is read once and cached as gzipped JSON lines (one
file, since the data volume is slow with many small files); analyses read the
cache.

How each source becomes a line:

- **kern** (Essen): the first ``**kern`` spine, read natively (music21 drops
  the ``{``/``}`` phrase marks, which Essen has and the analyses want). Ties are
  merged, grace notes skipped; a chord keeps its top note.
- **ABC** (Nottingham): every tune in each file, through gtrsnipe's ABC parser
  (validated against music21 in v0.6.1). Chords keep their top note.
- **MIDI** (POP909, Lakh): a part named like a melody (``MELODY``, ``Vocal``,
  ``Voice``...; backing vocals excluded) if there is one, else the skyline of
  every non-drum part (the highest note at each onset: Uitdenbogerd & Zobel's
  "all-mono" baseline). Either way, a note is cut off at the next onset, which
  removes POP909's legato overlaps. ``Melody.source`` records which rule applied.

Data lives outside the repo: pass ``root`` (the folder holding ``essen/``,
``nottingham/``, ``pop909/``, ``lakh/``...) or set ``GTRSNIPE_CORPUS_ROOT``.
"""
from __future__ import annotations

import csv
import gzip
import io
import json
import os
import re
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, dataclass, field
from datetime import date
from fractions import Fraction
from functools import lru_cache
from typing import Callable, Dict, Iterator, List, Optional, Sequence, Tuple

TPQ = 960                     # ticks per quarter note (divisible by 2^6, 3 and 5)
CACHE_FORMAT = "gtrsnipe-melodies"
CACHE_VERSION = 1
ROOT_ENV = "GTRSNIPE_CORPUS_ROOT"

_PC = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


@dataclass
class Melody:
    """One tune as a monophonic line. ``onsets``/``durations`` are ticks
    (``TPQ`` per quarter note) from the first note; ``phrases`` holds the
    indices of notes that begin a phrase, when the source marks phrases."""
    id: str
    corpus: str
    pitches: List[int]
    onsets: List[int]
    durations: List[int]
    title: str = ""
    artist: str = ""
    meter: str = ""
    key: str = ""
    source: str = ""
    family: str = ""          # tune-family label, where the corpus has one (MTC)
    phrases: List[int] = field(default_factory=list)
    dropped: int = 0          # simultaneous notes removed to make the line monophonic

    def __len__(self) -> int:
        return len(self.pitches)

    @property
    def ref(self) -> str:
        return f"{self.corpus}:{self.id}"

    def phrase_spans(self) -> List[Tuple[int, int]]:
        """(start, end) note-index spans, end exclusive; one span if unmarked."""
        starts = sorted(set([0] + [p for p in self.phrases if 0 < p < len(self)]))
        return list(zip(starts, starts[1:] + [len(self)]))

    def slice(self, start: int, end: int) -> "Melody":
        """Notes ``start:end`` (0-based, end exclusive), re-based to time 0."""
        if not 0 <= start < end <= len(self):
            raise ValueError(f"{self.ref}: notes {start}-{end} outside 0-{len(self)}")
        t0 = self.onsets[start]
        return Melody(self.id + f"@{start}-{end}", self.corpus, self.pitches[start:end],
                      [t - t0 for t in self.onsets[start:end]], self.durations[start:end],
                      self.title, self.artist, self.meter, self.key, self.source,
                      self.family, [p - start for p in self.phrases if start <= p < end])

    def to_song(self):
        """As a gtrsnipe Song (beats = quarter notes), e.g. for --homograph analysis."""
        from ..core.types import MusicalEvent, Song, Track
        events = [MusicalEvent(t / TPQ, p, d / TPQ, 90)
                  for p, t, d in zip(self.pitches, self.onsets, self.durations)]
        return Song(tracks=[Track(events=events)], title=self.title or self.id,
                    time_signature=self.meter or "4/4")

    def to_json(self) -> str:
        return json.dumps(asdict(self), separators=(",", ":"), ensure_ascii=False)

    @classmethod
    def from_dict(cls, d: dict) -> "Melody":
        return cls(**d)


def _line(corpus: str, id_: str, notes: Sequence[Tuple[int, int, int]], **meta) -> Melody:
    """A Melody from (onset, duration, pitch) ticks, re-based to the first onset."""
    t0 = notes[0][0] if notes else 0
    return Melody(id_, corpus, [p for _, _, p in notes], [t - t0 for t, _, _ in notes],
                  [d for _, d, _ in notes], **meta)


def skyline(notes: Sequence[Tuple[int, int, int]]) -> Tuple[List[Tuple[int, int, int]], int]:
    """(onset, end, pitch) notes -> a monophonic (onset, duration, pitch) line:
    the highest note at each onset, cut off at the next onset. Returns the line
    and how many notes were dropped."""
    top: Dict[int, Tuple[int, int]] = {}
    for on, end, p in notes:
        if on not in top or (p, end) > (top[on][1], top[on][0]):
            top[on] = (end, p)
    ons = sorted(top)
    line = []
    for i, on in enumerate(ons):
        end, p = top[on]
        if i + 1 < len(ons):
            end = min(end, ons[i + 1])
        line.append((on, max(1, end - on), p))
    return line, len(notes) - len(line)


# -- kern ---------------------------------------------------------------------------

_KERN_DUR = re.compile(r"(\d+)(?:%(\d+))?(\.*)")
_KERN_PITCH = re.compile(r"([a-gA-G])\1*")


def _kern_ticks(tok: str) -> Optional[int]:
    m = _KERN_DUR.search(tok)
    if not m:
        return None
    digits, den, dots = m.group(1), int(m.group(2) or 1), len(m.group(3))
    if set(digits) == {"0"}:                   # 0 = breve, 00 = longa, 000 = maxima
        q = Fraction(8 * 2 ** (len(digits) - 1))
    else:
        q = Fraction(4 * den, int(digits))
    return round(q * (2 - Fraction(1, 2 ** dots)) * TPQ)


def _kern_pitch(tok: str) -> Optional[int]:
    m = _KERN_PITCH.search(tok)
    if not m:
        return None
    letters = m.group(0)
    octave = 3 + len(letters) if letters[0].islower() else 4 - len(letters)
    acc = tok.count("#") - tok.count("-")
    return 12 * (octave + 1) + _PC[letters[0].upper()] + acc


def parse_kern(text: str, corpus: str = "", id_: str = "") -> Melody:
    """The first **kern spine of a Humdrum file as a monophonic line."""
    meta = {"title": "", "meter": "", "key": ""}
    col: Optional[int] = None
    t = 0
    notes: List[List[int]] = []                # [onset, duration, pitch]
    phrases: List[int] = []
    phrase_pending = False
    tie_open: Optional[int] = None             # index of the note a tie continues
    dropped = 0
    for raw in text.splitlines():
        line = raw.rstrip("\r\n")
        if not line:
            continue
        if line.startswith("!!!"):
            k, _, v = line[3:].partition(":")
            if k.strip() == "OTL" and not meta["title"]:
                meta["title"] = v.strip()
            continue
        if line.startswith("!"):
            continue
        cells = line.split("\t")
        if col is None:
            if line.startswith("**"):
                col = next((i for i, c in enumerate(cells) if c == "**kern"), None)
            continue
        if col >= len(cells):
            continue
        tok = cells[col]
        if tok.startswith("*"):
            m = re.match(r"\*M(\d+)/(\d+)$", tok)
            if m and not meta["meter"]:
                meta["meter"] = f"{m.group(1)}/{m.group(2)}"
            m = re.match(r"\*([A-Ga-g])([#-]*):$", tok)
            if m and not meta["key"]:
                meta["key"] = (m.group(1).upper() + m.group(2).replace("-", "b")
                               + ("m" if m.group(1).islower() else ""))
            continue
        if tok.startswith("=") or tok == ".":
            continue
        if "{" in tok:
            phrase_pending = True                 # the next sounding note starts a phrase
        subs = [s for s in tok.split(" ") if s and s != "."]
        if not subs or any(c in s for s in subs for c in "qQ"):
            continue                              # grace notes take no time
        durs = [d for d in (_kern_ticks(s) for s in subs) if d is not None]
        if not durs:
            continue
        step = min(durs)
        sounding = [(s, _kern_pitch(s), _kern_ticks(s)) for s in subs if "r" not in s]
        sounding = [x for x in sounding if x[1] is not None and x[2] is not None]
        if sounding:
            s, p, d = max(sounding, key=lambda x: x[1])
            dropped += len(sounding) - 1
            continues = ("_" in s or "]" in s) and tie_open is not None \
                and notes[tie_open][2] == p
            if continues:
                notes[tie_open][1] += d
            else:
                if phrase_pending:
                    phrases.append(len(notes))
                    phrase_pending = False
                notes.append([t, d, p])
            if "[" in s:
                tie_open = len(notes) - 1
            elif "]" in s:
                tie_open = None
        t += step
    return _line(corpus, id_, [tuple(n) for n in notes], source="kern",
                 phrases=phrases, dropped=dropped, **meta)


def read_kern_file(path: str, rel: str, corpus: str) -> List[Melody]:
    with open(path, encoding="utf-8", errors="replace") as f:
        return [parse_kern(f.read(), corpus, _stem_id(rel))]


@lru_cache(maxsize=4)
def _mtc_families(metadata_dir: str) -> Dict[str, str]:
    """songid -> tune family, from an MTC collection's metadata folder."""
    for name, col in (("MTC-ANN-tune-family-labels.csv", "tunefamily"),
                      ("MTC-FS-INST-2.0.csv", "tunefamily_id")):
        path = os.path.join(metadata_dir, name)
        if not os.path.exists(path):
            continue
        fields_path = path.replace(".csv", "-fieldnames.csv")
        with open(fields_path, encoding="utf-8") as f:
            fields = next(csv.reader(f))
        with open(path, encoding="utf-8") as f:
            return {row[0]: row[fields.index(col)] for row in csv.reader(f)
                    if len(row) == len(fields)}
    return {}


def read_mtc_file(path: str, rel: str, corpus: str) -> List[Melody]:
    """A Meertens Tune Collections kern file, labelled with its tune family."""
    (m,) = read_kern_file(path, rel, corpus)
    fam = _mtc_families(os.path.join(os.path.dirname(os.path.dirname(path)), "metadata"))
    m.family = fam.get(_stem_id(os.path.basename(rel)), "")
    return [m]


# -- ABC ----------------------------------------------------------------------------

def split_abc(text: str) -> Tuple[List[str], List[List[str]]]:
    """(file header lines, [tune lines]) -- a tune runs from its ``X:`` line."""
    header: List[str] = []
    tunes: List[List[str]] = []
    for line in text.splitlines():
        if re.match(r"^X:", line):
            tunes.append([line])
        elif tunes:
            tunes[-1].append(line)
        else:
            header.append(line)
    return header, tunes


def read_abc_file(path: str, rel: str, corpus: str) -> List[Melody]:
    from ..formats.abc.parser import AbcParser
    with open(path, encoding="utf-8", errors="replace") as f:
        header, tunes = split_abc(f.read())
    out, seen = [], defaultdict(int)
    for tune in tunes:
        x = tune[0][2:].strip() or "?"
        seen[x] += 1
        id_ = f"{_stem_id(rel)}#{x}" + (f".{seen[x]}" if seen[x] > 1 else "")
        song = AbcParser.parse("\n".join(header + tune))
        evs = [e for tr in song.tracks for e in tr.events]
        if not evs:
            continue
        notes = [(round(e.time * TPQ), round((e.time + e.duration) * TPQ), e.pitch) for e in evs]
        line, dropped = skyline(notes)
        key = next((ln[2:].strip() for ln in tune if ln.startswith("K:")), "")
        out.append(_line(corpus, id_, line, title=song.title if song.title != "Untitled" else "",
                         meter=song.time_signature, key=key.split()[0] if key else "",
                         source="abc", dropped=dropped))
    return out


# -- MIDI ---------------------------------------------------------------------------

MELODY_NAME = re.compile(r"melod|vocal|voice|\bvox\b|singer|\bsing\b|\blead\s*v|canto|stimme",
                         re.I)
BACKING_NAME = re.compile(r"back|harmon|choir|chorus|\bbgv?\b|\bbv\b|2nd|second", re.I)


@dataclass
class MidiPart:
    track: int
    channel: int
    name: str
    notes: List[Tuple[int, int, int]]          # (onset, end, pitch) in file ticks

    @property
    def drums(self) -> bool:
        return self.channel == 9


def midi_parts(path: str) -> Tuple[List[MidiPart], int, str, str]:
    """Every (track, channel) with notes. Returns (parts, ticks per beat, first
    meter, first key). Reads RIFF-wrapped files and clips bad data bytes."""
    import mido
    from ..formats.mid.reader import MidiReader
    smf = MidiReader._read_smf(path)
    try:
        mf = mido.MidiFile(file=io.BytesIO(smf))
    except Exception:
        mf = mido.MidiFile(file=io.BytesIO(smf), clip=True)
    meter = key = ""
    parts: List[MidiPart] = []
    for ti, trk in enumerate(mf.tracks):
        name, tick = "", 0
        held: Dict[Tuple[int, int], List[int]] = defaultdict(list)
        by_ch: Dict[int, List[Tuple[int, int, int]]] = defaultdict(list)
        for msg in trk:
            tick += msg.time
            if msg.is_meta:
                if msg.type == "track_name" and not name:
                    name = str(msg.name).strip()
                elif msg.type == "time_signature" and not meter:
                    meter = f"{msg.numerator}/{msg.denominator}"
                elif msg.type == "key_signature" and not key:
                    key = msg.key
                continue
            if msg.type == "note_on" and msg.velocity > 0:
                held[(msg.channel, msg.note)].append(tick)
            elif msg.type in ("note_on", "note_off"):
                q = held.get((msg.channel, msg.note))
                if q:
                    on = q.pop(0)
                    by_ch[msg.channel].append((on, max(tick, on + 1), msg.note))
        for (ch, p), ons in held.items():         # never released: end at track end
            by_ch[ch].extend((on, max(tick, on + 1), p) for on in ons)
        for ch in sorted(by_ch):
            label = name if len(by_ch) == 1 else f"{name} ch{ch + 1}".strip()
            parts.append(MidiPart(ti, ch, label, sorted(by_ch[ch])))
    return parts, (mf.ticks_per_beat or 480), meter, key


def pick_melody(parts: Sequence[MidiPart]) -> Tuple[List[Tuple[int, int, int]], str]:
    """The melody notes and how they were chosen (see the module docstring)."""
    named = [p for p in parts if not p.drums and MELODY_NAME.search(p.name)
             and not BACKING_NAME.search(p.name)]
    if named:
        best = max(named, key=lambda p: ("melod" in p.name.lower(), len(p.notes)))
        return best.notes, f"midi:track {best.name}"
    pitched = [n for p in parts if not p.drums for n in p.notes]
    return pitched, "midi:skyline"


def read_midi_file(path: str, rel: str, corpus: str) -> List[Melody]:
    parts, tpb, meter, key = midi_parts(path)
    notes, how = pick_melody(parts)
    if not notes:
        return []
    scaled = [(round(on * TPQ / tpb), round(end * TPQ / tpb), p) for on, end, p in notes]
    line, dropped = skyline(scaled)
    artist, title = "", os.path.splitext(os.path.basename(rel))[0]
    if corpus == "lakh-clean":
        artist = rel.split("/")[0]
    return [_line(corpus, _stem_id(rel), line, title=title, artist=artist, meter=meter,
                  key=key, source=how, dropped=dropped)]


# -- the corpora --------------------------------------------------------------------

@dataclass(frozen=True)
class CorpusSpec:
    name: str
    subdir: str                                # under the corpus root
    suffix: str
    reader: Callable[[str, str, str], List[Melody]]
    about: str
    pattern: Optional[str] = None              # regex the relative path must match


CORPORA: Dict[str, CorpusSpec] = {s.name: s for s in [
    CorpusSpec("essen", "essen", ".krn", read_kern_file,
               "Essen Folksong Collection, Humdrum kern (CCARH): 8,473 tunes, phrase-marked"),
    CorpusSpec("mtc-ann", "mtc/MTC-ANN-2.0.1/krn", ".krn", read_mtc_file,
               "Meertens Tune Collections, annotated (MTC-ANN 2.0.1): 360 Dutch folk "
               "melodies in 26 tune families"),
    CorpusSpec("mtc-fs", "mtc/MTC-FS-INST-2.0/krn", ".krn", read_mtc_file,
               "Meertens Tune Collections, MTC-FS-INST 2.0: 18,109 Dutch folk melodies, "
               "labelled with tune-family ids"),
    CorpusSpec("nottingham", "nottingham/ABC_cleaned", ".abc", read_abc_file,
               "Nottingham Music Database, cleaned ABC (Jukedeck): 1,034 folk tunes"),
    CorpusSpec("pop909", "pop909/POP909", ".mid", read_midi_file,
               "POP909: 909 Chinese pop songs, MELODY track", pattern=r"^\d{3}/\d{3}\.mid$"),
    CorpusSpec("lakh-clean", "lakh/clean_midi", ".mid", read_midi_file,
               "Lakh MIDI, Clean MIDI subset: 17,256 files named Artist/Title"),
    CorpusSpec("lakh-full", "lakh/lmd_full", ".mid", read_midi_file,
               "Lakh MIDI, LMD-full: 178,561 files named by md5"),
]}


def corpus_root(root: Optional[str] = None) -> str:
    root = root or os.environ.get(ROOT_ENV)
    if not root:
        raise ValueError(f"no corpus root: pass --data DIR or set {ROOT_ENV}")
    if not os.path.isdir(root):
        raise ValueError(f"corpus root {root!r} is not a directory")
    return root


def default_cache(name: str, root: Optional[str] = None) -> str:
    return os.path.join(corpus_root(root), "_cache", f"{name}.jsonl.gz")


def _stem_id(rel: str) -> str:
    return os.path.splitext(rel)[0]


def corpus_files(spec: CorpusSpec, root: Optional[str] = None) -> List[Tuple[str, str]]:
    """(path, relative path) of every source file, sorted. Walks with os.walk,
    which (unlike glob) sees names starting with '.', and skips macOS '._' files."""
    base = os.path.join(corpus_root(root), spec.subdir)
    if not os.path.isdir(base):
        raise ValueError(f"{spec.name}: {base} not found")
    pat = re.compile(spec.pattern) if spec.pattern else None
    out = []
    for d, dirs, files in os.walk(base):
        dirs.sort()
        for fn in files:
            if fn.startswith("._") or not fn.lower().endswith(spec.suffix):
                continue
            path = os.path.join(d, fn)
            rel = os.path.relpath(path, base).replace(os.sep, "/")
            if pat is None or pat.match(rel):
                out.append((path, rel))
    return sorted(out, key=lambda x: x[1])


def _read_one(job: Tuple[str, str, str]) -> Tuple[str, List[dict], str]:
    name, path, rel = job
    try:
        mels = CORPORA[name].reader(path, rel, name)
        return rel, [asdict(m) for m in mels if len(m)], ""
    except Exception as e:                     # noqa: BLE001 -- recorded, not fatal
        return rel, [], f"{type(e).__name__}: {e}"


def build(name: str, *, root: Optional[str] = None, out: Optional[str] = None,
          workers: Optional[int] = None, limit: Optional[int] = None,
          progress: Optional[Callable[[int, int], None]] = None) -> dict:
    """Read a whole corpus and write its cache. Returns the header written.

    Melodies stream to disk as they are read (LMD-full does not fit in memory as
    Python lists); the header, which needs the totals, goes in front afterwards
    as its own gzip member -- concatenated members read back as one stream."""
    from importlib.metadata import PackageNotFoundError, version
    spec = CORPORA[name]
    files = corpus_files(spec, root)[:limit] if limit else corpus_files(spec, root)
    out = out or default_cache(name, root)
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    jobs = [(name, p, r) for p, r in files]
    workers = workers or max(1, (os.cpu_count() or 2) - 2)
    errors: List[Tuple[str, str]] = []
    count = 0
    body = out + ".body.part"
    with gzip.open(body, "wt", encoding="utf-8") as f:
        ex = ProcessPoolExecutor(max_workers=workers) if workers > 1 else None
        try:
            it: Iterator = ex.map(_read_one, jobs, chunksize=16) if ex else map(_read_one, jobs)
            for i, (rel, mels, err) in enumerate(it, 1):
                if err:
                    errors.append((rel, err))
                for m in mels:
                    f.write(json.dumps(m, separators=(",", ":"), ensure_ascii=False) + "\n")
                count += len(mels)
                if progress:
                    progress(i, len(jobs))
        finally:
            if ex:
                ex.shutdown()
    try:
        gv = version("gtrsnipe")
    except PackageNotFoundError:
        gv = "unknown"
    header = {"format": CACHE_FORMAT, "version": CACHE_VERSION, "corpus": name,
              "about": spec.about, "tpq": TPQ, "built": date.today().isoformat(),
              "gtrsnipe": gv, "files": len(files), "melodies": count,
              "errors": len(errors), "error_sample": errors[:20]}
    tmp = out + ".part"
    with gzip.open(tmp, "wt", encoding="utf-8") as f:
        f.write(json.dumps(header) + "\n")
    with open(tmp, "ab") as dst, open(body, "rb") as src:
        while chunk := src.read(1 << 20):
            dst.write(chunk)
    os.remove(body)
    os.replace(tmp, out)
    return header


def cache_header(path: str) -> dict:
    with gzip.open(path, "rt", encoding="utf-8") as f:
        header = json.loads(f.readline())
    if header.get("format") != CACHE_FORMAT:
        raise ValueError(f"{path} is not a gtrsnipe melody cache")
    if header.get("version") != CACHE_VERSION or header.get("tpq") != TPQ:
        raise ValueError(f"{path}: cache version {header.get('version')} / tpq "
                         f"{header.get('tpq')} -- rebuild it with this gtrsnipe")
    return header


def iter_cache(path: str) -> Iterator[Melody]:
    """The melodies of a cache file, one at a time (for corpora too big to hold)."""
    cache_header(path)
    with gzip.open(path, "rt", encoding="utf-8") as f:
        f.readline()
        for ln in f:
            if ln.strip():
                yield Melody.from_dict(json.loads(ln))


def read_cache(path: str) -> Tuple[dict, List[Melody]]:
    """(header, melodies) from a cache file written by ``build``."""
    return cache_header(path), list(iter_cache(path))


def find(melodies: Sequence[Melody], query: str) -> Melody:
    """A melody by id: exact, else a unique match of the last path part(s)."""
    exact = [m for m in melodies if m.id == query]
    if exact:
        return exact[0]
    tail = [m for m in melodies if m.id.endswith("/" + query)]
    if len(tail) == 1:
        return tail[0]
    if not tail:
        raise ValueError(f"no melody {query!r}")
    raise ValueError(f"{query!r} is ambiguous: {', '.join(m.id for m in tail[:5])}")
