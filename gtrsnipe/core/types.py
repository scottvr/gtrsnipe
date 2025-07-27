from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Tuple, List

@dataclass
class TimeSignature:
    numerator: int = 4
    denominator: int = 4
    
    def as_tuple(self) -> Tuple[int, int]:
        return (self.numerator, self.denominator)

    def __str__(self) -> str:
        """Returns the time signature as a string, e.g., '4/4'."""
        return f"{self.numerator}/{self.denominator}"

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
    # Values are tuples of note names from high E (string 1) to low E (string 6)
    STANDARD = ("E4", "B3", "G3", "D3", "A2", "E2")
    DROP_D   = ("E4", "B3", "G3", "D3", "A2", "D2")
    OPEN_G   = ("D4", "B3", "G3", "D3", "G2", "D2")

@dataclass(frozen=True, order=True)
class FretPosition:
    string: int  # 0 (high E) to 5 (low E)
    fret: int    # 0 (open) to max_fret
    
    def __str__(self):
        string_names = ['e', 'B', 'G', 'D', 'A', 'E']
        return f"{string_names[self.string]}:{self.fret}"

@dataclass
class MusicalEvent:
    time: float          # Time in beats
    pitch: int          # MIDI pitch number
    duration: float     # Duration in beats
    velocity: int       # MIDI velocity (0-127)
    string: Optional[int] = None
    fret: Optional[int] = None
    technique: Optional[str] = None

@dataclass
class Track:
    """Represents a single track of music."""
    events: List[MusicalEvent] = field(default_factory=list)
    instrument_name: str = "Acoustic Grand Piano"

@dataclass
class Song:
    """A universal, format-agnostic representation of a song."""
    tracks: List[Track] = field(default_factory=list)
    tempo: float = 120.0
    time_signature: str = "4/4"
    title: str = "Untitled"