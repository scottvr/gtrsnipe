from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple, List

@dataclass
class TimeSignature:
    numerator: int = 4
    denominator: int = 4
    
    def as_tuple(self) -> Tuple[int, int]:
        return (self.numerator, self.denominator)

class Technique(Enum):
    PICK = "pick"
    HAMMER = "hammer-on"
    PULL = "pull-off"
    BEND = "bend"
    SLIDE = "slide"
    TAP = "tap"
    HARMONIC = "harmonic"
    PALM_MUTE = "palm-mute"

class Tuning(Enum):
    STANDARD = ['E', 'A', 'D', 'G', 'B', 'E']
    DROP_D = ['D', 'A', 'D', 'G', 'B', 'E']
    OPEN_G = ['D', 'G', 'D', 'G', 'B', 'D']

@dataclass
class MusicalEvent:
    time: float          # Time in beats
    pitch: int          # MIDI pitch number
    duration: float     # Duration in beats
    velocity: int       # MIDI velocity (0-127)
    string: Optional[int] = None
    fret: Optional[int] = None
    technique: Optional[str] = None

@dataclass(frozen=True, order=True)
class FretPosition:
    string: int  # 0 (high E) to 5 (low E)
    fret: int    # 0 (open) to max_fret
    
    def __str__(self):
        string_names = ['e', 'B', 'G', 'D', 'A', 'E']
        return f"{string_names[self.string]}:{self.fret}"