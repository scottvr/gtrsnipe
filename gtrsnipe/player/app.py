"""Wire the player together: parse -> map -> timeline -> clock -> render -> run.

This module owns the only I/O in the player (screen clears, sleeping, keypress
reads) and keeps it injectable so the run loop stays unit-testable. The CLI
entry point (:func:`main`, exposed as the ``gtrsnipe-play`` console script)
parses a file, maps it to the fretboard, and plays it in the terminal.
"""
import argparse
import sys
import time
from pathlib import Path
from typing import Callable, List, Optional, Sequence

from ..core.config import MapperConfig
from ..core.types import MusicalEvent, Song
from ..guitar.mapper import GuitarMapper
from .clock import make_clock
from .frame import Frame
from .render.ascii import AsciiFretboardRenderer
from .render.scrolltab import ScrollingTabRenderer
from .timeline import DEFAULT_WINDOW_SIZE, TimelineBuilder

CLEAR = "\033[2J\033[H"  # clear screen + cursor home


def _default_read_key() -> str:
    """Read a single keypress without waiting for Enter (POSIX), else fall back.

    Returns the character read (lowercased). On platforms without termios we
    fall back to line-buffered ``input`` (press Enter to advance).
    """
    try:
        import termios
        import tty
    except ImportError:  # non-POSIX: no raw mode available
        termios = None

    # Raw single-char reads need a real terminal. When stdin is piped or
    # redirected (tests, `printf | ...`), fall back to line-buffered input.
    if termios is None or not sys.stdin.isatty():
        return (sys.stdin.readline()[:1] or "\n").lower()

    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
    return ch.lower()


class Player:
    """Drives a timeline through a clock, painting each frame as it advances.

    I/O is injected so tests can drive the loop with fakes:
        writer:   receives the rendered text for each frame
        sleep:    called with the delay in seconds for auto-advancing clocks
        read_key: called to advance a manual (step) clock; return 'q' to quit
    """

    def __init__(self, renderer: AsciiFretboardRenderer, *,
                 writer: Callable[[str], object] = None,
                 sleep: Callable[[float], object] = time.sleep,
                 read_key: Callable[[], str] = _default_read_key,
                 clear: bool = True):
        self.renderer = renderer
        self.writer = writer or sys.stdout.write
        self.sleep = sleep
        self.read_key = read_key
        self.clear = clear

    def _paint(self, timeline: Sequence[Frame], index: int) -> None:
        if self.clear:
            self.writer(CLEAR)
        self.writer(self.renderer.paint(timeline, index) + "\n")

    def run(self, timeline: Sequence[Frame], clock, tempo_bpm: float) -> None:
        schedule = clock.schedule(timeline, tempo_bpm)
        n = len(schedule)
        for i, (frame, delay) in enumerate(schedule):
            self._paint(timeline, i)
            if i == n - 1:
                break
            if delay is None:
                if self.read_key() == "q":
                    break
            else:
                self.sleep(delay)


def parse_and_map(input_path: str, mapper_config: MapperConfig, *,
                  track: Optional[int] = None,
                  no_articulations: bool = True) -> Song:
    """Parse an input file and map every track onto the fretboard."""
    # Imported here to avoid a converter<->player import cycle at package load.
    from ..converter import MusicConverter

    fmt = Path(input_path).suffix.lstrip(".").lower()
    song = MusicConverter()._parse(
        input_path, fmt, track,
        quantization_resolution=mapper_config.quantization_resolution,
    )
    mapper = GuitarMapper(mapper_config)
    for trk in song.tracks:
        trk.events = mapper.map_events_to_fretboard(
            trk.events, no_articulations=no_articulations)
    return song


def build_timeline(song: Song, mapper_config: MapperConfig,
                   window_size: int = DEFAULT_WINDOW_SIZE) -> List[Frame]:
    return TimelineBuilder(mapper_config, window_size=window_size).build_from_song(song)


