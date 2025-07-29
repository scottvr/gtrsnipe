from dataclasses import dataclass
from itertools import product
from typing import Dict, Set, Optional, List, Tuple
from itertools import groupby
from ..core.types import MusicalEvent, FretPosition, Tuning, Technique
from ..core.config import MapperConfig
from ..core.theory import note_name_to_pitch

import logging

logger = logging.getLogger(__name__)

Fingering = Tuple[FretPosition, ...]

class GuitarMapper:
    def __init__(self, config: MapperConfig):
        self.config = config
        tuning_str = self.config.tuning.upper()
        try:
            self.tuning = Tuning[self.config.tuning.upper()]
        except KeyError:
            logger.warning(f"Unknown tuning '{self.config.tuning}'. Defaulting to STANDARD.")
        self.open_string_pitches = [note_name_to_pitch(n) for n in self.tuning.value] 
        self.pitch_to_positions: Dict[int, Set[FretPosition]] = {}
        self._build_pitch_maps()
        logger.info("--- Chord-Aware Mapper initialized. ---")

    def _build_pitch_maps(self):
        for string_idx, base_pitch in enumerate(self.open_string_pitches):
            for fret in range(self.config.max_fret + 1):
                pitch = base_pitch + fret
                pos = FretPosition(string_idx, fret)
                if pitch not in self.pitch_to_positions:
                    self.pitch_to_positions[pitch] = set()
                self.pitch_to_positions[pitch].add(pos)                
    
    def _map_to_single_string(self, events: List[MusicalEvent], string_index: int) -> List[MusicalEvent]:
        open_string_pitch = self.open_string_pitches[string_index]
        mapped_events = []
        for event in sorted(events, key=lambda e: e.time):
            fret = event.pitch - open_string_pitch
            if 0 <= fret <= self.config.max_fret:
                event.string = string_index
                event.fret = fret
                mapped_events.append(event)
            else:
                logger.warning(f"Note with pitch {event.pitch} is unplayable on string {string_index+1} (fret {fret}) and was dropped.")
        return mapped_events

    def _normalize_pitch(self, pitch: int) -> int:
        """Transposes a pitch by octaves until it is within the playable range of the instrument."""
        # Get the min and max pitches once to avoid recalculating in the loop
        min_pitch = min(self.pitch_to_positions.keys())
        max_pitch = max(self.pitch_to_positions.keys())
        
        while pitch > max_pitch:
            pitch -= 12
        while pitch < min_pitch:
            pitch += 12
        return pitch

    def _score_fingering(self, fingering: Fingering, prev_fingering: Optional[Fingering]) -> float:
        """Scores a fingering based on internal shape, position, and transition cost."""
        
        # 1. Internal Shape Score (Compactness)
        if self.config.ignore_open:
            frets = [pos.fret for pos in fingering if pos.fret > 0]
        else:
            frets = [pos.fret for pos in fingering]
        fret_span = (max(frets) - min(frets)) if frets else 0
        if fret_span > self.config.unplayable_fret_span:
            return -1000
        score = -fret_span * self.config.fret_span_penalty 

        # 2. Positional Score (Where on the neck?)
        if fingering:
            avg_fret = sum(p.fret for p in fingering) / len(fingering)
            if self.config.sweet_spot_low <= avg_fret <= self.config.sweet_spot_high:
                score += self.config.sweet_spot_bonus
            elif avg_fret > self.config.sweet_spot_high:
                positional_penalty = (avg_fret - self.config.sweet_spot_high) * self.config.high_fret_penalty
                strings_used = {pos.string for pos in fingering}
                if any(s >= 4 for s in strings_used): # Penalize high frets on low strings more
                    positional_penalty *= self.config.low_string_high_fret_multiplier
                score -= positional_penalty

        # 3. Transition Score (Cost of movement from previous fingering)
        if prev_fingering and fingering:
            # Penalize movement up/down the neck
            avg_current_fret = sum(p.fret for p in fingering) / len(fingering)
            avg_prev_fret = sum(p.fret for p in prev_fingering) / len(prev_fingering)
            fret_diff = abs(avg_current_fret - avg_prev_fret)
            score -= fret_diff * self.config.movement_penalty
            
            # Penalize changing strings
            strings_used = {pos.string for pos in fingering}
            prev_strings_used = {pos.string for pos in prev_fingering}
            string_changes = len(strings_used.symmetric_difference(prev_strings_used))
            score -= string_changes * self.config.string_switch_penalty

        return score
    
    def _find_optimal_fingering(self, notes: List[MusicalEvent], prev_fingering: Optional[Fingering]) -> Optional[Fingering]:
        note_positions = []
        for note in notes:
            norm_pitch = self._normalize_pitch(note.pitch)            
            positions = self.pitch_to_positions.get(norm_pitch)
            if not positions: return None
            note_positions.append(positions)

        all_combinations = product(*note_positions)
        best_fingering = None
        max_score = -float('inf')

        for fingering in all_combinations:
            strings_used = {pos.string for pos in fingering}
            if len(strings_used) != len(fingering):
                continue

            score = self._score_fingering(fingering, prev_fingering)
            
            logger.debug(f"considering score: {score} {fingering}")
            if score > max_score:
                max_score = score
                best_fingering = fingering
        logger.debug(f"best score: {max_score} {best_fingering}")
        return best_fingering


    def _infer_technique_between_notes(self, prev_event: MusicalEvent, curr_event: MusicalEvent) -> str:
        if prev_event.fret is None or curr_event.fret is None: return Technique.PICK.value
        time_delta = curr_event.time - prev_event.time
        if time_delta < 0.01: return Technique.PICK.value
        if prev_event.string != curr_event.string: return Technique.PICK.value
        if time_delta > self.config.legato_time_threshold: return Technique.PICK.value
        if curr_event.fret > prev_event.fret: return Technique.HAMMER.value
        if curr_event.fret < prev_event.fret: return Technique.PULL.value
        return Technique.PICK.value

    def _infer_techniques_from_positions(self, mapped_events: List[MusicalEvent], no_articulations: bool, single_string_mode: bool = False) -> List[MusicalEvent]:
        if no_articulations or not mapped_events:
            if mapped_events:
                for event in mapped_events: event.technique = Technique.PICK.value
            return mapped_events

        # --- Pass 1: Infer base techniques (pick, hammer-on, pull-off) for all notes ---
        events_with_base_techniques = [mapped_events[0]]
        mapped_events[0].technique = Technique.PICK.value

        for i in range(1, len(mapped_events)):
            prev_event = mapped_events[i-1]
            curr_event = mapped_events[i]
            curr_event.technique = self._infer_technique_between_notes(prev_event, curr_event)
            events_with_base_techniques.append(curr_event)

        # --- Pass 2: If in single-string mode, identify runs and mark the highest note as a 'tap' ---
        if single_string_mode:
            runs, current_run = [], []
            for event in events_with_base_techniques:
                if event.technique == Technique.PICK.value:
                    if current_run: runs.append(current_run)
                    current_run = [event]
                else:
                    current_run.append(event)
            if current_run: runs.append(current_run)

            for run in runs:
                # Tapping is usually for runs of 3+ notes (e.g., pick-pull-tap)
                # This also prevents simple hammer-ons (e.g., 5h7) from becoming taps.
                if len(run) > self.config.tapping_run_threshold:
                    highest_pitch = max(e.pitch for e in run)

                    # If the highest note only appears once and is the first note,
                    # it's likely a descending run (e.g., 7p5p3), not a tapping one.
                    is_descending_run = sum(1 for e in run if e.pitch == highest_pitch) == 1 and run[0].pitch == highest_pitch

                    if not is_descending_run:
                        for note in run:
                            if note.pitch == highest_pitch:
                                note.technique = Technique.TAP.value
            
        return events_with_base_techniques
    
    def map_events_to_fretboard(self, events: List[MusicalEvent], no_articulations: bool, single_string: Optional[int] = None) -> List[MusicalEvent]:
        if not events: return []
        
        mapped_events: List[MusicalEvent]
        
        if single_string is not None:
            logger.info(f"--- Single-string mode active. Mapping all notes to string {single_string}. ---")
            string_index = single_string - 1
            mapped_events = self._map_to_single_string(events, string_index)
        else:
            QUANTIZATION_RESOLUTION = 0.125
            def quantize_time(beat): return round(beat / QUANTIZATION_RESOLUTION) * QUANTIZATION_RESOLUTION
            
            sorted_events = sorted(events, key=lambda e: e.time)
            time_groups = [list(g) for t, g in groupby(sorted_events, key=lambda e: quantize_time(e.time))]

            multi_string_events = []
            last_fingering: Optional[Fingering] = None
            for note_group in time_groups:
                unique_pitches = {}
                deduplicated_note_group = []
                for note in note_group:
                    norm_pitch = self._normalize_pitch(note.pitch)
                    if norm_pitch not in unique_pitches:
                        unique_pitches[norm_pitch] = note
                        deduplicated_note_group.append(note)

                fingering = self._find_optimal_fingering(deduplicated_note_group, last_fingering)
                if fingering:
                    # The fingering corresponds to the deduplicated notes.
                    # We need to apply it back to the correct note events.
                    for i, note_event in enumerate(deduplicated_note_group):
                        note_event.fret = fingering[i].fret
                        note_event.string = fingering[i].string
                    multi_string_events.extend(deduplicated_note_group)
                    last_fingering = fingering
                else:
                    logger.warning(f"Could not find a playable fingering for notes at time {note_group[0].time}")
            mapped_events = multi_string_events

        return self._infer_techniques_from_positions(mapped_events, no_articulations, single_string_mode=(single_string is not None))
