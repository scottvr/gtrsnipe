from dataclasses import dataclass
from itertools import product
from typing import Dict, Set, Optional, List, Tuple
from itertools import groupby
from ..core.types import MusicalEvent, FretPosition, Tuning
import logging

logger = logging.getLogger(__name__)

# A Fingering is a tuple of FretPosition objects, representing one possible way to play a chord.
Fingering = Tuple[FretPosition, ...]

class GuitarMapper:
    def __init__(self, max_fret: int = 24, tuning: Tuning = Tuning.STANDARD):
        self.max_fret = max_fret
        self.tuning = tuning
        self.reference_pitch = 40
        self.string_offsets = self._calculate_string_offsets()
        self._build_pitch_maps()
        logger.info("--- Chord-Aware Mapper initialized. ---")

    def _get_open_string_pitches(self, tuning: Tuning) -> List[int]:
        if tuning == Tuning.STANDARD: return [64, 59, 55, 50, 45, 40]
        return [64, 59, 55, 50, 45, 40]

    def _calculate_string_offsets(self) -> List[int]:
        offsets_low_to_high = [0, 5, 10, 15, 19, 24]
        return list(reversed(offsets_low_to_high))

    def _build_pitch_maps(self):
        self.pitch_to_positions: Dict[int, Set[FretPosition]] = {}
        for string in range(6):
            base_pitch = self.reference_pitch + self.string_offsets[string]
            for fret in range(self.max_fret + 1):
                pitch = base_pitch + fret
                pos = FretPosition(string, fret)
                if pitch not in self.pitch_to_positions:
                    self.pitch_to_positions[pitch] = set()
                self.pitch_to_positions[pitch].add(pos)
                
    def _normalize_pitch(self, pitch: int) -> int:
        keys = self.pitch_to_positions.keys()
        while pitch > max(keys): pitch -= 12
        while pitch < min(keys): pitch += 12
        return pitch

    def _score_fingering(self, fingering: Fingering, prev_fingering: Optional[Fingering]) -> float:
        """Scores a complete chord fingering based on compactness, movement, and position."""
        # --- Weights ---
        FRET_SPAN_PENALTY_WEIGHT = 100  # Heavy penalty for wide fret stretches
        MOVEMENT_PENALTY_WEIGHT = 3   # Penalty for distance from previous hand position
        HIGH_FRET_PENALTY_WEIGHT = 0.4  # Penalty for playing high on the neck
        SWEET_SPOT_BONUS = 0.5          # Bonus for playing in the ideal fret range

        # Compactness Score (Cluster Score)
        frets = [pos.fret for pos in fingering if pos.fret > 0]
        #frets = [pos.fret for pos in fingering]
        fret_span = (max(frets) - min(frets)) if frets else 0

        # Heavily penalize unplayable fret spans
        if fret_span > 4:
            return -1000

        score = -fret_span * FRET_SPAN_PENALTY_WEIGHT

        # Movement Score
        if prev_fingering:
            avg_current_fret = sum(p.fret for p in fingering) / len(fingering)
            avg_prev_fret = sum(p.fret for p in prev_fingering) / len(prev_fingering)
            fret_diff = abs(avg_current_fret - avg_prev_fret)
            score -= fret_diff * MOVEMENT_PENALTY_WEIGHT

        avg_fret = sum(p.fret for p in fingering) / len(fingering)
        
        if 0 <= avg_fret <= 12:
            score += SWEET_SPOT_BONUS
        elif avg_fret > 12:
            positional_penalty = (avg_fret - 12) * HIGH_FRET_PENALTY_WEIGHT
            
            # Check if the fingering uses the lowest strings
            # Low E string is index 5, A string is 4
            strings_used = [pos.string for pos in fingering]
            if any(s >= 4 for s in strings_used):
                positional_penalty *= 1.5 # Make penalty 50% worse on low strings
            
            score -= positional_penalty

        return score

    def _find_optimal_fingering(self, notes: List[MusicalEvent], prev_fingering: Optional[Fingering]) -> Optional[Fingering]:
        """Finds the best way to play a chord by evaluating all fingering combinations."""
        
        # Get all possible fret positions for each note in the chord
        note_positions = []
        for note in notes:
            norm_pitch = self._normalize_pitch(note.pitch)
            positions = self.pitch_to_positions.get(norm_pitch)
            if not positions: return None # Note is unplayable
            note_positions.append(positions)

        # Generate all fingering combinations (e.g., [(C_pos1, E_pos1), (C_pos1, E_pos2), ...])
        all_combinations = product(*note_positions)

        best_fingering = None
        max_score = -float('inf')

        for fingering in all_combinations:
            # Rule out invalid fingerings (e.g., two notes on the same string)
            strings_used = [pos.string for pos in fingering]
            if len(strings_used) != len(set(strings_used)):
                continue

            score = self._score_fingering(fingering, prev_fingering)
            if score > -1000: logger.debug(f"considered fingering scored {score}") 
            if score > max_score:
                max_score = score
                best_fingering = fingering
        logger.debug(f"score of best fingering = {max_score}")
        return best_fingering

    def _infer_techniques_from_positions(self, mapped_events: List[MusicalEvent], no_articulations: bool) -> List[MusicalEvent]:
        if no_articulations:
            return mapped_events
        """Second pass to determine legato techniques based on final positions."""
        if not mapped_events: return []
            
        final_events = [mapped_events[0]]
        for i in range(1, len(mapped_events)):
            prev_event = mapped_events[i-1]
            curr_event = mapped_events[i]
            inferred_technique = self._infer_technique_between_notes(prev_event, curr_event)
            curr_event.technique = inferred_technique
            final_events.append(curr_event)
        return final_events

    def _infer_technique_between_notes(self, prev_event: MusicalEvent, curr_event: MusicalEvent) -> str:
        if prev_event.fret is None or curr_event.fret is None: return "pick"

        time_delta = curr_event.time - prev_event.time

        # If notes are simultaneous (a chord) or too close, it's not a legato link.
        # Use a small epsilon to handle floating point inaccuracies.
        if time_delta < 0.01:
            return "pick"
            
        # Check if notes are on the same string for a legato phrase.
        if prev_event.string != curr_event.string: return "pick"
        
        # Increase the time threshold to be more lenient for fast passages.
        # This allows up to an eighth note's duration between legato notes.
        if time_delta > 0.5: return "pick"
        
        if curr_event.fret > prev_event.fret: return "hammer-on"
        if curr_event.fret < prev_event.fret: return "pull-off"
        
        return "pick"
    
    def map_events_to_fretboard(self, events: List[MusicalEvent], no_articulations: bool) -> List[MusicalEvent]:
        """Maps musical events to a fretboard, considering chords as a whole."""
        if not events: return []
        
        # --- Step 1: Group events by quantized time to identify chords ---
        QUANTIZATION_RESOLUTION = 0.125
        def quantize_time(beat): return round(beat / QUANTIZATION_RESOLUTION) * QUANTIZATION_RESOLUTION
        
        sorted_events = sorted(events, key=lambda e: e.time)
        time_groups = [list(g) for t, g in groupby(sorted_events, key=lambda e: quantize_time(e.time))]

        # --- Step 2: Map each time group (note or chord) holistically ---
        mapped_events = []
        last_fingering: Optional[Fingering] = None

        for note_group in time_groups:
            # Set a default "pick" technique before finding the position.
            # This will be corrected for legato notes in the final pass.
            for note in note_group:
                note.technique = "pick"
                
            fingering = self._find_optimal_fingering(note_group, last_fingering)
            logger.debug(f"best fingering: {fingering}") 
            if fingering:
                for i, note_event in enumerate(note_group):
                    note_event.fret = fingering[i].fret
                    note_event.string = fingering[i].string
                mapped_events.extend(note_group)
                last_fingering = fingering
            else:
                logger.warning(f"Could not find a playable fingering for notes at time {note_group[0].time}")

        # This function analyzes the final positions to find hammer-ons and pull-offs.
        return self._infer_techniques_from_positions(mapped_events, no_articulations=no_articulations)