def play_file(input_path: str, *, clock: str = "tempo",
              tempo: Optional[float] = None, grid_beats: float = 0.5,
              window_size: int = DEFAULT_WINDOW_SIZE,
              track: Optional[int] = None,
              mapper_config: Optional[MapperConfig] = None,
              player: Optional[Player] = None) -> int:
    """Parse, map, and play a file in the terminal. Returns a process exit code."""
    cfg = mapper_config or MapperConfig()
    song = parse_and_map(input_path, cfg, track=track)
    timeline = build_timeline(song, cfg, window_size=window_size)
    if not timeline:
        sys.stderr.write("Nothing to play: no notes could be mapped.\n")
        return 1
    the_clock = make_clock(clock, grid_beats=grid_beats)
    the_player = player or Player(AsciiFretboardRenderer(cfg))
    the_player.run(timeline, the_clock, tempo or song.tempo)
    return 0


def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="gtrsnipe-play",
        description="Play/visualize a gtrsnipe Song on an ASCII fretboard.",
    )
    p.add_argument("input", help="Input file (.mid/.abc/.vex/.tab).")
    p.add_argument("--clock", choices=["tempo", "metronome", "step"],
                   default="tempo",
                   help="Timing policy: at-tempo, fixed metronome grid, or "
                        "manual spacebar step (default: tempo).")
    p.add_argument("--tempo", type=float, default=None,
                   help="Override tempo in BPM (default: the song's tempo).")
    p.add_argument("--grid", type=float, default=0.5,
                   help="Metronome step in beats (default: 0.5 = eighth note).")
    p.add_argument("--window", type=int, default=DEFAULT_WINDOW_SIZE,
                   help=f"Visible fret window size (default: {DEFAULT_WINDOW_SIZE}).")
    p.add_argument("--track", type=int, default=None,
                   help="For MIDI input: 1-indexed track to play (default: all).")
    p.add_argument("--tuning", default="STANDARD", help="Tuning name.")
    p.add_argument("--num-strings", type=int, default=6)
    p.add_argument("--max-fret", type=int, default=24)
    p.add_argument("--capo", type=int, default=0)
    p.add_argument("--optimizer", choices=["viterbi", "greedy"], default="viterbi")
    p.add_argument("--view", choices=["fretboard", "tab"], default="fretboard",
                   help="fretboard = animated neck; tab = horizontally scrolling "
                        "tab staff (Guitar-Hero style). Default: fretboard.")
    p.add_argument("--orientation", choices=["horizontal", "vertical"],
                   default="horizontal",
                   help="Fretboard view only: strings as rows (horizontal) or "
                        "frets top-to-bottom (vertical). Default: horizontal.")
    p.add_argument("--hand", choices=["right", "left"], default="right",
                   help="Fretboard view only: mirror the neck for left-handed "
                        "players (default: right).")
    p.add_argument("--width", type=int, default=48,
                   help="Tab view only: viewport width in columns (default: 48).")
    p.add_argument("--no-clear", action="store_true",
                   help="Do not clear the screen between frames (scrolls).")
    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    cfg = MapperConfig(
        tuning=args.tuning,
        num_strings=args.num_strings,
        max_fret=args.max_fret,
        capo=args.capo,
        optimizer=args.optimizer,
    )
    if args.view == "tab":
        renderer = ScrollingTabRenderer(cfg, width=args.width)
    else:
        renderer = AsciiFretboardRenderer(cfg, orientation=args.orientation,
                                          handed=args.hand)
    player = Player(renderer, clear=not args.no_clear)
    try:
        return play_file(
            args.input, clock=args.clock, tempo=args.tempo,
            grid_beats=args.grid, window_size=args.window, track=args.track,
            mapper_config=cfg, player=player,
        )
    except KeyboardInterrupt:  # pragma: no cover - interactive
        sys.stderr.write("\nStopped.\n")
        return 130


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
