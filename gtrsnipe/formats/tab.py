from dataclasses import dataclass, field
from typing import List, Optional, Tuple
import math
import re
from ..core.types import FretPosition, MusicalEvent, Song, Technique, Track
from ..guitar.mapper import GuitarMapper
from itertools import groupby
import logging

logger = logging.getLogger(__name__)

@dataclass
class TabNote:
    """Represents a single note within a measure for formatting purposes."""
    position: FretPosition
    beat_in_measure: float
    technique: Optional[Technique] = None
    duration: float = 1.0

@dataclass
class TabMeasure:
    """Represents a measure of tab."""
    notes: List[TabNote]
    time_signature: Tuple[int, int]

@dataclass
class TabScore:
    """Represents a complete tab score to be formatted."""
    measures: List[TabMeasure] = field(default_factory=list)
    title: str = "Untitled"
    tuning_name: str = "STANDARD"
    time_signature: Tuple[int, int] = (4, 4)
    tempo: float = 120.0


class AsciiTabGenerator:
    @staticmethod
    def generate(song: Song, max_line_width: int = 120, default_note_length: str = "1/16", no_articulataions: bool = False) -> str:
        """
        Generates an ASCII tab string from a Song object.
        Args:
            song: The Song object to convert.
            max_line_width: The maximum character width before breaking a line.
            default_note_length: The "base unit" for rhythmic spacing (e.g., "1/8", "1/16").
        """
        mapper = GuitarMapper()
        mapped_song = Song(tempo=song.tempo, time_signature=song.time_signature, title=song.title, tracks=[])
        for track in song.tracks:
            mapped_events = mapper.map_events_to_fretboard(track.events, no_articulataions=no_articulataions)
            new_track = Track(events=mapped_events, instrument_name=track.instrument_name)
            mapped_song.tracks.append(new_track)

        score = AsciiTabGenerator._create_score_from_song(mapped_song)
        
        # Calculate the base unit in beats to pass to the formatter
        try:
            num, den = map(int, default_note_length.split('/'))
            base_unit_in_beats = (num / den) * 4
        except (ValueError, ZeroDivisionError):
            base_unit_in_beats = 0.25 # Default to a 16th note

        return AsciiTabGenerator._format_score(score, max_line_width, base_unit_in_beats)

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
    def _format_single_measure(measure: TabMeasure, base_unit_in_beats: float) -> List[str]:
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
            if AsciiTabGenerator._is_chord_playable(notes):
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
                tech_map = {"hammer-on": "h", "pull-off": "p"}
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
    def _is_chord_playable(notes: List[TabNote]) -> bool:
        """Checks if a chord is physically playable."""
        if len(notes) <= 1:
            return True

        MAX_FRET_SPAN = 4
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
            if (max(frets_used) - min(frets_used)) > MAX_FRET_SPAN:
                return False

        return True
    
    @staticmethod
    def _format_score(score: TabScore, max_line_width: int, base_unit_in_beats: float, ) -> str:
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
            measure_content = AsciiTabGenerator._format_single_measure(measure, base_unit_in_beats)
            
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


@dataclass
class _TabEvent:
    """A temporary data structure to hold note info before final timing is calculated."""
    char_idx: int
    string_idx: int
    fret: int
    technique: Optional[str] = None


