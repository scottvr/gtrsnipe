from .formats import abc, mid, tab, vex
from .formats.mid.generator import MidiUtilFile
from .core.types import Song
from .core.config import MapperConfig
from .utils.io import save_text_file, save_midi_file
from .utils.logger import setup_logger
from argparse import ArgumentParser
from typing import Optional
from pathlib import Path
import os
import logging
from sys import exit

logger = logging.getLogger(__name__)

class MusicConverter:
    def convert(self, input_data: str, from_format: str, to_format: str, 
                nudge: int, track_num: Optional[int], 
                staccato: bool = False, 
                no_articulations: bool = False,
                single_string: Optional[int] = None,
                mapper_config: Optional[MapperConfig] = None) -> object | str:
        """
        Converts music data from one format to another.
        """
        song = self._parse(input_data, from_format, track_num)
        
        if input_data:
            song.title = Path(os.path.basename(input_data)).stem

        if nudge > 0 and song.tracks:
            nudge_unit_in_beats = 0.25
            beat_offset = nudge * nudge_unit_in_beats
            logger.info(f"--- Nudging all events forward by {beat_offset} beats ---")
            for track in song.tracks:
                for event in track.events:
                    event.time += beat_offset

        output_data = self._generate(song, to_format, no_articulations=no_articulations, single_string=single_string, mapper_config=mapper_config)

        return output_data

    def _parse(self, data: str, format: str, track_num: Optional[int], staccato: bool = False) -> Song:
        if format == 'mid':
            return mid.MidiReader.parse(data, track_number_to_select=track_num)
        elif format == 'abc':
            with open(data, 'r') as f:
                content = f.read()
            return abc.AbcParser.parse(content)
        elif format == 'vex':
            with open(data, 'r') as f:
                content = f.read()
            return vex.VextabParser.parse(content)
        elif format == 'tab':
            with open(data, 'r') as f:
                content = f.read()
            return tab.AsciiTabParser.parse(content, staccato=staccato)
        else:
            raise ValueError(f"Unsupported input format: {format}")

    def _generate(self, song: Song, format: str, no_articulations: bool = False,
                  single_string: Optional[int] = None, mapper_config: Optional[MapperConfig] = None) -> object | str:
        if format == 'mid':
            return mid.midiGenerator.generate(song)
        elif format == 'abc':
            return abc.AbcGenerator.generate(song)
        elif format == 'vex':
            return vex.VextabGenerator.generate(song, no_articulations=no_articulations, single_string=single_string, mapper_config=mapper_config)
        elif format == 'tab':
            return tab.AsciiTabGenerator.generate(song, no_articulations=no_articulations, single_string=single_string, mapper_config=mapper_config)
        else:
            raise ValueError(f"Unsupported output format: {format}")

