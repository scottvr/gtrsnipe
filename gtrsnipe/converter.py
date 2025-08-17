from .formats import abc, mid, tab, vex
from .formats.mid.generator import MidiUtilFile
from .core.theory import note_name_to_pitch, pitch_to_note_name, midi_to_hz
from .core.types import Song, Tuning
from .core.config import MapperConfig
from .utils.io import save_text_file, save_midi_file
from .arguments import setup_parser
from .utils.logger import setup_logger
from .audio.dynamic_tempo import analyze_dynamic_tempo
from argparse import ArgumentParser
from typing import Optional
from pathlib import Path
from .core.types import MusicalEvent
import numpy as np
import sys
import os
import logging
from sys import exit
import librosa 

logger = logging.getLogger(__name__)
bp_logger = logging.getLogger('basic_pitch')
bp_logger.setLevel(logging.ERROR)

SAMPLE_RATE=44100

def filter_by_velocity(song: Song, velocity_cutoff: int) -> Song:
    """
    Removes all musical events from a song that are below a certain
    MIDI velocity threshold.
    """
    if velocity_cutoff <= 0:
        return song

    logger.info(f"--- Filtering out notes with velocity < {velocity_cutoff} ---")
    
    notes_before = sum(len(track.events) for track in song.tracks)
    
    for track in song.tracks:
        track.events = [event for event in track.events if event.velocity >= velocity_cutoff]

    notes_after = sum(len(track.events) for track in song.tracks)
    notes_removed = notes_before - notes_after
    
    if notes_removed > 0:
        logger.info(f"Removed {notes_removed} low-velocity notes.")
        
    return song

def pre_quantize_song(song: Song, resolution: float) -> Song:
    """
    Applies heavy-handed quantization to all events in a song.

    This function iterates through every note and snaps its start time to the
    nearest quantization grid line defined by the resolution.
    """
    logger.info(f"--- Applying pre-quantization pass with resolution: {resolution} ---")
    notes_adjusted = 0
    for track in song.tracks:
        for event in track.events:
            original_time = event.time
            quantized_time = round(original_time / resolution) * resolution
            if original_time != quantized_time:
                event.time = quantized_time
                notes_adjusted += 1
    logger.info(f"Adjusted the timing of {notes_adjusted} notes.")
    return song

def quantize_notes_to_dynamic_beats(events: list[MusicalEvent], beat_times: np.ndarray) -> list[MusicalEvent]:
    """
    Re-calculates note timings based on a dynamic beat grid.
    Assumes initial event.time is in seconds.
    """
    if not beat_times.any():
        return events # Return original events if no beats were found

    for event in events:
        note_time_sec = event.time
        note_duration_sec = event.duration

        # Find the index of the beat that occurs just before or at the note's start time
        beat_index = np.searchsorted(beat_times, note_time_sec, side='right') - 1

        if beat_index < 0:
            # Note occurs before the very first detected beat
            new_time = 0.0
            new_duration = note_duration_sec / (beat_times[1] - beat_times[0]) # Use first beat's duration as estimate
        elif beat_index >= len(beat_times) - 1:
            # Note occurs after the last detected beat
            new_time = float(beat_index)
            new_duration = note_duration_sec / (beat_times[-1] - beat_times[-2]) # Use last beat's duration
        else:
            # This is the normal case for most notes
            # Get the timestamps of the surrounding beats
            start_beat_time = beat_times[beat_index]
            end_beat_time = beat_times[beat_index + 1]
            
            beat_duration_sec = end_beat_time - start_beat_time
            if beat_duration_sec <= 0: # Avoid division by zero
                beat_duration_sec = 0.5 # Fallback duration

            # Calculate the note's fractional position within this beat
            fractional_pos = (note_time_sec - start_beat_time) / beat_duration_sec
            
            # The new time is the beat index + its fraction
            new_time = beat_index + fractional_pos
            
            # The new duration is its duration in seconds divided by the beat's duration
            new_duration = note_duration_sec / beat_duration_sec
            
        event.time = new_time
        event.duration = new_duration

    return events

