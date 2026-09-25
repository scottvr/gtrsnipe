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
    # Values are tuples of note names ordered LOW string to HIGH string
    # (e.g. STANDARD = E2 A2 D3 G3 B3 E4). Note: the internal string *index* is
    # still 0 = highest string; open-string pitches are derived by reversing these.
    STANDARD = ("E2", "A2", "D3", "G3", "B3", "E4")
    E_FLAT   = ("Eb2", "Ab2", "Db3", "Gb3", "Bb3", "Eb4")
    DROP_D   = ("D2", "A2", "D3", "G3", "B3", "E4")
    D_STANDARD = ("D2", "G2", "C3", "F3", "A3", "D4")
    DROP_C = ("C2", "G2", "C3", "F3", "A3", "D4")
    OPEN_G   = ("D2", "G2", "D3", "G3", "B3", "D4")
    OPEN_E = ("E2", "B2", "E3", "G#3", "B3", "E4")
    DADGAD = ("D2", "A2", "D3", "G3", "A3", "D4")
    OPEN_D = ("D2", "A2", "D3", "F#3", "A3", "D4")
    OPEN_C6 = ("C2", "A2", "C3", "G3", "C4", "E4")
    C_SHARP_STANDARD = ("C#2", "F#2", "B2", "E3", "G#3", "C#4")
    DROP_B = ("B1", "F#2", "B2", "E3", "G#3", "C#4")
    BASS_STANDARD = ("E1", "A1", "D2", "G2")
    BASS_DROP_D = ("D1", "A1", "D2", "G2")
    BASS_E_FLAT = ("Eb1", "Ab1", "Db2", "Gb2")
    SEVEN_STRING_STANDARD = ("B1", "E2", "A2", "D3", "G3", "B3", "E4")
    SEVEN_STRING_DROP_A = ("A1", "E2", "A2", "D3", "G3", "B3", "E4")
    BARITONE_B = ("B1", "E2", "A2", "D3", "F#3", "B3")
    BARITONE_A = ("A1", "D2", "G2", "C3", "E3", "A3")
    BARITONE_C = ("C2", "F2", "Bb2", "Eb3", "G3", "C4")
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