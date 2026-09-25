from dataclasses import dataclass
from typing import List, Optional
import re
from ...core.types import MusicalEvent, Song, Track
from ...core.theory import note_name_to_pitch
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
    def parse(tab_string: str, staccato: bool = False, quantization_resolution: float = 0.125,
              open_string_pitches: Optional[List[int]] = None) -> Song:
        logger.debug("Starting ASCII Tab parsing.")
        song = Song()
        track = Track()

        tempo_match = re.search(r"Tempo:\s*([\d\.]+)", tab_string, re.IGNORECASE)
        if tempo_match:
            song.tempo = float(tempo_match.group(1))

        # Read the embedded tuning header so a generated tab round-trips in its own
        # tuning (unless the caller supplied one explicitly, which wins). Handles
        # the current 'Tuning: <low..high>' and the legacy 'Tuning (High to Low): ...'.
        if open_string_pitches is None:
            hm = re.search(r"//\s*Tuning([^:]*):\s*(.+)", tab_string, re.IGNORECASE)
            if hm:
                names = [x for x in re.split(r"[,\s]+", hm.group(2).strip()) if x]
                try:
                    pitches = [note_name_to_pitch(x) for x in names]
                    # index 0 = highest string; names low->high unless labeled otherwise.
                    open_string_pitches = (pitches if "high to low" in hm.group(1).lower()
                                           else list(reversed(pitches)))
                except ValueError:
                    open_string_pitches = None  # unparseable header -> fall back

        lines = tab_string.split('\n')
        # A tab line is a short (1-3 char) string label then '|' — accepts any
        # tuning's labels (not just eBGDAE), and comment lines never match.
        def _is_tab_line(s):
            return bool(re.match(r'^\s*[^\s|]{1,3}\|', s))
        tab_lines = [line for line in lines if _is_tab_line(line)]

        # 1. First, simply check if any tab lines were found at all.
        if not tab_lines:
            logger.warning("Tab parsing failed: No valid tab lines found in the input.")
            return song

        # 2. Determine strings per block: the tuning header's count if known,
        # else the length of the first contiguous run of tab lines (robust to
        # duplicate labels like the two E strings, which the old start-char scan
        # mis-counted as 5).
        if open_string_pitches:
            num_strings = len(open_string_pitches)
        else:
            num_strings = 0
            for line in lines:
                if _is_tab_line(line):
                    num_strings += 1
                elif num_strings:
                    break

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

        TIME_PER_CHAR_IN_BEATS = quantization_resolution

        if not temp_events:
            logger.warning("No notes found in tab string.")
        else:
            # We don't need to group by index anymore; we can process each note directly.
            for temp_event in temp_events:
                # The note's time is its character index multiplied by the time per character.
                note_time = temp_event.char_idx * TIME_PER_CHAR_IN_BEATS

                pitch = AsciiTabParser._tab_pos_to_midi(temp_event.string_idx, temp_event.fret, num_strings, open_string_pitches)
                
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
    def _tab_pos_to_midi(string_idx: int, fret: int, num_strings: int,
                         open_string_pitches: Optional[List[int]] = None) -> int:
        """Converts a string/fret position to a MIDI pitch.

        Uses the caller-supplied ``open_string_pitches`` (high->low) when given —
        so a tab is decoded in its actual tuning — else falls back to standard
        guitar/bass tuning by string count.
        """
        if not open_string_pitches:
            # Standard 6-String Guitar (high->low) / 4-String Bass fallback.
            guitar_tuning = [64, 59, 55, 50, 45, 40]
            bass_tuning = [43, 38, 33, 28]  # G2, D2, A1, E1
            open_string_pitches = bass_tuning if num_strings == 4 else guitar_tuning

        # Ensure we don't go out of bounds if string_idx is too high
        if string_idx >= len(open_string_pitches):
            logger.error(f"Invalid string index {string_idx} for a {num_strings}-string instrument.")
            return 0 # Return a default, silent pitch
    
        return open_string_pitches[string_idx] + fret