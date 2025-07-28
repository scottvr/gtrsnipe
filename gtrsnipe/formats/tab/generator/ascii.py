from typing import List, Optional
from ....core.types import FretPosition, Song, Technique, Track
from ....core.config import MapperConfig
from ....guitar.mapper import GuitarMapper
from ..types import TabScore, TabMeasure, TabNote
from itertools import groupby
import logging

logger = logging.getLogger(__name__)

class AsciiTabGenerator:
    @staticmethod
    def generate(song: Song, max_line_width: int = 120, default_note_length: str = "1/16", 
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
        for track in song.tracks:
            mapped_events = mapper.map_events_to_fretboard(track.events, no_articulations=no_articulations,
                                                           single_string=single_string)
            new_track = Track(events=mapped_events, instrument_name=track.instrument_name)
            mapped_song.tracks.append(new_track)

        score = AsciiTabGenerator._create_score_from_song(mapped_song)
        
        # Calculate the base unit in beats to pass to the formatter
        try:
            num, den = map(int, default_note_length.split('/'))
            base_unit_in_beats = (num / den) * 4
        except (ValueError, ZeroDivisionError):
            base_unit_in_beats = 0.25 # Default to a 16th note

        return AsciiTabGenerator._format_score(score, max_line_width, base_unit_in_beats, mapper_config)

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
        # This method is unchanged
        num, den = map(int, song.time_signature.split('/'))
        time_sig_tuple = (num, den)
        score = TabScore(tempo=song.tempo, time_signature=time_sig_tuple, tuning_name="STANDARD", title=song.title)
        all_events = [event for track in song.tracks for event in track.events]
        if not all_events: return score
        
        beats_per_measure = time_sig_tuple[0]
        last_event = max(all_events, key=lambda e: e.time)
        total_measures = int(last_event.time / beats_per_measure) + 1
        for _ in range(total_measures):
            score.measures.append(TabMeasure([], time_sig_tuple))

        for event in all_events:
            if event.string is None or event.fret is None: continue
            beat_time = event.time
            measure_num = int(beat_time / beats_per_measure)
            beat_in_measure = beat_time % beats_per_measure
            note = TabNote(position=FretPosition(event.string, event.fret), technique=Technique(event.technique) if event.technique else None, beat_in_measure=beat_in_measure, duration=event.duration)
            if measure_num < len(score.measures):
                score.measures[measure_num].notes.append(note)
        return score


    @staticmethod
    def _format_single_measure(measure: TabMeasure, base_unit_in_beats: float, config: MapperConfig) -> List[str]:
        """Formats a single measure and returns its string lines."""
        measure_lines = [""] * 6
        last_event_time = 0.0
        
        sorted_notes = sorted(measure.notes, key=lambda n: n.beat_in_measure)
        QUANTIZATION_RESOLUTION = 0.125
        def quantize_time(beat):
            return round(beat / QUANTIZATION_RESOLUTION) * QUANTIZATION_RESOLUTION
        
        notes_by_time_iter = groupby(sorted_notes, key=lambda n: quantize_time(n.beat_in_measure))

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
        
        for j in range(6):
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
    def _format_score(score: TabScore, max_line_width: int, base_unit_in_beats: float, config: MapperConfig) -> str:
        """Formats the complete score, breaking lines based on character width."""
        string_names = ['e', 'B', 'G', 'D', 'A', 'E']
        header = [
            f"// Title: {score.title}",
            f"// Tempo: {score.tempo} BPM",
            f"// Time: {score.time_signature[0]}/{score.time_signature[1]}",
            f"// Tuning: {score.tuning_name}", ""
        ]
        body = []
        tab_lines = [f"{name}|" for name in string_names]

        for measure in score.measures:
            measure_content = AsciiTabGenerator._format_single_measure(measure, base_unit_in_beats, config)
            
            # If adding the next measure exceeds the max width, break the line.
            # (+1 for the "|" separator)
            if len(tab_lines[0]) + len(measure_content[0]) + 1 > max_line_width:
                body.extend(tab_lines)
                body.append("")
                tab_lines = [f"{name}|" for name in string_names]

            # Append the measure content to the current line.
            for i in range(6):
                tab_lines[i] += measure_content[i] + "|"

        # Append the final line of tab to the body.
        if len(tab_lines[0]) > 2: # Check if the line has more than just "e|"
            body.extend(tab_lines)
            body.append("")

        return "\n".join(header + body)



