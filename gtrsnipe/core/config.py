from dataclasses import dataclass
from .types import Tuning

@dataclass
class MapperConfig:
    """Holds all tunable parameters for the GuitarMapper's scoring algorithm."""
    # From _score_fingering
    fret_span_penalty: float = 100.0
    movement_penalty: float = 3.0
    string_switch_penalty: float = 10.0
    high_fret_penalty: float = 5.0
    low_string_high_fret_multiplier: float =10.0 
    sweet_spot_bonus: float = 0.5
    unplayable_fret_span: int = 4
    sweet_spot_low: int = 0
    sweet_spot_high: int = 12

    # From _infer_technique_between_notes
    legato_time_threshold: float = 0.5

    # From _infer_techniques_from_positions
    tapping_run_threshold: int = 2 # Notes in a run to be considered for tapping

    # Guitar properties
    max_fret: int = 24
    tuning: str = "STANDARD"