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
    def _tab_pos_to_midi(string_idx: int, fret: int) -> int:
        open_string_pitches = [64, 59, 55, 50, 45, 40]
        return open_string_pitches[string_idx] + fret