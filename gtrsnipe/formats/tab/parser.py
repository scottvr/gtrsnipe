from dataclasses import dataclass
from typing import List, Optional
import re
from ...core.types import MusicalEvent, Song, Track
from itertools import groupby
import logging

logger = logging.getLogger(__name__)

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
    def parse(tab_string: str, staccato: bool = False, quantization_resolution: float = 0.125) -> Song:
        logger.debug("Starting ASCII Tab parsing.")
        song = Song()
        track = Track()

        tempo_match = re.search(r"Tempo:\s*([\d\.]+)", tab_string, re.IGNORECASE)
        if tempo_match:
            song.tempo = float(tempo_match.group(1))

        lines = tab_string.split('\n')
        tab_lines = [line for line in lines if re.match(r'^[eBGDAE]\|', line.strip())]

        # 1. First, simply check if any tab lines were found at all.
        if not tab_lines:
            logger.warning("Tab parsing failed: No valid tab lines found in the input.")
            return song

        # 2. Dynamically determine the number of strings per block.
        # We do this by counting lines until we see a repeated string name (like a second 'G|').
        num_strings = 0
        seen_starts = set()
        for line in tab_lines:
            # Get the starting character (e.g., 'G')
            start_char = line.strip()[0].upper()
            if start_char in seen_starts:
                break # We've found the start of the next page, so we know the string count.
            seen_starts.add(start_char)
            num_strings += 1

        if num_strings == 0:
            logger.warning("Tab parsing failed: Could not determine the number of strings.")
            return song

        logger.debug(f"Dynamically detected {num_strings} strings per block.")

        # 3. Use the dynamic num_strings value to parse correctly.
        full_strings = [""] * num_strings
        num_page_lines = len(tab_lines) // num_strings
        for i in range(num_page_lines):
            for j in range(num_strings):
                line_index = i * num_strings + j
                # Safety check in case of malformed tabs with incomplete last pages
                if line_index < len(tab_lines):
                    line_content_raw = tab_lines[line_index].strip().split('|', 1)
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

        print(f"DEBUG PARSER: Number of raw events found = {len(temp_events)}")

        TIME_PER_CHAR_IN_BEATS = quantization_resolution

        if not temp_events:
            logger.warning("No notes found in tab string.")
        else:
            # We don't need to group by index anymore; we can process each note directly.
            for temp_event in temp_events:
                # The note's time is its character index multiplied by the time per character.
                note_time = temp_event.char_idx * TIME_PER_CHAR_IN_BEATS

                pitch = AsciiTabParser._tab_pos_to_midi(temp_event.string_idx, temp_event.fret, num_strings)
                
                # A reasonable default duration is one time step.
                # The legato pass will adjust this later.
                duration = TIME_PER_CHAR_IN_BEATS

                event = MusicalEvent(
                    time=note_time,
                    pitch=pitch,
                    duration=duration,
                    velocity=90,
                    string=temp_event.string_idx,
                    fret=temp_event.fret,
                    technique=temp_event.technique
                )
                track.events.append(event)
        
            # Recalculate the final beat for logging purposes if needed
            last_event_time = max(e.time for e in track.events) if track.events else 0.0
            logger.debug(f"Finished parsing. Total notes: {len(track.events)}. Final beat count: {last_event_time:.2f}")

        # --- Pass 3: If staccato is enabled, modify the events now in the track ---
        if not staccato and len(track.events) > 1:
            logger.debug("Applying legato processing.")
            sorted_events = sorted(track.events, key=lambda e: e.time)
            events_grouped_by_time = [list(g) for t, g in groupby(sorted_events, key=lambda e: e.time)]
            
            logger.debug(f"Grouped notes into {len(events_grouped_by_time)} distinct time slices.")
            
            if len(events_grouped_by_time) <= 1:
                logger.debug("Cannot apply legato: only one time slice found. All notes may have the same start time.")
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
    def _tab_pos_to_midi(string_idx: int, fret: int, num_strings: int) -> int:
        """Converts a string/fret position to a MIDI pitch based on the instrument type."""
        # Standard 6-String Guitar Tuning (High to Low)
        guitar_tuning = [64, 59, 55, 50, 45, 40] 
        # Standard 4-String Bass Tuning (High to Low)
        bass_tuning = [43, 38, 33, 28] # G2, D2, A1, E1
    
        open_string_pitches = []
        if num_strings == 4:
            open_string_pitches = bass_tuning
        elif num_strings == 6:
            open_string_pitches = guitar_tuning
        else:
            # Default to guitar tuning if the string count is unusual
            open_string_pitches = guitar_tuning
    
        # Ensure we don't go out of bounds if string_idx is too high
        if string_idx >= len(open_string_pitches):
            logger.error(f"Invalid string index {string_idx} for a {num_strings}-string instrument.")
            return 0 # Return a default, silent pitch
    
        return open_string_pitches[string_idx] + fret