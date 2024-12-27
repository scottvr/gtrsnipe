from dataclasses import dataclass
from enum import Enum
from typing import Dict, Set, Optional, List
from gtrsnipe import FretPosition, Tuning

class TechniqueRestrictions:
    @staticmethod
    def is_valid_position(technique: str, pos: FretPosition) -> bool:
        """Check if a technique can be performed at a given position"""
        match technique:
            case "tap":
                return pos.fret > 0
            case "hammer-on":
                return pos.fret > 0
            case "pull-off":
                return pos.fret > 0
            case "bend":
                return 0 < pos.fret < 20
            case "slide":
                return pos.fret < 22
            case "pick":
                return True
            case _:
                return True

class FretboardMapper:
    def __init__(self, max_fret: int = 24, tuning: Tuning = Tuning.STANDARD):
        self.max_fret = max_fret
        self.tuning = tuning
        self.reference_pitch = 40  # Adjusted for typical guitar range
#        self.string_offsets = [0, -5, -9, -14, -19, -24]
        self.string_offsets = self._calculate_string_offsets()
        self._build_pitch_maps()

    def _calculate_string_offsets(self) -> List[int]:
        note_to_offset = {'E': 0, 'A': -5, 'D': -10, 'G': -15, 'B': -19, 'F': -17}
        return [note_to_offset[note] for note in self.tuning.value]
    
    def normalize_pitch(self, pitch: int) -> int:
        """Normalize MIDI pitch to guitar range"""
        while pitch > max(self.pitch_to_positions.keys()):
            pitch -= 12
        while pitch < min(self.pitch_to_positions.keys()):
            pitch += 12
        return pitch

    def _build_pitch_maps(self):
        """Build mappings between pitches and fretboard positions"""
        self.pitch_to_positions: Dict[int, Set[FretPosition]] = {}
        self.position_to_pitch: Dict[FretPosition, int] = {}
        
        for string in range(6):
            base_pitch = self.reference_pitch + self.string_offsets[string]
            for fret in range(self.max_fret + 1):
                pitch = base_pitch + fret
                pos = FretPosition(string, fret)
                
                if pitch not in self.pitch_to_positions:
                    self.pitch_to_positions[pitch] = set()
                self.pitch_to_positions[pitch].add(pos)
                self.position_to_pitch[pos] = pitch
    
    def find_optimal_position(self, 
                            pitch: int, 
                            technique: Optional[str],
                            previous_position: Optional[FretPosition] = None) -> FretPosition:
        """Find best playable position considering technique and context"""
        norm_pitch = self.normalize_pitch(pitch)
        if norm_pitch not in self.pitch_to_positions:
            raise ValueError(f"Pitch {pitch} cannot be mapped to guitar")
            
        positions = self.pitch_to_positions[norm_pitch]
        valid_positions = {
            pos for pos in positions 
            if TechniqueRestrictions.is_valid_position(technique, pos)
        }
        
        if not valid_positions:
            raise ValueError(f"No valid positions found for {technique}")
        
        scored_positions = [
            (self._score_position(pos, technique, previous_position), pos)
            for pos in positions 
        ]
        return max(scored_positions, key=lambda pos: 
                  pos[0])[1]
    
    def _score_position(self, 
                       pos: FretPosition, 
                       technique: Optional[str],
                       previous_position: Optional[FretPosition]) -> float:
        score = 0.0
        print(f"SCDEBUG: {pos} {technique} {previous_position}")      
        # Prefer middle strings
        score -= abs(pos.string - 2) * 0.5
        
        print(f"    SCDEBUG: post-mideval {score}")      
        # Prefer lower frets
        score -= pos.fret * 0.1
        
        print(f"    SCDEBUG: post-lowfreval {score}")      
        # Consider previous position if available
        if previous_position:
            distance = abs(pos.string - previous_position.string) + \
                      abs(pos.fret - previous_position.fret)
            score -= distance * 0.3
            print(f"    SCDEBUG: post-prevdeval {score}")      

        # Technique-specific preferences
        if technique:
            match technique:
                case "tap":
                    if 5 <= pos.fret <= 15:
                        score += 10
                case "hammer-on" | "pull-off":
                    if 3 <= pos.fret <= 15:
                        score += 8
                    elif pos.fret < 3:
                        score -= 2.0
                case "bend":
                    if pos.fret < 12:
                        score += 5
                    elif pos.fret > 15:
                        score -= 3.0
                case "slide":
                    if 5 <= pos.fret <= 15:
                        score += 5
            print(f"    SCDEBUG: post-techqeval {score}")      
        
        return score