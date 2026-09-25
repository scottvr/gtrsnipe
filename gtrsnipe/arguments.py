from argparse import ArgumentParser

from .core.config import MapperConfig

# Single source of truth for tuning names, shared by every CLI/mode.
TUNING_CHOICES = ['STANDARD', 'E_FLAT', 'DROP_D', 'OPEN_G', 'BASS_STANDARD', 'BASS_DROP_D',
                  'BASS_E_FLAT', 'SEVEN_STRING_STANDARD', 'BARITONE_B', 'BARITONE_A',
                  'BARITONE_C', 'C_SHARP_STANDARD', 'OPEN_C6', 'DROP_C', 'PIANO']

QUANTIZATION_CHOICES = [0.0125, 0.025, 0.0625, 0.125, 0.25, 0.5, 1.0]


def add_tuning_args(target) -> None:
    """Fretboard geometry shared by every mode (all feed MapperConfig).

    ``target`` is a parser or an argument group, so the caller controls grouping.
    """
    target.add_argument(
        '--capo', type=int, default=0,
        help="Specify a capo position. All fret numbers will be relative to the capo.")
    target.add_argument(
        '--tuning', type=str, default='STANDARD', choices=TUNING_CHOICES,
        help='Specify the guitar tuning or "PIANO" for full-range midi passthrough. (default: STANDARD).')
    target.add_argument(
        '--num-strings', type=int, default=None, choices=[4, 5, 6, 7],
        help="Force the number of strings on the tab staff (4, 5, 6, or 7). Defaults to 4 for bass and 6 for guitar.")
    target.add_argument(
        '--max-fret', type=int, default=24,
        help='Maximum fret number on the virtual guitar neck (default: 24).')


def add_mapper_args(target) -> None:
    """All fretboard-mapper scoring/behavior knobs (all feed MapperConfig).

    Shared by every mode so the player and chord charts inherit the full option
    surface, not an amputated subset.
    """
    target.add_argument(
        '--optimizer', type=str, default='viterbi', choices=['viterbi', 'greedy'],
        help="Fretboard mapping strategy: 'viterbi' (global DP optimum, default) "
             "or 'greedy' (legacy per-step choice).")
    target.add_argument(
        '--mono-lowest-only', action='store_true',
        help="Force monophonic output by keeping only the lowest note in any chord.")
    target.add_argument(
        '--fret-span-penalty', type=float, default=100.0,
        help='Penalty for wide fret stretches (default: 100.0).')
    target.add_argument(
        '--movement-penalty', type=float, default=3.0,
        help='Penalty for hand movement between chords (default: 3.0).')
    target.add_argument(
        '--string-switch-penalty', type=float, default=5.0,
        help='Penalty for switching strings (default: 5.0).')
    target.add_argument(
        '--high-fret-penalty', type=float, default=5,
        help='Penalty for playing high on the neck (default: 5).')
    target.add_argument(
        '--low-string-high-fret-multiplier', type=float, default=10.0,
        help='Multiplier penalty for playing high on the neck on low strings (default: 10).')
    target.add_argument(
        '--unplayable-fret-span', type=int, default=4,
        help='Fret span considered unplayable (default: 4).')
    target.add_argument(
        '--sweet-spot-bonus', type=float, default=0.5,
        help='Bonus for playing in the ideal lower fret range.')
    target.add_argument(
        '--sweet-spot-low', type=int, default=0,
        help='Lowest fret of the "sweet spot" (default 0 - open)')
    target.add_argument(
        '--sweet-spot-high', type=int, default=12,
        help='Highest fret of the "sweet spot" (default 12)')
    target.add_argument(
        '--ignore-open', action='store_true', default=False,
        help="Don't consider open when calculating shape score.")
    target.add_argument(
        '--legato-time-threshold', type=float, default=0.5,
        help='Max time in beats between notes for a legato phrase (h/p) (default: 0.5).')
    target.add_argument(
        '--tapping-run-threshold', type=int, default=2,
        help='Min number of notes in a run to be considered for tapping (default: 2).')
    target.add_argument(
        '--dedupe', action='store_true',
        help="Enable de-duplication of notes with the same pitch within a chord. "
             "Useful for cleaning up MIDI from non-guitar sources.")
    target.add_argument(
        '--quantization-resolution', type=float, default=0.125, choices=QUANTIZATION_CHOICES,
        help="Quantization resolution. Used by the mapper to determine simultaneous sounding of notes (chords) and by the ascii tab generator mainly for spacing purposes.")
    target.add_argument(
        '--prefer-open', action='store_true',
        help='Prefer open strings over their fretted equivalents (e.g., open B over G-string fret 4).')
    target.add_argument(
        '--fretted-open-penalty', type=float, default=20.0,
        help='The penalty score applied to fretted notes that could be open strings (default: 20.0).')
    target.add_argument(
        '--barre-bonus', type=float, default=0.0,
        help='Bonus awarded to fingerings that use a barre/single finger (default: 0.0).')
    target.add_argument(
        '--barre-penalty', type=float, default=0.0,
        help='Penalty applied to fingerings that use a barre/single finger (default: 0.0).')
    target.add_argument(
        '--let-ring-bonus', type=float, default=0.0,
        help='Bonus awarded for fingerings that allow previous notes to ring out (default: 0.0).')
    target.add_argument(
        '--diagonal-span-penalty', action='store_true',
        help='Penalize fingerings with an unplayable fret span between consecutive notes.')


