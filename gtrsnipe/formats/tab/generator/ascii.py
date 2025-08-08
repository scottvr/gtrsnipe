from typing import List, Optional
from ....core.types import FretPosition, Song, Technique, Track, Tuning
from ....core.config import MapperConfig
from ....guitar.mapper import GuitarMapper
from ..tab_types import TabScore, TabMeasure, TabNote
from itertools import groupby
import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

class AsciiTabGenerator:
    @staticmethod
    def generate(song: Song, command_line: str, max_line_width: int = 40, default_note_length: str = "1/16", 
                 no_articulations: bool = False, 
                 single_string: Optional[int] = None, mapper_config: Optional[MapperConfig] = None, **kwargs) -> str:
        """
        Generates an ASCII tab string from a Song object.
        Args:
            song: The Song object to convert.
            max_line_width: The maximum character width before breaking a line.
            default_note_length: The "base unit" for rhythmic spacing (e.g., "1/8", "1/16").
        """
        if mapper_config is None:
            mapper_config = MapperConfig()

        mapper = GuitarMapper(config=mapper_config)
        mapped_song = Song(tempo=song.tempo, time_signature=song.time_signature, title=song.title, tracks=[])

        total_mapped_notes = 0
        for track in song.tracks:
            mapped_events = mapper.map_events_to_fretboard(track.events, no_articulations=no_articulations,
                                                           single_string=single_string)
            total_mapped_notes += len(mapped_events)
            new_track = Track(events=mapped_events, instrument_name=track.instrument_name)
            mapped_song.tracks.append(new_track)

        logger.info(f"--- Successfully mapped {total_mapped_notes} notes for transcription. ---")
        score = AsciiTabGenerator._create_score_from_song(mapped_song)
        
        # Calculate the base unit in beats to pass to the formatter
        try:
            num, den = map(int, default_note_length.split('/'))
            base_unit_in_beats = (num / den) * 4
        except (ValueError, ZeroDivisionError):
            base_unit_in_beats = 0.25 # Default to a 16th note

        return AsciiTabGenerator._format_score(score, command_line, max_line_width, base_unit_in_beats, mapper_config)

    @staticmethod
    def _get_quantized_spacing(time_delta: float, base_unit_in_beats: float) -> int:
        """Converts a time delta in beats to a number of dashes relative to a base unit."""
        if base_unit_in_beats <= 0: return 2 # Safety check

        # Calculate how many 'base units' fit into the time delta
        relative_duration = time_delta / base_unit_in_beats
        
        # Fewer dashes for a more compact tab
        if relative_duration <= 1.0: return 2 # 1 unit of time
        if relative_duration <= 2.0: return 3 # 2 units of time
        if relative_duration <= 4.0: return 4 # 4 units of time
        return 5 # More than 4 units

    @staticmethod
    def _create_score_from_song(song: Song) -> TabScore:
        num, den = map(int, song.time_signature.split('/'))
        time_sig_tuple = (num, den)

        if song.tracks:
            main_track = song.tracks[0]
            instrument = main_track.instrument_name
            if instrument and instrument != 'Acoustic Grand Piano':
                song.title = f"{song.title} ({instrument})"

        score = TabScore(tempo=song.tempo, time_signature=time_sig_tuple, tuning_name="STANDARD", title=song.title)

        all_events = [event for track in song.tracks for event in track.events]
        if not all_events: return score
        
        beats_per_measure = time_sig_tuple[0]
        # Sort all events by time to process them in chronological order
        all_events.sort(key=lambda e: e.time)

        current_measure_num = -1

        for event in all_events:
            if event.string is None or event.fret is None: continue
        
            beat_time = event.time
            measure_num = int(beat_time / beats_per_measure)
        
            # --- FIX: Create measures only when they are needed ---
            if measure_num > current_measure_num:
                # Add any empty measures between the last note and this one
                for i in range(measure_num - current_measure_num):
                    score.measures.append(TabMeasure([], time_sig_tuple))
                current_measure_num = measure_num

            beat_in_measure = beat_time % beats_per_measure
            note = TabNote(
                position=FretPosition(event.string, event.fret), 
                technique=Technique(event.technique) if event.technique else None, 
                beat_in_measure=beat_in_measure, 
                duration=event.duration
            )
        
            if score.measures:
                score.measures[-1].notes.append(note)
            
        return score

    @staticmethod
    def _format_single_measure(measure: TabMeasure, base_unit_in_beats: float, config: MapperConfig) -> List[str]:
        """Formats a single measure and returns its string lines."""
        measure_lines = [""] * config.num_strings
        last_event_time = 0.0
        
        sorted_notes = sorted(measure.notes, key=lambda n: n.beat_in_measure)

        if config.mono_lowest_only:
            filtered_notes = []
            # Group notes by their precise beat in the measure
            for time, notes_in_group in groupby(sorted_notes, key=lambda n: n.beat_in_measure):
                notes = list(notes_in_group)
                if len(notes) > 1:
                    # If it's a chord, find and keep only the lowest note
                    # Negate the string number to correctly prioritize lower-pitched strings (higher string numbers).
                    lowest_note = min(notes, key=lambda note: (-note.position.string, -note.position.fret))
                    filtered_notes.append(lowest_note)
                else:
                    # If it's a single note, keep it
                    filtered_notes.append(notes[0])
            # The list of notes to render is now the filtered monophonic list
            sorted_notes = filtered_notes

        notes_by_time_iter = groupby(sorted_notes, key=lambda n: n.beat_in_measure)

        # Pre-process groups to handle unplayable chords
        events_to_render = []
        for time, notes_in_group_iter in notes_by_time_iter:
            notes = list(notes_in_group_iter)
            if AsciiTabGenerator._is_chord_playable(notes, config):
                events_to_render.append({'time': time, 'notes': notes})
            else:
                # Unplayable chord: break it into individual, slightly offset notes
                for i, note in enumerate(notes):
                    events_to_render.append({'time': time + (i * 0.01), 'notes': [note]})

        for event in events_to_render:
            time = event['time']
            notes_in_chord = event['notes']

            time_delta = time - last_event_time
            spacing = AsciiTabGenerator._get_quantized_spacing(time_delta, base_unit_in_beats=base_unit_in_beats)
            
            max_len = max(len(s) for s in measure_lines) if any(measure_lines) else 0
            start_pos = max_len + spacing

            for note in notes_in_chord:
                str_idx = note.position.string
                # Add a check to prevent index errors if mapper produces an invalid note
                if str_idx >= len(measure_lines):
                    logger.warning(f"Note with string index {str_idx} is out of bounds for a {len(measure_lines)}-string instrument. Skipping.")
                    continue
                
                fret = str(note.position.fret)
                tech_map = {"hammer-on": "h", "pull-off": "p", "tap": "t"}
                symbol = tech_map.get(note.technique.value) if note.technique else None
                note_text = f"{symbol or ''}{fret}" if symbol else fret
                
                padding = start_pos - len(measure_lines[str_idx])
                measure_lines[str_idx] += ('-' * padding) + note_text
            
            last_event_time = time
        
        final_max_len = max(len(s) for s in measure_lines) if measure_lines else 0
        min_measure_width = measure.time_signature[0] * 4
        if final_max_len < min_measure_width:
            final_max_len = min_measure_width
        
        for j in range(config.num_strings):
            padding = final_max_len - len(measure_lines[j])
            measure_lines[j] += ('-' * padding)
        
        return measure_lines

    @staticmethod
    def _is_chord_playable(notes: List[TabNote], config: MapperConfig) -> bool:
        """Checks if a chord is physically playable."""
        if len(notes) <= 1:
            return True

        strings_used = set()
        frets_used = []

        for note in notes:
            # Check for multiple notes on the same string
            if note.position.string in strings_used:
                return False
            strings_used.add(note.position.string)

            # Collect frets for span calculation (ignore open strings)
            if note.position.fret > 0:
                frets_used.append(note.position.fret)
        
        # Check fret span
        if len(frets_used) > 1:
            if (max(frets_used) - min(frets_used)) > config.unplayable_fret_span:
                return False

        return True
    
    @staticmethod
    def _format_score(score: TabScore, command_line: str, max_line_width: int, base_unit_in_beats: float, config: MapperConfig) -> str:
        """Formats the complete score, breaking lines based on character width."""
        
        try:
            tuning_notes = Tuning[config.tuning].value
        except KeyError:
            tuning_notes = Tuning.STANDARD.value

        # --- New logic to generate conventional string names ---
        string_names = []
        is_bass_tuning = config.tuning.startswith('BASS_')
        
        for i, note in enumerate(tuning_notes):
            natural_name = note[0]  # Get the first character (e.g., "E" from "Eb4")

            if is_bass_tuning:
                # For bass, all names are uppercase
                display_name = natural_name.upper()
            else:
                # For guitars (6, 7, baritone), high string is lowercase
                display_name = natural_name.lower() if i == 0 else natural_name.upper()
                        
            string_names.append(display_name)
        # --- End of new logic ---

        header = [
            f"// Title: {score.title}",
            f"// Tempo: {score.tempo} BPM",
            f"// Time: {score.time_signature[0]}/{score.time_signature[1]}",
            f"// Tuning (High to Low): {' '.join(tuning_notes)}",
            ""
        ]

        if config.capo > 0:
            header.append(f"// Capo: {config.capo}nd Fret" if config.capo == 2 else
                          f"// Capo: {config.capo}st Fret" if config.capo == 1 else
                          f"// Capo: {config.capo}th Fret")

        if command_line:
            # Clean up the command for display (optional, but nice)
            executable_name = Path(sys.argv[0]).name
            display_command = command_line.replace(sys.argv[0], executable_name)
            header.append(f"// Transcribed with: {display_command}")

        header.append("") # Add a blank line after the heade1r info

        body = []
        # 'ljust' is no longer needed as all names are a single character
        tab_lines = [f"{name}|" for name in string_names]

        for measure in score.measures:
            measure_content = AsciiTabGenerator._format_single_measure(measure, base_unit_in_beats, config)
            
            if len(tab_lines[0]) + len(measure_content[0]) + 1 > max_line_width:
                body.extend(tab_lines)
                body.append("")
                tab_lines = [f"{name}|" for name in string_names]

            for i in range(config.num_strings):
                tab_lines[i] += measure_content[i] + "|"

        if len(tab_lines[0]) > 2:
            body.extend(tab_lines)
            body.append("")

        return "\n".join(header + body)


