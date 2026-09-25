"""Wire the player together: parse -> map -> timeline -> transport -> render.

The Transport (:mod:`gtrsnipe.player.transport`) drives playback; a small Driver
binds a renderer + a visual Sink + an AudioSink to the Transport's callbacks. All
I/O is injectable (sink, audio, clock) so the run loop stays unit-testable. The
CLI entry point (:func:`main`, the ``gtrsnipe-play`` console script) parses a
file, maps it to the fretboard, and plays it in the terminal.
"""
import argparse
import sys
import time
from pathlib import Path
from typing import List, Optional, Sequence

from ..arguments import (
    add_mapper_args,
    add_tuning_args,
    build_mapper_config,
    resolve_num_strings,
)
from ..core.config import MapperConfig
from ..core.types import Song
from ..guitar.mapper import GuitarMapper
from .audio import AudioSink, NullSink, make_audio_sink
from .frame import Frame
from .render.ascii import AsciiFretboardRenderer
from .render.scrolltab import ScrollingTabRenderer
from .sink import PlainSink, Sink
from .timeline import DEFAULT_WINDOW_SIZE, TimelineBuilder
from .transport import Transport, metronome_timeline


class _Driver:
    """Binds a renderer + visual sink + audio sink to the Transport callbacks."""

    def __init__(self, timeline: Sequence[Frame], renderer, sink: Sink,
                 audio: AudioSink):
        self.timeline = timeline
        self.renderer = renderer
        self.sink = sink
        self.audio = audio

    def render(self, beat_time: float) -> None:
        # Let an interactive sink (curses) drive the renderer's viewport width.
        w = getattr(self.sink, "width", None)
        if w and hasattr(self.renderer, "width"):
            self.renderer.width = w
        self.sink.write(self.renderer.render_at(self.timeline, beat_time))

    def fire(self, frames: Sequence[Frame]) -> None:
        pitches = [p for f in frames for p in f.pitches]
        self.audio.attack(pitches)

    def silence(self) -> None:
        self.audio.all_off()

    def read_key(self, blocking: bool) -> Optional[str]:
        return self.sink.read_key(blocking)


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


def build_renderer(cfg: MapperConfig, *, view: str = "fretboard",
                   orientation: str = "horizontal", handed: str = "right",
                   width: int = 48):
    if view == "tab":
        return ScrollingTabRenderer(cfg, width=width)
    return AsciiFretboardRenderer(cfg, orientation=orientation, handed=handed)


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
              window_size: int = DEFAULT_WINDOW_SIZE, track: Optional[int] = None,
              mapper_config: Optional[MapperConfig] = None,
              view: str = "fretboard", orientation: str = "horizontal",
              handed: str = "right", width: int = 48, fps: float = 12.0,
              audio: Optional[AudioSink] = None, sink: Optional[Sink] = None,
              now=time.monotonic, sleep=time.sleep) -> int:
    """Parse, map, and play a file. Returns a process exit code.

    ``clock`` maps to Transport state: ``tempo``/``metronome`` play; ``step``
    starts paused. ``metronome`` also re-times the timeline to an even grid.
    """
    cfg = mapper_config or MapperConfig()
    song = parse_and_map(input_path, cfg, track=track)
    timeline = build_timeline(song, cfg, window_size=window_size)

    the_audio = audio or NullSink()
    the_sink = sink or PlainSink(interactive=True)
    try:
        if not timeline:
            sys.stderr.write("Nothing to play: no notes could be mapped.\n")
            return 1
        if clock == "metronome":
            timeline = metronome_timeline(timeline, grid_beats)
        renderer = build_renderer(cfg, view=view, orientation=orientation,
                                  handed=handed, width=width)
        if hasattr(renderer, "beats_per_measure"):
            renderer.beats_per_measure = _beats_per_measure(song.time_signature)
        driver = _Driver(timeline, renderer, the_sink, the_audio)
        transport = Transport(timeline, tempo or song.tempo, fps=fps,
                              playing=(clock != "step"), now=now, sleep=sleep)
        the_sink.setup()
        transport.run(driver)
        return 0
    finally:
        the_audio.close()
        the_sink.teardown()


def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="gtrsnipe-play",
        description="Play/visualize a gtrsnipe Song on an ASCII fretboard.",
    )
    p.add_argument("input", nargs="?", default=None,
                   help="Input file (.mid/.abc/.vex/.tab).")
    p.add_argument("--clock", choices=["tempo", "metronome", "step"],
                   default="tempo",
                   help="Timing: at-tempo, fixed metronome grid, or start paused "
                        "for manual spacebar step (default: tempo).")
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
                   help="Fretboard view only: strings as rows or frets top-to-bottom.")
    p.add_argument("--hand", choices=["right", "left"], default="right",
                   help="Fretboard view only: mirror the neck for left-handed players.")
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
    try:
        audio = make_audio_sink(args.audio, midi_port=args.midi_port,
                                soundfont=args.soundfont,
                                instrument=args.instrument)
    except (RuntimeError, ValueError) as e:
        sys.stderr.write(f"{e}\n")
        return 1
    sink = PlainSink(clear=not args.no_clear, interactive=True)
    try:
        return play_file(
            args.input, clock=args.clock, tempo=args.tempo, grid_beats=args.grid,
            window_size=args.window, track=args.track, mapper_config=cfg,
            view=args.view, orientation=args.orientation, handed=args.hand,
            width=args.width, fps=args.fps, audio=audio, sink=sink,
        )
    except KeyboardInterrupt:  # pragma: no cover - interactive
        sys.stderr.write("\nStopped.\n")
        return 130


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