class AsciiTabParser:
    """
    Parses an ASCII tablature string into a format-agnostic Song object,
    inferring rhythm from note spacing.
    """

    @staticmethod
    def _spacing_to_beats(spacing: int, base_unit_in_beats: float) -> float:
        """The inverse of the generator's _get_quantized_spacing logic."""
        relative_duration = 1.0
        if spacing <= 2:    # e.g., "-f-" has a spacing of 2
            relative_duration = 1.0
        elif spacing == 3:  # e.g., "-f--" has a spacing of 3
            relative_duration = 2.0
        elif spacing == 4:  # e.g., "-f---" has a spacing of 4
            relative_duration = 4.0
        else:  # spacing >= 5
            relative_duration = 6.0  # Approximation for "> 4 units"

        return relative_duration * base_unit_in_beats

    @staticmethod
    def parse(tab_string: str, staccato: bool = False) -> Song:
        logger.debug("Starting ASCII Tab parsing.")
        song = Song()
        track = Track()

        tempo_match = re.search(r"Tempo:\s*([\d\.]+)", tab_string, re.IGNORECASE)
        if tempo_match:
            song.tempo = float(tempo_match.group(1))

        lines = tab_string.split('\n')
        tab_lines = [line for line in lines if re.match(r'^[eBGDAE]\|', line.strip())]
        if not tab_lines or len(tab_lines) % 6 != 0:
            logger.warning("Tab parsing failed: Invalid or empty tab lines.")
            return song

        full_strings = [""] * 6
        num_page_lines = len(tab_lines) // 6
        for i in range(num_page_lines):
            for j in range(6):
                line_content_raw = tab_lines[i * 6 + j].strip().split('|', 1)
                if len(line_content_raw) > 1:
                    tab_part = line_content_raw[1].replace('|', '')
                    full_strings[j] += tab_part
       
        # --- Pass 1: A more robust method to find all note events ---
        temp_events: List[_TabEvent] = []
        for string_idx, line in enumerate(full_strings):
            for match in re.finditer(r'(\d+)', line):
                fret = int(match.group(1))
                char_idx = match.start()
                tech = None
                if char_idx > 0 and line[char_idx - 1].isalpha():
                    tech_char = line[char_idx-1]
                    if tech_char == 'h': tech = "hammer-on"
                    elif tech_char == 'p': tech = "pull-off"
                temp_events.append(_TabEvent(char_idx, string_idx, fret, tech))
        
        logger.debug(f"Found {len(temp_events)} raw note events in the tab string.")

        # --- Pass 2: Calculate timing and add events directly to the track ---
        current_beat = 0.0
        last_char_idx = 0
        BASE_UNIT_IN_BEATS = 0.25

        events_by_char_idx = groupby(sorted(temp_events, key=lambda e: e.char_idx), key=lambda e: e.char_idx)
        
        for char_idx, group_iter in events_by_char_idx:
            spacing = char_idx - last_char_idx
            if spacing < 0: continue # Should not happen with sorted input, but a safeguard
            
            time_delta = AsciiTabParser._spacing_to_beats(spacing, BASE_UNIT_IN_BEATS)
            current_beat += time_delta
            
            for temp_event in group_iter:
                pitch = AsciiTabParser._tab_pos_to_midi(temp_event.string_idx, temp_event.fret)
                event = MusicalEvent(
                    time=current_beat, pitch=pitch, duration=0.5, velocity=90,
                    string=temp_event.string_idx, fret=temp_event.fret, technique=temp_event.technique
                )
                track.events.append(event)
            last_char_idx = char_idx
        
        logger.debug(f"Finished parsing. Total notes: {len(track.events)}. Final beat count: {current_beat:.2f}")

        # --- Pass 3: If staccato is enabled, modify the events now in the track ---
        if not staccato and len(track.events) > 1:
            logger.debug("Applying staccato processing.")
            sorted_events = sorted(track.events, key=lambda e: e.time)
            events_grouped_by_time = [list(g) for t, g in groupby(sorted_events, key=lambda e: e.time)]
            
            logger.debug(f"Grouped notes into {len(events_grouped_by_time)} distinct time slices.")
            
            if len(events_grouped_by_time) <= 1:
                logger.debug("Cannot apply staccato: only one time slice found. All notes may have the same start time.")
            else:
                for i in range(len(events_grouped_by_time) - 1):
                    current_group = events_grouped_by_time[i]
                    next_group = events_grouped_by_time[i+1]
                    duration = next_group[0].time - current_group[0].time
                    
                    logger.debug(f"Time: {current_group[0].time:<5.2f} | Notes: {str([e.pitch for e in current_group]):<15} | Old Duration: {current_group[0].duration:.2f} | New Duration: {duration:.2f}")

                    for event in current_group:
                        event.duration = duration
        elif staccato:
            logger.debug("Staccato flag set, skipping legato processing.")

        song.tracks.append(track)
        logger.debug("Finished creating Song object.")
        return song

    @staticmethod
    def _tab_pos_to_midi(string_idx: int, fret: int) -> int:
        open_string_pitches = [64, 59, 55, 50, 45, 40]
        return open_string_pitches[string_idx] + fret