def dynamic_quantize_song(intermediate_midi_path: str, processed_audio_path: str, args) -> Song:
    """
    Loads an intermediate MIDI, detects beats from audio, and returns a requantized Song.
    """
    logger.info("--- Performing dynamic beat quantization ---")
    
    # 1. Load the PROCESSED audio to get the beat grid
    y, sr = librosa.load(processed_audio_path, sr=SAMPLE_RATE)
    
    # 2. Get the beat timestamps in seconds
    _, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    beat_times = librosa.frames_to_time(beat_frames, sr=sr)
    
    # 3. Parse the intermediate MIDI file, getting timings in SECONDS
    temp_converter = MusicConverter()
    song = temp_converter._parse(intermediate_midi_path, 'mid', args.track, units='seconds')

    # 4. Re-quantize all notes in the song to this dynamic grid
    for track in song.tracks:
        track.events = quantize_notes_to_dynamic_beats(track.events, beat_times)

    # 5. Analyze the beat grid to find tempo changes
    song.tempo_events = analyze_dynamic_tempo(beat_times, song.time_signature)
    
    # 6. Set the song's initial tempo to the first detected tempo event or global average
    if song.tempo_events:
        song.tempo = song.tempo_events[0].bpm
    else:
        song.tempo = librosa.beat.tempo(y=y, sr=sr)[0]

    logger.info(f"--- Dynamic quantization complete. Initial tempo set to {song.tempo:.2f} BPM. ---")
    return song 
    # 5. Set the song's tempo to the global estimate
    song.tempo = librosa.beat.tempo(y=y, sr=sr)[0]
    logger.info(f"--- Dynamic quantization complete. Global tempo set to {song.tempo:.2f} BPM. ---")
    
    return song

class MusicConverter:
    def convert(self, song: Song, from_format: str, to_format: str, 
                command_line: str,
                nudge: int, 
                max_line_width: int = 40,
                transpose: int = 0,
                no_articulations: bool = False,
                single_string: Optional[int] = None,
                mapper_config: Optional[MapperConfig] = None) -> object | str:
        """
        Converts a Song object from one format to another.
        Assumes the Song has already been parsed and filtered.
        """
        if from_format == 'mid' and mapper_config and mapper_config.tuning == 'STANDARD' and song.tracks:
            all_events = [event for track in song.tracks for event in track.events]
            if all_events:
                min_pitch = min(event.pitch for event in all_events)
                if min_pitch == 39: # MIDI pitch for Eb2
                    logger.info("--- Lowest note detected is Eb2. Automatically switching to E_FLAT tuning. ---")
                    mapper_config.tuning = 'E_FLAT'
        

        if transpose != 0 and song.tracks:
            logger.info(f"--- Transposing all events by {transpose} semitones ---")
            for track in song.tracks:
                for event in track.events:
                    event.pitch += transpose
                    event.pitch = max(0, min(127, event.pitch)) # Clamp to valid MIDI range

        if nudge > 0 and song.tracks:
            nudge_unit_in_beats = 0.25
            beat_offset = nudge * nudge_unit_in_beats
            logger.info(f"--- Nudging all events forward by {beat_offset} beats ---")
            for track in song.tracks:
                for event in track.events:
                    event.time += beat_offset

        output_data = self._generate(song, to_format, command_line=command_line, no_articulations=no_articulations, single_string=single_string, max_line_width=max_line_width, mapper_config=mapper_config)

        return output_data


    def _parse(self, data: str, format: str, track_num: Optional[int], staccato: bool = False,  units: str = 'beats', quantization_resolution=0.125) -> Song:
        if format == 'mid':
            return mid.MidiReader.parse(data, track_number_to_select=track_num, units=units)
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
            return tab.AsciiTabParser.parse(content, staccato=staccato, quantization_resolution=quantization_resolution)
        else:
            raise ValueError(f"Unsupported input format: {format}")

    def _generate(self, song: Song, format: str, command_line: str, no_articulations: bool = False, max_line_width = 80,
                  single_string: Optional[int] = None, staccato: bool = False, mapper_config: Optional[MapperConfig] = None) -> object | str:
        if format == 'mid':
            return mid.MidiGenerator.generate(song)
        elif format == 'abc':
            return abc.AbcGenerator.generate(song)
        elif format == 'vex':
            return vex.VextabGenerator.generate(song, no_articulations=no_articulations, single_string=single_string, mapper_config=mapper_config)
        elif format == 'tab':
            return tab.AsciiTabGenerator.generate(song, command_line=command_line, no_articulations=no_articulations, single_string=single_string, max_line_width=max_line_width, mapper_config=mapper_config)
        else:
            raise ValueError(f"Unsupported output format: {format}")


