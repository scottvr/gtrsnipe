"""CLI for the chord-chart output (`gtrsnipe-chords`).

Parses an input file, breaks it into per-measure chords, and writes a Markdown
chord sheet to stdout (or a file with ``-o``). Shares the full tuning + mapper
option surface with the main tool via :mod:`gtrsnipe.arguments`.
"""
import argparse
import sys
from pathlib import Path
from typing import Optional, Sequence

from ..arguments import (
    add_mapper_args,
    add_tuning_args,
    build_mapper_config,
    resolve_num_strings,
)
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
    add_tuning_args(p.add_argument_group("Instrument"))
    add_mapper_args(p.add_argument_group("Mapper (advanced)"))
    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)

    # Imported here to avoid a converter<->chords import cycle at package load.
    from ..converter import MusicConverter

    cfg = build_mapper_config(
        args, tuning=args.tuning,
        num_strings=resolve_num_strings(args.tuning, args.num_strings),
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
