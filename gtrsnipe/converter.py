from .formats import abc, mid, tab, vex
from .formats.mid.generator import MidiUtilFile
from .core.types import Song
from .core.config import MapperConfig
from .core.types import Tuning
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
                max_line_width: int = 40,
                transpose: int = 0,
                staccato: bool = False, 
                no_articulations: bool = False,
                single_string: Optional[int] = None,
                mapper_config: Optional[MapperConfig] = None) -> object | str:
        """
        Converts music data from one format to another.
        """
        song = self._parse(input_data, from_format, track_num, staccato=staccato)

        if not song:
            logger.error("Could not parse the input file; cannot proceed with conversion.")
            return None # Return None to indicate failure
        
        if input_data:
            song.title = Path(os.path.basename(input_data)).stem

        if from_format == 'mid' and mapper_config and mapper_config.tuning == 'STANDARD' and song.tracks:
            all_events = [event for track in song.tracks for event in track.events]
            if all_events:
                min_pitch = min(event.pitch for event in all_events)
                # MIDI pitch for Eb2 is 39
                if min_pitch == 39:
                    logger.info("--- Lowest note detected is Eb2. Automatically switching to E_FLAT tuning. ---")
                    mapper_config.tuning = 'E_FLAT'
        
        if transpose != 0 and song.tracks:
            logger.info(f"--- Transposing all events by {transpose} semitones ---")
            for track in song.tracks:
                for event in track.events:
                    event.pitch += transpose
                    # Clamp the pitch to the valid MIDI range [0, 127]
                    event.pitch = max(0, min(127, event.pitch))

        if nudge > 0 and song.tracks:
            nudge_unit_in_beats = 0.25
            beat_offset = nudge * nudge_unit_in_beats
            logger.info(f"--- Nudging all events forward by {beat_offset} beats ---")
            for track in song.tracks:
                for event in track.events:
                    event.time += beat_offset

        output_data = self._generate(song, to_format, no_articulations=no_articulations, single_string=single_string, max_line_width=max_line_width, mapper_config=mapper_config)

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

    def _generate(self, song: Song, format: str, no_articulations: bool = False, max_line_width = 80,
                  single_string: Optional[int] = None, staccato: bool = False, mapper_config: Optional[MapperConfig] = None) -> object | str:
        if format == 'mid':
            return mid.midiGenerator.generate(song)
        elif format == 'abc':
            return abc.AbcGenerator.generate(song)
        elif format == 'vex':
            return vex.VextabGenerator.generate(song, no_articulations=no_articulations, single_string=single_string, mapper_config=mapper_config)
        elif format == 'tab':
            return tab.AsciiTabGenerator.generate(song, no_articulations=no_articulations, single_string=single_string, max_line_width=max_line_width, mapper_config=mapper_config)
        else:
            raise ValueError(f"Unsupported output format: {format}")

def main():
    parser = ArgumentParser(description="Convert music files between binary MIDI .mid and ASCII .tab .vex, and .abc notation formats, in any direction.")
    parser.add_argument('input_file', nargs='?', help='Path to the input music file')
    parser.add_argument('output_file', nargs='?', help='Path to save the output music file')
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
        "--transpose",
        type=int,
        default=0,
        help="Transpose the music up or down by N semitones (e.g., 2 for up, -3 for down)."
    )
    parser.add_argument(
        "--no-articulations",
        action='store_true',
        help="Transcribe with no legato, taps, hammer-ons, pull-offs, etc."
    )
    parser.add_argument(
        "--staccato",
        action='store_true',
        help="Do not extend note durations to the start of the next note, instead giving each note an 1/8 note duration. When converting from ASCII tab."
    )
    parser.add_argument(
        "--max-line-width",
        type=int,
        default=40,
        help="Max number of vertical columns per line of ASCII tab. (default: 40)"
    )
    parser.add_argument(
        "--bass",
        action='store_true',
        help="Enable bass mode. Automatically uses bass tuning and a 4-string staff."
    )
    parser.add_argument(
        "--num-strings",
        type=int,
        default=None,
        choices=[4, 5, 6, 7], # Add 7 as a valid choice
        help="Force the number of strings on the tab staff (4, 5, 6, or 7). Defaults to 4 for bass and 6 for guitar."
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

    info_group = parser.add_argument_group('Tuning Information')
    info_group.add_argument(
        '--list-tunings',
        action='store_true',
        help='List all available tuning names and exit.'
    )
    info_group.add_argument(
        '--show-tuning',
        type=str,
        metavar='TUNING_NAME',
        help='Show the notes for a specific tuning and exit.'
    )

    mapper_group = parser.add_argument_group('Mapper Tuning/Configuration (Advanced)')
    # Instrument tunables
    mapper_group.add_argument(
        '--tuning',
        type=str,
        default='STANDARD',
        choices=['STANDARD', 'E_FLAT', 'DROP_D', 'OPEN_G', 'BASS_STANDARD', 'BASS_DROP_D', 'BASS_E_FLAT', 'SEVEN_STRING_STANDARD', 'BARITONE_B', 'BARITONE_A', 'BARITONE_C', 'C_SHARP', 'OPEN_C6', 'DROP_C'],
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
        '--string-switch-penalty',
        type=float,
        default=5.0,
        help='Penalty for switching strings (default: 5.0).'
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
    mapper_group.add_argument(
        '--ignore-open',
        action='store_true',
        default=False,
        help="Don't consider open when calculating shape score."
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
    
    if args.list_tunings:
        print("Available Tunings:")

        max_name_len = max(len(t.name) for t in Tuning)

        for tuning in Tuning:
            notes = ' '.join(tuning.value)
            print(f"- {tuning.name.ljust(max_name_len)} : {notes}")
        exit(0)

    if args.show_tuning:
        tuning_name_to_show = args.show_tuning.upper()
        try:
            tuning_to_show = Tuning[tuning_name_to_show]
            notes = ' '.join(tuning_to_show.value)
            print(f"Tuning: {tuning_to_show.name}")
            print(f"Notes:  {notes} (High to Low)")
        except KeyError:
            print(f"Error: Tuning '{args.show_tuning}' not found.")
            print("Use --list-tunings to see all available options.")
            exit(1)
        exit(0)    
    
    if not args.input_file or not args.output_file:
        parser.error("the following arguments are required for conversion: input_file, output_file")
 
    # The --bass flag is a shortcut for BASS_STANDARD, but only if another
    # tuning isn't explicitly chosen.
    tuning = args.tuning
    if args.bass and args.tuning == 'STANDARD':
        tuning = 'BASS_STANDARD'
    
    if args.num_strings is not None:
        num_strings = args.num_strings
    else:
        # If no choice is made, infer the number of strings from the tuning name.
        if tuning.startswith('BASS_'):
            num_strings = 4
        else:
            num_strings = 6

    mapper_config = MapperConfig(
        max_fret=args.max_fret,
        tuning=tuning,
        num_strings=num_strings,
        fret_span_penalty=args.fret_span_penalty,
        movement_penalty=args.movement_penalty,
        string_switch_penalty=args.string_switch_penalty,
        high_fret_penalty=args.high_fret_penalty,
        low_string_high_fret_multiplier=args.low_string_high_fret_multiplier,
        sweet_spot_bonus=args.sweet_spot_bonus,
        sweet_spot_low=args.sweet_spot_low,
        sweet_spot_high=args.sweet_spot_high,
        unplayable_fret_span=args.unplayable_fret_span,
        ignore_open=args.ignore_open,
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
                                        transpose=args.transpose, max_line_width=args.max_line_width,
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