def main():
    command_line = " ".join(sys.argv)
    parser = setup_parser()
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
    
    if not args.input or not args.output:
        parser.error("the following arguments are required for conversion: -i/--input and -o/--output")

    log_level = logging.DEBUG if args.debug else logging.INFO
    setup_logger(log_level)
 
    SAMPLE_RATE=44100

    try:
        current_file = args.input
        original_from_format = Path(args.input).suffix.lower()
        #output_ext = Path(args.output).suffix.lower()
        KNOWN_NON_AUDIO_FORMATS = ['.mid', '.abc', '.vex', '.tab']
        is_audio_input = original_from_format not in KNOWN_NON_AUDIO_FORMATS


        min_freq = None
        max_freq = None
 
        is_piano_mode = args.tuning.upper() == 'PIANO'
        if is_piano_mode and to_format != 'mid':
            parser.error("--tuning PIANO can only be used with MIDI output (e.g., a .mid file).")

 
        if not args.no_constrain_frequency:
            logger.info("--- Calculating frequency range based on selected tuning ---")
            try:
                tuning_notes = Tuning[args.tuning.upper()].value
                open_string_pitches = [note_name_to_pitch(n) for n in tuning_notes]
                
                min_pitch = min(open_string_pitches)
                max_pitch = max(open_string_pitches) + args.max_fret

                if not args.no_constrain_frequency and args.min_note_override:
                    try:
                        override_pitch = note_name_to_pitch(args.min_note_override)
                        logger.info(f"Overriding minimum pitch from {pitch_to_note_name(min_pitch)} to {pitch_to_note_name(override_pitch)}.")
                        min_pitch = override_pitch
                    except ValueError:
                        logger.error(f"Invalid note name for --min-note-override: '{args.min_note_override}'")

                if not args.no_constrain_frequency and args.max_note_override:
                    try:
                        override_pitch = note_name_to_pitch(args.max_note_override)
                        logger.info(f"Overriding maximum pitch from {pitch_to_note_name(max_pitch)} to {pitch_to_note_name(override_pitch)}.")
                        max_pitch = override_pitch
                    except ValueError:
                        logger.error(f"Invalid note name for --max-note-override: '{args.max_note_override}'")

                if not args.no_constrain_frequency:
                    min_freq = midi_to_hz(min_pitch)
                max_freq = midi_to_hz(max_pitch)
                
                logger.info(
                    f"Constraining frequency to {min_freq:.2f} Hz - {max_freq:.2f} Hz "
                    f"({pitch_to_note_name(min_pitch)} to {pitch_to_note_name(max_pitch)})"
                )

            except KeyError:
                logger.error(f"Tuning '{args.tuning}' not found. Cannot calculate frequency range.")
                exit(1)
        

        processed_audio_for_beats = ""

        # --- Audio Pipeline Execution ---
        if is_audio_input:
            logger.info("--- Audio input detected. Starting audio-to-MIDI pipeline. ---")
            from .audio.separator import separate_instrument
            from .audio.cleaner import cleanup_audio, apply_low_pass_filter
            from .audio.distortion_remover import remove_distortion_effects

            processed_audio_for_beats = current_file

            if args.pitch_engine == "basic-pitch": 
                from .audio.pitch_detector_bp import transcribe_to_midi_with_bp
            else:
                from .audio.pitch_detector_lr import transcribe_to_midi_with_lr

            # Determine the correct path for the intermediate MIDI file.
            intermediate_midi_path = None
            # Check if any of the requested outputs is a midi file.
            for out_path in args.output:
                if Path(out_path).suffix.lower() == '.mid':
                    intermediate_midi_path = out_path
                    break
            
            # If no MIDI output was requested, create a temporary path.
            if intermediate_midi_path is None:
                intermediate_midi_path = Path(args.input).with_suffix('.mid').name
            
            if args.stem_track:
                current_file = separate_instrument(current_file, 
                                                   instrument=args.stem_track,
                                                   model_name=args.demucs_model)

            if args.remove_fx:
                current_file = remove_distortion_effects(current_file)


            if args.low_pass_filter and max_freq:
                current_file = apply_low_pass_filter(current_file, cutoff_hz=max_freq, sr=SAMPLE_RATE)
          
            if args.nr:
                current_file = cleanup_audio(current_file)

            # Determine the correct path for the intermediate MIDI file.
            intermediate_midi_path = None
            # Check if any of the requested outputs is a midi file.
            for out_path in args.output:
                if Path(out_path).suffix.lower() == '.mid':
                    intermediate_midi_path = out_path
                    break
            
            # If no MIDI output was requested, create a temporary path.
            if intermediate_midi_path is None:
                intermediate_midi_path = Path(args.input).with_suffix('.mid').name

            if args.pitch_engine == 'basic-pitch':
                current_file = transcribe_to_midi_with_bp(
                    current_file,
                    final_output_path=intermediate_midi_path,
                    overwrite=args.yes,
                    min_freq=min_freq,
                    max_freq=max_freq,
                    onset_threshold=args.onset_threshold,
                    frame_threshold=args.frame_threshold,
                    min_note_len_ms=args.min_note_len_ms,
                    melodia_trick=args.melodia_trick,
                )
            elif args.pitch_engine == 'librosa':
                # Note: fmin and fmax could be derived from --constrain-frequency
                # for a more integrated solution.
                current_file = transcribe_to_midi_with_lr(
                    current_file,
                    intermediate_midi_path,
                    fmin_hz=min_freq or librosa.note_to_hz('C1'),
                    fmax_hz=max_freq or librosa.note_to_hz('G4')
                )



        # --- Final Conversion (The "Last Mile") ---
        # At this point, current_file is the path to a MIDI file (either original input or from the pipeline)

        converter = MusicConverter()
        format_to_parse = Path(current_file).suffix.lstrip('.')
        if args.dynamic_quantize and is_audio_input:
            # If dynamic quantize is on, we build the Song object here
            song = dynamic_quantize_song(current_file, processed_audio_for_beats, args)
        else:
            # Otherwise, we parse normally
            logger.info(f"--- Parsing '{current_file}' as a {format_to_parse} file for final conversion ---")
            song = converter._parse(current_file, format_to_parse, args.track, staccato=args.staccato, quantization_resolution=args.quantization_resolution)
        
        if not song:
            logger.error(f"Failed to parse {format_to_parse} file or file is empty.")
            exit(1)

        if args.first_note_is_downbeat:
            all_events = [event for track in song.tracks for event in track.events]
            if all_events:
                # Find the time of the very first note across all tracks
                first_note_time = min(event.time for event in all_events)
                
                # If there's leading silence, shift the entire song
                if first_note_time > 0:
                    logger.info(f"--- First note is downbeat: Shifting timeline by {-first_note_time:.3f} beats ---")
                    for track in song.tracks:
                        for event in track.events:
                            event.time -= first_note_time

        initial_note_count = sum(len(track.events) for track in song.tracks)
        logger.info(f"Parsed {initial_note_count} initial notes from the input file.")

        song.title = Path(os.path.basename(args.input)).stem 

        tuning_name = args.tuning
        num_strings = args.num_strings
    
        if num_strings is not None and tuning_name == 'STANDARD':
            if num_strings == 7:
                tuning_name = 'SEVEN_STRING_STANDARD'
            elif num_strings == 4:
                tuning_name = 'BASS_STANDARD'
        # Handle the --bass shortcut.
        elif args.bass and tuning_name == 'STANDARD':
            tuning_name = 'BASS_STANDARD'

        if num_strings is None:
            try:
                num_strings = len(Tuning[tuning_name].value)
            except KeyError:
                num_strings = 6 
    
        try:
            actual_tuning_strings = len(Tuning[tuning_name].value)
            if num_strings != actual_tuning_strings:
                parser.error(
                    f"Mismatch between --num-strings ({num_strings}) and tuning '{tuning_name}' "
                    f"(which has {actual_tuning_strings} strings). Please specify a compatible tuning."
                )
        except KeyError:
            # This will catch invalid tuning names passed with --tuning
            parser.error(f"Tuning '{tuning_name}' not found. Use --list-tunings to see available options.")

        if args.dynamic_quantize and is_audio_input:
            logger.info("--- Performing dynamic beat quantization ---")
            # 1. Load the ORIGINAL audio to get the beat grid
            y, sr = librosa.load(args.input, sr=SAMPLE_RATE)
            
            # 2. Get the beat timestamps in seconds
            _, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
            beat_times = librosa.frames_to_time(beat_frames, sr=sr)
            
            # 3. Re-quantize all notes in the song to this dynamic grid
            # The song.events are already in seconds thanks to our parser change.
            for track in song.tracks:
                track.events = quantize_notes_to_dynamic_beats(track.events, beat_times)
            
            # 4. Set the song's tempo to the global estimate
            song.tempo = librosa.beat.tempo(y=y, sr=sr)[0]
            logger.info(f"--- Dynamic quantization complete. Global tempo set to {song.tempo:.2f} BPM. ---")


        mapper_config = None
        
        if not is_piano_mode:   
            mapper_config = MapperConfig(
                max_fret=args.max_fret,
                tuning=tuning_name,
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
                prefer_open=args.prefer_open,
                fretted_open_penalty=args.fretted_open_penalty,
                ignore_open=args.ignore_open,
                legato_time_threshold=args.legato_time_threshold,
                tapping_run_threshold=args.tapping_run_threshold,
                deduplicate_pitches=args.dedupe,
                quantization_resolution=args.quantization_resolution,
                capo=args.capo,
                barre_bonus=args.barre_bonus,  
                barre_penalty=args.barre_penalty,  
                mono_lowest_only=args.mono_lowest_only,
                let_ring_bonus=args.let_ring_bonus,
                diagonal_span_penalty=args.diagonal_span_penalty,
            )
        
        song = filter_by_velocity(song, args.velocity_cutoff)

        if not args.no_pre_quantize and mapper_config:
            logger.info(f"Pre-quantizing before any fretboard mapping.")
            song = pre_quantize_song(song, args.quantization_resolution)    
        
        if not is_piano_mode:
            if args.analyze:
                logger.info(f"--- Analyzing Processed Song Data ---")
                all_events = [event for track in song.tracks for event in track.events]
                if not all_events:
                    logger.info("No musical events found in the specified pitch range.")
                    exit(0)

                min_pitch = min(event.pitch for event in all_events)
                max_pitch = max(event.pitch for event in all_events)

                suggested_tunings = []
                for tuning in Tuning:
                    open_notes = [note_name_to_pitch(n) for n in tuning.value]
                    lowest_tuning_note = min(open_notes)
                    highest_playable_note = max(open_notes) + args.max_fret
                    if min_pitch >= lowest_tuning_note and max_pitch <= highest_playable_note:
                        suggested_tunings.append((tuning, lowest_tuning_note))

                suggested_tunings.sort(key=lambda x: min_pitch - x[1])

                logger.info(f"Found {len(all_events)} notes within the specified pitch range.")
                logger.info(f"Lowest Note:  {min_pitch} ({pitch_to_note_name(min_pitch)})")
                logger.info(f"Highest Note: {max_pitch} ({pitch_to_note_name(max_pitch)})")
                logger.info("\n--- Tuning Suggestions ---")
                if not suggested_tunings:
                    logger.info("Could not find any standard tunings that fit this song's pitch range.")
                else:
                    logger.info(f"Based on a {args.max_fret}-fret neck.")
                    logger.info("The following tunings can accommodate the song's pitch range:")
                    for tuning, low_note in suggested_tunings:
                        print(f"- {tuning.name} (Lowest note: {pitch_to_note_name(low_note)})")
                exit(0)
            if args.constrain_pitch:
                max_fret = args.max_fret
                try:
                    # Use the tuning from the --tuning argument
                    constrain_tuning_name = args.tuning.upper()
                    constrain_tuning = Tuning[constrain_tuning_name]

                    constrain_open_notes = [note_name_to_pitch(n) for n in constrain_tuning.value]
                    min_range = min(constrain_open_notes)
                    max_range = max(constrain_open_notes) + max_fret

                    logger.info(f"Constraining notes to '{constrain_tuning_name}' range (Mode: {args.pitch_mode})")

                    if args.pitch_mode == 'normalize':
                        notes_normalized = 0
                        for track in song.tracks:
                            for event in track.events:
                                # Check if the note is outside the playable range
                                if event.pitch > max_range or event.pitch < min_range:
                                    notes_normalized += 1
                                        # While the note is too high, transpose it down by one octave
                                    while event.pitch > max_range:
                                        event.pitch -= 12
                                            # While the note is too low, transpose it up by one octave
                                        while event.pitch < min_range:
                                            event.pitch += 12
                        if notes_normalized > 0:
                            logger.info(f"Normalized {notes_normalized} out-of-range note(s) by octaves to fit the range.")

                    elif args.pitch_mode == 'drop':
                        original_note_count = sum(len(track.events) for track in song.tracks)
                        for track in song.tracks:
                            track.events = [e for e in track.events if min_range <= e.pitch <= max_range]

                        new_note_count = sum(len(track.events) for track in song.tracks)
                        notes_discarded = original_note_count - new_note_count
                        if notes_discarded > 0:
                            logger.info(f"Discarded {notes_discarded} out-of-range note(s).")

                except KeyError:
                    logger.error(f"Error: Tuning '{args.tuning}' not found.")
                    exit(1) 

        logger.info("--- Generating output files ---")
        for output_path_str in args.output:
            output_path = Path(output_path_str)
            to_format = output_path.suffix.lstrip('.').lower()

            output_data = converter.convert(
                song=song,
                command_line=command_line,
                from_format=format_to_parse,
                to_format=to_format,
                nudge=args.nudge,
                transpose=args.transpose,
                max_line_width=args.max_line_width,
                no_articulations=args.no_articulations,
                single_string=args.single_string,
                mapper_config=mapper_config
            )
    
            if output_path.exists() and not args.yes:
                logger.error(f"Error: Output file '{output_path}' already exists.")
                logger.error("Use the -y or --yes flag to allow overwriting.")
                exit(1)


            logger.info(f"Saving '{args.input}' ({format_to_parse}) to '{args.output}' ({to_format})...")

            if to_format == 'mid':
                if isinstance(output_data, MidiUtilFile):
                    save_midi_file(output_data, str(output_path))
            else:
                if isinstance(output_data, str):                
                    save_text_file(output_data, str(output_path))

            logger.info(f"Successfully saved {output_path_str}")

    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=args.debug)

if __name__ == "__main__":
    main()