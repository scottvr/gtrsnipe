from .formats import abc, mid, tab, vex
from .core.types import Song
from .utils.io import save_text_file, save_midi_file
from .utils.logger import setup_logger
from argparse import ArgumentParser
from typing import Optional
from .formats.mid import MidiUtilFile
from pathlib import Path
import os
import logging

logger = logging.getLogger(__name__)

class MusicConverter:
    def convert(self, input_data: str, from_format: str, to_format: str, nudge: int, track_num: Optional[int], staccato: bool = False) -> str | MidiUtilFile:
        """
        Converts music data from one format to another.

        Args:
            input_data: Path to a file or a string containing the music data.
            from_format: The format of the input ('mid', 'abc', 'vex').
            to_format: The desired output format ('mid', 'abc', 'vex').
        
        Returns:
            A string representation of the output or path to the output file.
        """
        song = self._parse(input_data, from_format, track_num, staccato=staccato)
        
        if input_data:
            song.title = Path(os.path.basename(input_data)).stem

        if nudge > 0 and song.tracks:
            nudge_unit_in_beats = 0.25
            beat_offset = nudge * nudge_unit_in_beats
            logger.info(f"--- Nudging all events forward by {beat_offset} beats ---")
            for track in song.tracks:
                for event in track.events:
                    event.time += beat_offset

        output_data = self._generate(song, to_format)

        return output_data

    def _parse(self, data: str, format: str, track_num: Optional[int], staccato: bool = False
               ) -> Song:
        if format == 'mid':
            return mid.midiReader.parse(data, track_number_to_select=track_num)
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

    def _generate(self, song: Song, format: str) -> MidiUtilFile | str:
        if format == 'mid':
            return mid.midiGenerator.generate(song)
        elif format == 'abc':
            return abc.AbcGenerator.generate(song)
        elif format == 'vex':
            return vex.VextabGenerator.generate(song)
        elif format == 'tab':
            return tab.AsciiTabGenerator.generate(song)
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
        "--track",
        type=int,
        default=None,
        help="The track number (1-based) to select from a multi-track MIDI file. If not set, all tracks are processed."
    )
    parser.add_argument(
        "--no-articulations",
        action='store_true',
        help="Transcribe with no legato, taps, hammer-ons, pull-offs, etc."
    )
    parser.add_argument(
        "--staccato",
        action='store_true',
        help="Extends note durations to the start of the next note for a sustained feel. Primarily for tab-to-MIDI conversions."
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help="Enable detailed debug logging messages."
    )

    args = parser.parse_args()

    log_level = logging.DEBUG if args.debug else logging.INFO
    setup_logger(log_level)

    from_format = args.input_file.split('.')[-1]
    to_format = args.output_file.split('.')[-1]

    logger.info(f"Converting '{args.input_file}' ({from_format}) to '{args.output_file}' ({to_format})...")

    converter = MusicConverter()

    try:
        output_data = converter.convert(args.input_file, from_format, to_format, args.nudge, args.track, staccato=args.staccato)

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