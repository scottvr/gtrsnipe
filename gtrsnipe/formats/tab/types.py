from typing import Tuple, Optional, List
from dataclasses import dataclass, field
from ...core.types import FretPosition, Technique

@dataclass
class TabNote:
    """Represents a single note within a measure for formatting purposes."""
    position: FretPosition
    beat_in_measure: float
    technique: Optional[Technique] = None
    duration: float = 1.0

@dataclass
class TabMeasure:
    """Represents a measure of tab."""
    notes: List[TabNote]
    time_signature: Tuple[int, int]

@dataclass
class TabScore:
    """Represents a complete tab score to be formatted."""
    measures: List[TabMeasure] = field(default_factory=list)
    title: str = "Untitled"
    tuning_name: str = "STANDARD"
    time_signature: Tuple[int, int] = (4, 4)
    tempo: float = 120.0
