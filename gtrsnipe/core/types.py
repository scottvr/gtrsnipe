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
    E_FLAT   = ("Eb4", "Bb3", "Gb3", "Db3", "Ab2", "Eb2")
    DROP_D   = ("E4", "B3", "G3", "D3", "A2", "D2")
    D_STANDARD = ("D4", "A3", "F3", "C3", "G2", "D2")
    DROP_C = ("D4", "A3", "F3", "C3", "G2", "C2")
    OPEN_G   = ("D4", "B3", "G3", "D3", "G2", "D2")
    OPEN_E = ("E4", "B3", "G#3", "E3", "B2", "E2")
    DADGAD = ("D4", "A3", "G3", "D3", "A2", "D2")
    OPEN_D = ("D4", "A3", "F#3", "D3", "A2", "D2")
    OPEN_C6 = ("E4", "C4", "G3", "C3", "A2", "C2")
    C_SHARP_STANDARD = ("C#4", "G#3", "E3", "B2", "F#2", "C#2")
    DROP_B= ("C#4", "G#3", "E3", "B2", "F#2", "B1")
    BASS_STANDARD = ("G2", "D2", "A1", "E1")
    BASS_DROP_D = ("G2", "D2", "A1", "D1")
    BASS_E_FLAT = ("Gb2", "Db2", "Ab1", "Eb1")
    SEVEN_STRING_STANDARD = ("E4", "B3", "G3", "D3", "A2", "E2", "B1")
    SEVEN_STRING_DROP_A = ("E4", "B3", "G3", "D3", "A2", "E2", "A1")
    BARITONE_B = ("B3", "F#3", "D3", "A2", "E2", "B1")
    BARITONE_A = ("A3", "E3", "C3", "G2", "D2", "A1")
    BARITONE_C = ("C4", "G3", "Eb3", "Bb2", "F2", "C2")    
@dataclass(frozen=True, order=True)
class FretPosition:
    string: int  # 0 (highest-pitched string) to num_strings-1
    fret: int    # 0 (open) to max_fret
    
    def __str__(self):
        # Generic representation to avoid errors with different tunings
        return f"S{self.string}:F{self.fret}"

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
class TempoEvent: 
    time: float
    bpm: float
@dataclass
class Song:
    """A universal, format-agnostic representation of a song."""
    tracks: List[Track] = field(default_factory=list)
    tempo: float = 120.0
    time_signature: str = "4/4"
    title: str = "Untitled"
    tempo_events: List[TempoEvent] = field(default_factory=list)