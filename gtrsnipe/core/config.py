from dataclasses import dataclass
from .types import Tuning

@dataclass
class MapperConfig:
    """Holds all tunable parameters for the GuitarMapper's scoring algorithm."""
    # From _score_fingering
    fret_span_penalty: float = 100.0
    movement_penalty: float = 3.0
    string_switch_penalty: float = 5.0
    high_fret_penalty: float = 5.0
    low_string_high_fret_multiplier: float =10.0 
    sweet_spot_bonus: float = 0.5
    unplayable_fret_span: int = 4
    ignore_open: bool = False
    sweet_spot_low: int = 0
    sweet_spot_high: int = 12

    # From _infer_technique_between_notes
    legato_time_threshold: float = 0.5

    # From _infer_techniques_from_positions
    tapping_run_threshold: int = 2 # Notes in a run to be considered for tapping

    # Guitar properties
    max_fret: int = 24
    tuning: str = "STANDARD"
    num_strings: int =  6
    capo: int = 0
    # Explicit open-string note names (low->high, the canonical tuning order), set
    # for a user-defined tuning via --tuning-pitches. When present it overrides
    # `tuning` everywhere the open string pitches / labels are derived.
    custom_tuning: tuple = None

    # from match_events_to_fretboard
    deduplicate_pitches: bool = False

    # quantization resolution. Used by the mapper and the ascii tab genereator.
    quantization_resolution: float = 0.125

    # open string preference
    prefer_open: bool = False
    fretted_open_penalty: float = 20.0

    # barre bonus/penalty
    barre_bonus: float = 0.0
    barre_penalty: float = 0.0

    # Monophonic mode
    mono_lowest_only: bool = False

    # Let Ring preference
    let_ring_bonus: float = 0.0 # also breaks up repetitive fretting of same note on same position, which can be easier to play

    # Diagonal fret span check
    diagonal_span_penalty: bool = False

    # Time-scaled movement (M08). When movement_time_base is set, the movement penalty is
    # multiplied by movement_reference_seconds / gap, where gap is the time the hand had for
    # the move, floored at min_gap_seconds: "onset" = onset to onset (Hori & Sagayama 2016),
    # "end" = from the end of the previous notes to this onset (scottvr: lifting the finger
    # ends the note). "" leaves movement time-blind, the default until M08 decides.
    # tempo_bpm turns beats into seconds; the generators set it from the song.
    movement_time_base: str = ""
    movement_reference_seconds: float = 0.5
    min_gap_seconds: float = 0.05
    tempo_bpm: float = 120.0

    # Fretboard optimizer: "viterbi" (global DP optimum, default) or "greedy"
    # (legacy per-step argmax, kept behind the flag to reproduce older fingerings).
    optimizer: str = "viterbi"
    # Pathological safety valve for per-chord candidate enumeration. Expected to
    # never fire on real music; if it does, the DP logs a warning and that
    # group's result is no longer provably optimal.
    hard_enum_cap: int = 4096