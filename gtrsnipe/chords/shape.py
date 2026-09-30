"""Name the chord a fret shape plays (``gtrsnipe --name-chord x,3,2,0,1,0``).

A shape lists one fret per string, lowest string first (the order of chord charts
and of ``--tuning-pitches``), with ``x`` for a muted string. The sounding pitches
come from the tuning (and any capo), so the same shape names different chords in
different tunings. Naming is :func:`gtrsnipe.core.chords.identify`, as in chord
charts and ``--name-chords``.
"""
from dataclasses import dataclass
from typing import List, Optional, Sequence

from ..core.chords import PITCH_CLASS_NAMES, Chord, identify
from ..core.theory import note_name_to_pitch


@dataclass
class NamedShape:
    shape: str
    frets: List[Optional[int]]      # per string, low to high; None = muted
    pitches: List[int]              # sounding MIDI pitches, low string first
    chord: Optional[Chord]

    @property
    def label(self) -> str:
        return self.chord.name if self.chord else "no chord"


def parse_shape(shape: str, num_strings: int) -> List[Optional[int]]:
    """``"x,3,2,0,1,0"`` or ``"x32010"`` -> frets low to high (None = muted).

    The compact form is accepted only when it has exactly one character per string,
    so a two-digit fret always needs commas."""
    text = shape.strip()
    if "," in text:
        parts = [p.strip() for p in text.split(",")]
    elif len(text) == num_strings:
        parts = list(text)
    else:
        raise ValueError(f"shape {shape!r}: use commas (e.g. x,3,2,0,1,0), or one character "
                         f"per string for all {num_strings} strings")
    if len(parts) != num_strings:
        raise ValueError(f"shape {shape!r} has {len(parts)} strings; the tuning has "
                         f"{num_strings} (list them lowest first, x for muted)")
    frets: List[Optional[int]] = []
    for p in parts:
        if p.lower() == "x":
            frets.append(None)
        elif p.isdigit():
            frets.append(int(p))
        else:
            raise ValueError(f"shape {shape!r}: {p!r} is not a fret number or x")
    if all(f is None for f in frets):
        raise ValueError(f"shape {shape!r}: every string is muted")
    return frets


def name_shape(shape: str, open_pitches: Sequence[int], capo: int = 0) -> NamedShape:
    """Name ``shape`` on strings tuned to ``open_pitches`` (MIDI, low to high); a
    capo raises every string, and frets count from it."""
    frets = parse_shape(shape, len(open_pitches))
    pitches = [o + capo + f for o, f in zip(open_pitches, frets) if f is not None]
    chord = identify(pitches, bass=min(pitches))
    return NamedShape(shape, frets, pitches, chord)


def run_name_chord(args) -> int:
    """CLI entry for ``--name-chord`` (repeatable). Prints one line per shape."""
    from ..arguments import resolve_custom_tuning, resolve_named_tuning
    custom = resolve_custom_tuning(args)
    try:
        if custom:
            label, names = "custom", list(custom)
        else:
            label, _ = resolve_named_tuning(args.tuning, args.num_strings, args.bass)
            from ..core.types import Tuning
            names = list(Tuning[label].value)
    except (ValueError, KeyError) as e:
        print(f"Error: {e}")
        return 1
    opens = [note_name_to_pitch(n) for n in names]
    capo = args.capo or 0
    where = f"{label} ({','.join(names)})" + (f", capo {capo}" if capo else "")
    naming = None
    if getattr(args, "shape_names", False):
        from .shape_names import shape_naming
        naming = shape_naming(names, capo, label if label != "custom" else "this tuning")
    status = 0
    for shape in args.name_chord:
        try:
            named = name_shape(shape, opens, capo)
        except ValueError as e:
            print(f"Error: {e}")
            status = 1
            continue
        # spelled with the chord names' sharps, so "E" doesn't sit next to "Ab4"
        notes = " ".join(f"{PITCH_CLASS_NAMES[p % 12]}{p // 12 - 1}" for p in named.pitches)
        shape_col = f"  shape: {naming.name(named.chord)}" if naming and naming.active else ""
        print(f"{shape:<16} {named.label:<10} {notes}{shape_col}")
    print(f"(tuning {where}; chord names are concert pitch)")
    if naming:
        print(f"({naming.banner})")
    return status
