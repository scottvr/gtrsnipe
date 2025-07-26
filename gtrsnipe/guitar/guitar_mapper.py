from typing import Tuple, List, Optional
from ..core.types import MusicalEvent
from .fretboard import FretboardMapper

class GuitarPositionMapper:
    def __init__(self):
        self.fretboard_mapper = FretboardMapper()
    
    def map_events(self, events: List[MusicalEvent], 
                  optimize_positions: bool = True,
                  prefer_techniques: bool = True) -> List[MusicalEvent]:
        previous_position = None
        guitar_events = []
        
        for event in events:
            try:
                technique = self._determine_technique(event) if prefer_techniques else None
                
                if optimize_positions:
                    position = self.fretboard_mapper.find_optimal_position(
                        pitch=event.pitch,
                        technique=technique,
                        previous_position=previous_position
                    )
                    print(f"[OP] Mapped MIDI note {event.pitch} to position {position}")
                    event.string = position.string
                    event.fret = position.fret
                    event.technique = technique
                    previous_position = position
                else:
                    pitch = self.fretboard_mapper.normalize_pitch(event.pitch)
                    positions = self.fretboard_mapper.pitch_to_positions[pitch]
                    position = next(iter(positions))
                    print(f"Mapped MIDI note {event.pitch} to position {position}")
                    event.string = position.string
                    event.fret = position.fret
                
                guitar_events.append(event)
                
            except (ValueError, KeyError) as e:
                print(f"Warning: Could not map pitch {event.pitch}: {str(e)}")
                continue
        
        return guitar_events
    
    def _determine_technique(self, event: MusicalEvent) -> Optional[str]:
        if event.velocity > 100:
            return "hammer-on"
        elif event.velocity < 50:
            return "pull-off"
        elif event.duration > 2.0:
            return "bend"
        return "pick"