def resolve_num_strings(tuning: str, num_strings) -> int:
    """Infer string count from the tuning when not explicitly set (mirrors the
    converter's inference); falls back to 6 for unknown tunings / PIANO."""
    if num_strings:
        return num_strings
    from .core.types import Tuning
    key = (tuning or 'STANDARD').upper()
    if key in Tuning.__members__:
        return len(Tuning[key].value)
    return 6


def build_mapper_config(args, *, tuning: str, num_strings: int) -> MapperConfig:
    """The single MapperConfig builder (was duplicated across three CLIs).

    ``tuning`` and ``num_strings`` are passed resolved (callers apply their own
    bass/num-strings resolution first); every other knob comes from ``args``.
    """
    return MapperConfig(
        max_fret=args.max_fret,
        tuning=tuning,
        num_strings=num_strings,
        fret_span_penalty=args.fret_span_penalty,
        movement_penalty=args.movement_penalty,
        string_switch_penalty=args.string_switch_penalty,
        high_fret_penalty=args.high_fret_penalty,
        low_string_high_fret_multiplier=args.low_string_high_fret_multiplier,
        sweet_spot_bonus=args.sweet_spot_bonus,
        sweet_spot_low=args.sweet_spot_low,
        sweet_spot_high=args.sweet_spot_high,
        unplayable_fret_span=args.unplayable_fret_span,
        prefer_open=args.prefer_open,
        fretted_open_penalty=args.fretted_open_penalty,
        ignore_open=args.ignore_open,
        legato_time_threshold=args.legato_time_threshold,
        tapping_run_threshold=args.tapping_run_threshold,
        deduplicate_pitches=args.dedupe,
        quantization_resolution=args.quantization_resolution,
        capo=args.capo,
        barre_bonus=args.barre_bonus,
        barre_penalty=args.barre_penalty,
        mono_lowest_only=args.mono_lowest_only,
        let_ring_bonus=args.let_ring_bonus,
        diagonal_span_penalty=args.diagonal_span_penalty,
        optimizer=args.optimizer,
    )


