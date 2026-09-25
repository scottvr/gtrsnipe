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

from ..arguments import (
    add_mapper_args,
    add_tuning_args,
    build_mapper_config,
    resolve_num_strings,
)
from ..core.config import MapperConfig
from ..core.types import MusicalEvent, Song
from ..guitar.mapper import GuitarMapper
from .audio import AudioSink, NullSink, make_audio_sink
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

    def __init__(self, renderer, *,
                 writer: Callable[[str], object] = None,
                 sleep: Callable[[float], object] = time.sleep,
                 read_key: Callable[[], str] = _default_read_key,
                 clear: bool = True,
                 audio: Optional[AudioSink] = None,
                 refresh: float = 0.08):
        self.renderer = renderer
        self.writer = writer or sys.stdout.write
        self.sleep = sleep
        self.read_key = read_key
        self.clear = clear
        self.audio = audio or NullSink()
        self.refresh = refresh  # target seconds between animation redraws

    def _paint_at(self, timeline: Sequence[Frame], beat_time: float) -> None:
        if self.clear:
            self.writer(CLEAR)
        self.writer(self.renderer.render_at(timeline, beat_time) + "\n")

    def _animate(self, timeline: Sequence[Frame], t0: float, t1: float,
                 seconds: float) -> None:
        """Redraw the view scrolling from beat ``t0`` toward ``t1`` over
        ``seconds`` of wall-clock, so motion stays continuous (and a long rest
        keeps scrolling instead of freezing)."""
        steps = max(1, round(seconds / self.refresh)) if self.refresh > 0 else 1
        for k in range(steps):
            self._paint_at(timeline, t0 + (t1 - t0) * (k / steps))
            self.sleep(seconds / steps)

    def run(self, timeline: Sequence[Frame], clock, tempo_bpm: float) -> None:
        schedule = clock.schedule(timeline, tempo_bpm)
        n = len(schedule)
        try:
            for i, (frame, delay) in enumerate(schedule):
                self.audio.attack(frame.pitches)  # onset
                t0 = frame.time
                t1 = (timeline[i + 1].time if i + 1 < n
                      else frame.time + max(frame.duration, 0.0))
                if delay is None:                 # manual advance (step clock)
                    self._paint_at(timeline, t0)
                    if i == n - 1:
                        break                     # nothing to advance to after last
                    if self.read_key() == "q":
                        break
                else:                             # auto: animate across the dwell
                    self._animate(timeline, t0, t1, delay)
        finally:
            self.audio.close()


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


def _beats_per_measure(time_signature: str) -> float:
    """Quarter-note beats per measure from a "num/den" signature (local copy to
    avoid a player->chords import cycle)."""
    try:
        num, den = (int(x) for x in time_signature.split("/"))
        return num * (4.0 / den) if num > 0 and den > 0 else 4.0
    except (ValueError, AttributeError):
        return 4.0


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
    # Give the renderer the song's meter so its bar/beat readout is correct.
    if hasattr(the_player.renderer, "beats_per_measure"):
        the_player.renderer.beats_per_measure = _beats_per_measure(song.time_signature)
    the_player.run(timeline, the_clock, tempo or song.tempo)
    return 0


def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="gtrsnipe-play",
        description="Play/visualize a gtrsnipe Song on an ASCII fretboard.",
    )
    p.add_argument("input", nargs="?", default=None,
                   help="Input file (.mid/.abc/.vex/.tab).")
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
    add_tuning_args(p.add_argument_group("Instrument"))
    add_mapper_args(p.add_argument_group("Mapper (advanced)"))
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
    p.add_argument("--fps", type=float, default=12.0,
                   help="Animation redraws per second for smooth scrolling / a "
                        "live bar:beat readout (default: 12).")
    p.add_argument("--audio", choices=["none", "midi", "fluidsynth"], default="none",
                   help="Make sound while playing: 'midi' streams to a MIDI port "
                        "(route it to a DAW/synth), 'fluidsynth' uses a SoundFont. "
                        "Default: none (needs the [play] or [synth] extra).")
    p.add_argument("--midi-port", default=None,
                   help="MIDI output port name for --audio midi (default: first "
                        "available, else a virtual 'gtrsnipe' port).")
    p.add_argument("--soundfont", default=None,
                   help="Path to a .sf2 SoundFont for --audio fluidsynth.")
    p.add_argument("--instrument", default=None,
                   help="Instrument for --audio: a GM program number (0-127) or a "
                        "name substring (e.g. 'nylon', 'distortion guitar').")
    p.add_argument("--list-instruments", action="store_true",
                   help="Print the General MIDI instrument names and exit.")
    p.add_argument("--no-clear", action="store_true",
                   help="Do not clear the screen between frames (scrolls).")
    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    if args.list_instruments:
        from .audio import GM_INSTRUMENTS
        for i, name in enumerate(GM_INSTRUMENTS):
            print(f"{i:3}  {name}")
        return 0
    if not args.input:
        parser.error("an input file is required (or use --list-instruments)")

    cfg = build_mapper_config(
        args, tuning=args.tuning,
        num_strings=resolve_num_strings(args.tuning, args.num_strings),
    )
    if args.view == "tab":
        renderer = ScrollingTabRenderer(cfg, width=args.width)
    else:
        renderer = AsciiFretboardRenderer(cfg, orientation=args.orientation,
                                          handed=args.hand)
    try:
        audio = make_audio_sink(args.audio, midi_port=args.midi_port,
                                soundfont=args.soundfont,
                                instrument=args.instrument)
    except (RuntimeError, ValueError) as e:
        sys.stderr.write(f"{e}\n")
        return 1
    refresh = 1.0 / args.fps if args.fps and args.fps > 0 else 0.08
    player = Player(renderer, clear=not args.no_clear, audio=audio, refresh=refresh)
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