def main():
    parser = ArgumentParser(description="Convert music files between binary MIDI .mid and ASCII .tab .vex, and .abc notation formats, in any direction.")
    parser.add_argument('input_file', help='Path to the input music file')
    parser.add_argument('output_file', help='Path to save the output music file')
    parser.add_argument(
        "--nudge",
        type=int,
        default=0,
        help="An integer to shift the transcription's start time to the right. Each unit corresponds to roughly a 16th note."
    )
    parser.add_argument(
        '-y', '--yes',
        action='store_true',
        help="Automatically overwrite the output file if it already exists."
    )
    parser.add_argument(
        "--track",
        type=int,
        default=None,
        help="The track number (1-based) to select from a multi-track MIDI file. If not set, all tracks are processed. For a multitrack midi, you will want to select a single instrument track to transcribe."
    )
    parser.add_argument(
        "--no-articulations",
        action='store_true',
        help="Transcribe with no legato, taps, hammer-ons, pull-offs, etc."
    )
    parser.add_argument(
        "--staccato",
        action='store_true',
        help="Do not extend note durations to the start of the next note, instead giving each note an 1/8 note duration. Primarily for tab-to-MIDI conversions."
    )
    parser.add_argument(
        "--single-string",
        type=int,
        default=None,
        choices=range(1, 7), # Restrict input to 1, 2, 3, 4, 5, 6
        help="Force all notes onto a single string (1-6, high e to low E). Ideal for transcribing legato/tapping runs."
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help="Enable detailed debug logging messages."
    )
    mapper_group = parser.add_argument_group('Mapper Tuning (Advanced)')
    # Instrument tunables
    mapper_group.add_argument(
        '--tuning',
        type=str,
        default='STANDARD',
        choices=['STANDARD', 'DROP_D', 'OPEN_G'],
        help='Specify the guitar tuning (default: STANDARD).'
    )
    mapper_group.add_argument(
        '--max-fret',
        type=int,
        default=24,
        help='Maximum fret number on the virtual guitar neck (default: 24).'
    )
    # Scoring Weights
    mapper_group.add_argument(
        '--fret-span-penalty',
        type=float,
        default=100.0,
        help='Penalty for wide fret stretches (default: 100.0).'
    )
    mapper_group.add_argument(
        '--movement-penalty',
        type=float,
        default=3.0,
        help='Penalty for hand movement between chords (default: 3.0).'
    )
    mapper_group.add_argument(
        '--high-fret-penalty',
        type=float,
        default=5,
        help='Penalty for playing high on the neck (default: 5).'
    )
    mapper_group.add_argument(
        '--low-string-high-fret-multiplier',
        type=float,
        default=10.0,
        help='Multiplier penalty for playing high on the neck on low strings (default: 10).'
    )
    mapper_group.add_argument(
        '--unplayable-fret-span',
        type=int,
        default=4,
        help='Fret span considered unplayable (default: 4).'
    )
    mapper_group.add_argument(
        '--sweet-spot-bonus',
        type=float,
        default=0.5,
        help='Bonus for playing in the ideal lower fret range.'
    )
    mapper_group.add_argument(
        '--sweet-spot-low',
        type=int,
        default=0,
        help='Lowest fret of the "sweet spot" (default 0 - open)'
    )
    mapper_group.add_argument(
        '--sweet-spot-high',
        type=int,
        default=12,
        help='Highest fret of the "sweet spot" (default 12)'
    )
    # Technique Inference Thresholds
    mapper_group.add_argument(
        '--legato-time-threshold',
        type=float,
        default=0.5,
        help='Max time in beats between notes for a legato phrase (h/p) (default: 0.5).'
    )
    mapper_group.add_argument(
        '--tapping-run-threshold',
        type=int,
        default=2,
        help='Min number of notes in a run to be considered for tapping (default: 2).'
    )

    args = parser.parse_args()

    mapper_config = MapperConfig(
        max_fret=args.max_fret,
        tuning=args.tuning,
        fret_span_penalty=args.fret_span_penalty,
        movement_penalty=args.movement_penalty,
        high_fret_penalty=args.high_fret_penalty,
        low_string_high_fret_multiplier=args.low_string_high_fret_multiplier,
        sweet_spot_bonus=args.sweet_spot_bonus,
        sweet_spot_low=args.sweet_spot_low,
        sweet_spot_high=args.sweet_spot_high,
        unplayable_fret_span=args.unplayable_fret_span,
        legato_time_threshold=args.legato_time_threshold,
        tapping_run_threshold=args.tapping_run_threshold
    )

    log_level = logging.DEBUG if args.debug else logging.INFO
    setup_logger(log_level)

    output_path = Path(args.output_file)
    if output_path.exists() and not args.yes:
        logger.error(f"Error: Output file '{output_path}' already exists.")
        logger.error("Use the -y or --yes flag to allow overwriting.")
        exit(1)

    from_format = args.input_file.split('.')[-1]
    to_format = args.output_file.split('.')[-1]

    logger.info(f"Converting '{args.input_file}' ({from_format}) to '{args.output_file}' ({to_format})...")

    converter = MusicConverter()

    try:
        output_data = converter.convert(args.input_file, from_format, to_format, 
                                        args.nudge, args.track, staccato=args.staccato, 
                                        no_articulations=args.no_articulations,
                                        single_string=args.single_string, mapper_config=mapper_config)

        if to_format == 'mid':
            if isinstance(output_data, MidiUtilFile):
                save_midi_file(output_data, args.output_file)
        else:
            if isinstance(output_data, str):
                save_text_file(output_data, args.output_file)

    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=args.debug)

if __name__ == "__main__":
    main()