def setup_parser() -> ArgumentParser:
    """Configures and returns the argument parser for the command-line interface."""
    parser = ArgumentParser(description="Convert music files between various formats, including audio to MIDI to tab.")

    parser.add_argument('-i', '--input', help='Path to the input file (.mid, .mp3, .wav, etc.).')
    parser.add_argument(
        '-o', '--output',
        required=True,
        action='append',
        help='Path(s) to the output file(s) (e.g., -o out.mid -o out.tab).'
    )

    instrument_group = parser.add_argument_group("Instrument Options")
    add_tuning_args(instrument_group)
    instrument_group.add_argument(
        "--bass",
        action='store_true',
        help="Enable bass mode. Automatically uses bass tuning and a 4-string staff."
    )
    instrument_group.add_argument(
        '--velocity-cutoff',
        type=int,
        default=0,
        choices=range(0, 128),
        metavar='[0-127]',
        help='Ignore MIDI notes with a velocity lower than this value (0-127).'
    )
    instrument_group.add_argument(
        '--min-note-override',
        type=str,
        default=None,
        help="Override the calculated lowest note for frequency constraining (e.g., 'E2'). Requires --constrain-frequency."
    )
    instrument_group.add_argument(
        '--max-note-override',
        type=str,
        default=None,
        help="Override the calculated highest note for frequency constraining (e.g., 'E4'). Requires --constrain-frequency."
    )

    pipeline_group = parser.add_argument_group('Audio-to-MIDI Pipeline Options')
    pipeline_group.add_argument('--nr', action='store_true', help='Step 2: Enables noise/reverb reduction on the audio stem.')
    pipeline_group.add_argument(
        '--stem-track',
        type=str,
        default=None,
        choices=['guitar', 'bass', 'drums', 'vocals', 'piano', 'other'],
        help="The instrument stem to isolate with Demucs. 'guitar' defaults to the 'other' stem."
    )
    pipeline_group.add_argument(
        '--demucs-model',
        type=str,
        default='htdemucs_6s',
        help="The demucs model to use for separation (e.g., htdemucs, htdemucs_fti, htdemucs_6s, mdx_extra)."
    )
    pipeline_group.add_argument(
        '--no-constrain-frequency',
        default=False,
        action='store_true',
        help="Constrain pitch detection to the frequency range of the selected tuning."
    )
    pipeline_group.add_argument(
       '--low-pass-filter',
        action='store_true',
        help="Apply a low-pass filter to the audio stem based on the instrument's max frequency."
    )
    pipeline_group.add_argument(
        '--pitch-engine',
        type=str,
        default='librosa',
        choices=['librosa'],
        help="The pitch detection engine to use. Currently 'librosa' (pYIN) only; "
             "the experimental basic-pitch engine was removed in v0.3.0."
    )

    parser.add_argument(
        "--nudge",
        type=int,
        default=0,
        help="An integer to shift the transcription's start time to the right. Each unit corresponds to roughly a 16th note."
    )
    parser.add_argument(
        '--first-note-is-downbeat',
        action='store_true',
        help="Shift the entire timeline so that the first note of the song starts at beat 0."
    )
    parser.add_argument(
        '-y', '--yes',
        action='store_true',
        help="Automatically overwrite the output file if it already exists."
    )
    parser.add_argument(
        "--track",
        type=int,
        default=None,
        help="The track number (1-based) to select from a multi-track MIDI file. If not set, all tracks are processed. For a multitrack midi, you will want to select a single instrument track to transcribe."
    )
    parser.add_argument(
        '--analyze',
        action='store_true',
        help='Analyze the input MIDI file to find the pitch range and suggest suitable tunings, then exit.'
    )
    parser.add_argument(
        "--transpose",
        type=int,
        default=0,
        help="Transpose the music up or down by N semitones (e.g., 2 for up, -3 for down)."
    )
    parser.add_argument(
        "--no-articulations",
        action='store_true',
        help="Transcribe with no legato, taps, hammer-ons, pull-offs, etc."
    )
    parser.add_argument(
        "--staccato",
        action='store_true',
        help="Do not extend note durations to the start of the next note, instead giving each note an 1/8 note duration. When converting from ASCII tab."
    )
    parser.add_argument(
        "--max-line-width",
        type=int,
        default=40,
        help="Max number of vertical columns per line of ASCII tab. (default: 40)"
    )
    parser.add_argument(
        "--single-string",
        type=int,
        default=None,
        choices=range(1, 7),
        help="Force all notes onto a single string (1-6, high e to low E). Ideal for transcribing legato/tapping runs."
    )
    parser.add_argument(
        '--normalize-pitch',
        action='store_true',
        help="Shift notes (+12 or -12) until they fit within the specified tuning and max fret range."
             "Used when the input has many out-of-range notes that would otherwise be dropped."
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        help="Enable detailed debug logging messages."
    )

    info_group = parser.add_argument_group('Tuning Information')
    info_group.add_argument(
        '--list-tunings',
        action='store_true',
        help='List all available tuning names and exit.'
    )
    info_group.add_argument(
        '--show-tuning',
        type=str,
        metavar='TUNING_NAME',
        help='Show the notes for a specific tuning and exit.'
    )

    mapper_group = parser.add_argument_group('Mapper Tuning/Configuration (Advanced)')
    add_mapper_args(mapper_group)
    # Preamble flags that live with the mapper group but are converter-specific
    # (they act during pre-processing, not inside MapperConfig).
    mapper_group.add_argument(
        '--no-pre-quantize',
        default=False,
        action='store_true',
        help='Force a pre-quantization pass, snapping all notes to the quantization grid before mapping.'
    )
    mapper_group.add_argument(
        '--dynamic-quantize',
        action='store_true',
        help='Quantize notes to a dynamic beat grid detected from the audio.'
    )

    return parser
