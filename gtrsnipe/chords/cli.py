"""CLI for the chord-chart output (`gtrsnipe-chords`).

Parses an input file, breaks it into per-measure chords, and writes a Markdown
chord sheet to stdout (or a file with ``-o``).
"""
import argparse
import sys
from pathlib import Path
from typing import Optional, Sequence

from ..core.config import MapperConfig
from .chart import DEFAULT_MEASURES_PER_LINE, build_chord_sheet
from .segment import DEFAULT_CHORD_TONE_THRESHOLD


def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="gtrsnipe-chords",
        description="Break a song into per-measure chords and print a chord sheet.",
    )
    p.add_argument("input", help="Input file (.mid/.abc/.vex/.tab).")
    p.add_argument("-o", "--output", default=None,
                   help="Write the sheet to a file (default: stdout).")
    p.add_argument("--measures-per-line", type=int, default=DEFAULT_MEASURES_PER_LINE,
                   help=f"Bars per progression row (default: {DEFAULT_MEASURES_PER_LINE}).")
    p.add_argument("--chord-tone-threshold", type=float,
                   default=DEFAULT_CHORD_TONE_THRESHOLD,
                   help="Min fraction of a bar a note must sound to count as a "
                        f"chord tone (default: {DEFAULT_CHORD_TONE_THRESHOLD}).")
    p.add_argument("--track", type=int, default=None,
                   help="For MIDI input: 1-indexed track to analyze (default: all).")
    p.add_argument("--tuning", default="STANDARD", help="Tuning name.")
    p.add_argument("--num-strings", type=int, default=6)
    p.add_argument("--max-fret", type=int, default=24)
    p.add_argument("--capo", type=int, default=0)
    p.add_argument("--optimizer", choices=["viterbi", "greedy"], default="viterbi")
    p.add_argument("--prefer-open", action="store_true",
                   help="Bias the diagram voicings toward open strings.")
    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)

    # Imported here to avoid a converter<->chords import cycle at package load.
    from ..converter import MusicConverter

    cfg = MapperConfig(
        tuning=args.tuning, num_strings=args.num_strings,
        max_fret=args.max_fret, capo=args.capo,
        optimizer=args.optimizer, prefer_open=args.prefer_open,
    )
    fmt = Path(args.input).suffix.lstrip(".").lower()
    song = MusicConverter()._parse(args.input, fmt, args.track)
    song.title = song.title if song.title and song.title != "Untitled" else Path(args.input).stem

    sheet = build_chord_sheet(
        song, cfg,
        measures_per_line=args.measures_per_line,
        chord_tone_threshold=args.chord_tone_threshold,
    )

    if args.output:
        Path(args.output).write_text(sheet)
        sys.stderr.write(f"Wrote {args.output}\n")
    else:
        sys.stdout.write(sheet)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
