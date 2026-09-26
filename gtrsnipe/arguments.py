import argparse
import os
import sys
from argparse import ArgumentParser
from pathlib import Path
from typing import List, Optional

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
    target.add_argument(
        '--tuning-pitches', type=str, default=None, metavar='LOW,..,HIGH',
        help='Define a custom tuning by comma-separated note names, low string to '
             "high (e.g. 'A1,E2,A2,D3,F#3,B3'). Overrides --tuning.")
    target.add_argument(
        '--scale-length', type=float, default=None, metavar='INCHES',
        help='Scale length for string-tension physics (default: 25.5 guitar, 27 '
             'baritone, 34 bass).')
    target.add_argument(
        '--string-gauges', type=str, default=None, metavar='GAUGES',
        help="String gauges for tension physics, e.g. '.010,.013,.017,.026w,.036w,.046w' "
             "(any order; thickest = lowest string; 'w' = wound). Default: a "
             "conventional set for the tuning.")
    target.add_argument(
        '--drop-low-string', type=int, default=0, metavar='SEMITONES',
        help='Lower the lowest string by N semitones (2 = drop-D style), on any '
             'tuning / string count.')


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


def add_player_args(target) -> None:
    """Player/visualizer options, shared by `gtrsnipe --play` and gtrsnipe-play."""
    target.add_argument("--view", choices=["fretboard", "tab"], default="fretboard",
                        help="fretboard = animated neck; tab = scrolling tab staff.")
    target.add_argument("--clock", choices=["tempo", "metronome", "step"],
                        default="tempo",
                        help="Timing: at-tempo, fixed metronome grid, or 'step' to "
                             "start paused (space plays, '.' steps). Default: tempo.")
    target.add_argument("--tempo", type=float, default=None, metavar="BPM",
                        help="Override playback tempo in BPM (default: the song's).")
    target.add_argument("--grid", type=float, default=0.5,
                        help="Metronome step in beats (default: 0.5 = eighth note).")
    target.add_argument("--window", type=int, default=5,
                        help="Visible fret window size (fretboard view; default: 5).")
    target.add_argument("--width", type=int, default=48,
                        help="Tab view viewport width in columns (default: 48).")
    target.add_argument("--fps", type=float, default=12.0,
                        help="Animation redraws per second (default: 12).")
    target.add_argument("--orientation", choices=["horizontal", "vertical"],
                        default="horizontal",
                        help="Fretboard view: strings as rows or frets top-to-bottom.")
    target.add_argument("--hand", choices=["right", "left"], default="right",
                        help="Fretboard view: mirror the neck for left-handed players.")
    target.add_argument("--audio", choices=["none", "midi", "fluidsynth"],
                        default="none",
                        help="Make sound while playing: 'midi' streams to a port, "
                             "'fluidsynth' uses a SoundFont ([play]/[synth] extras).")
    target.add_argument("--midi-port", default=None,
                        help="MIDI output port name for --audio midi.")
    target.add_argument("--soundfont", default=None,
                        help="Path to a .sf2 SoundFont for --audio fluidsynth.")
    target.add_argument("--instrument", default=None,
                        help="Instrument for --audio: GM number (0-127) or name substring.")
    target.add_argument("--no-clear", action="store_true",
                        help="Do not clear the screen between frames (scrolls).")


def add_chart_args(target) -> None:
    """Chord-chart options, shared by `gtrsnipe -o x.chords.md` and gtrsnipe-chords."""
    target.add_argument("--measures-per-line", type=int, default=4,
                        help="Bars per progression row in a chord chart (default: 4).")
    target.add_argument("--chord-tone-threshold", type=float, default=0.15,
                        help="Min fraction of a bar a note must sound to count as a "
                             "chord tone (default: 0.15).")


def parse_tuning_pitches(spec: str) -> tuple:
    """Parse a `--tuning-pitches` spec (comma-separated notes, low->high) into a
    validated note-name tuple, stored low->high (the canonical tuning order)."""
    from .core.theory import note_name_to_pitch
    names_low_to_high = [s.strip() for s in spec.split(",") if s.strip()]
    if len(names_low_to_high) < 2:
        raise ValueError("--tuning-pitches needs >=2 comma-separated notes (low to high)")
    for n in names_low_to_high:
        note_name_to_pitch(n)  # validate; raises ValueError on a bad name
    return tuple(names_low_to_high)


def _named_tuning_names(tuning: str):
    from .core.types import Tuning
    key = (tuning or "STANDARD").upper()
    return list(Tuning[key].value) if key in Tuning.__members__ else None


def _drop_lowest(names_low_to_high, semitones: int) -> tuple:
    """Return the tuning with its lowest string (index 0, low->high) lowered."""
    from .core.theory import note_name_to_pitch, pitch_to_note_name
    names = list(names_low_to_high)
    names[0] = pitch_to_note_name(note_name_to_pitch(names[0]) - semitones)
    return tuple(names)


def resolve_custom_tuning(args) -> tuple:
    """The custom tuning (low->high note names) implied by --tuning-pitches and/or
    --drop-low-string, or None if a plain named tuning is in effect."""
    spec = getattr(args, "tuning_pitches", None)
    drop = getattr(args, "drop_low_string", 0) or 0
    names = parse_tuning_pitches(spec) if spec else None
    if drop:
        base = names if names else _named_tuning_names(getattr(args, "tuning", "STANDARD"))
        if base:
            names = _drop_lowest(base, drop)
    return names


def open_string_pitches_for(tuning: str, custom=None) -> list:
    """Open-string MIDI pitches, string index 0 = highest (HIGH->low), for a named
    or custom tuning; used to decode ASCII tabs in their actual tuning. Names are
    stored low->high, so reverse them."""
    from .core.theory import note_name_to_pitch
    names = list(custom) if custom else (_named_tuning_names(tuning)
                                         or _named_tuning_names("STANDARD"))
    return [note_name_to_pitch(n) for n in reversed(names)]


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
    bass/num-strings resolution first); every other knob comes from ``args``. A
    custom tuning (--tuning-pitches / --drop-low-string) overrides both.
    """
    custom = resolve_custom_tuning(args)
    if custom:
        tuning = "CUSTOM"
        num_strings = len(custom)
    return MapperConfig(
        max_fret=args.max_fret,
        tuning=tuning,
        num_strings=num_strings,
        custom_tuning=custom,
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


# ---------------------------------------------------------------------------
# Profiles / .gtrsnipe config
#
# A profile is just "saved argv": each file line becomes CLI tokens that are
# PREPENDED to the real command line and re-parsed by the same parser. So
# precedence falls out for free (profile tokens first, explicit CLI last → for
# argparse store actions the last value wins → CLI overrides the profile), and
# all validation/type-conversion is reused with no separate schema.
# ---------------------------------------------------------------------------

# Never taken from a profile file (avoid recursion / per-run-only meta).
_PROFILE_META = {"--profile", "--no-defaults", "--config-dir", "--save-args"}
# Not written by --save-args (per-run inputs, actions, or meta).
_SAVE_SKIP_DESTS = {
    "input", "output", "save_args", "profile", "no_defaults", "config_dir",
    "list_tunings", "show_tuning", "list_instruments", "analyze", "yes", "help",
    "solve_tuning", "homograph",
}


def add_profile_args(parser) -> None:
    """Profile/config options shared by every CLI (handled by apply_profiles)."""
    g = parser.add_argument_group("Profiles / config (.gtrsnipe)")
    g.add_argument("--profile", action="append", default=None, metavar="NAME[,NAME]",
                   help="Apply saved option profiles before the CLI args (repeatable "
                        "and/or comma-separated; applied in order; CLI overrides).")
    g.add_argument("--no-defaults", action="store_true",
                   help="Skip auto-loading the .gtrsnipe/defaults profile.")
    g.add_argument("--config-dir", default=None,
                   help="Directory to read/write profiles (default: ./.gtrsnipe then "
                        "~/.gtrsnipe, or $GTRSNIPE_HOME).")
    g.add_argument("--save-args", default=None, metavar="NAME",
                   help="Save the effective (non-default) options to a profile of this "
                        "name and continue.")


def _config_dirs(config_dir: Optional[str]) -> List[Path]:
    """Search path for profiles. --config-dir or $GTRSNIPE_HOME fully override
    (each yields exactly one dir — good for power users and hermetic tests);
    otherwise search ./.gtrsnipe then ~/.gtrsnipe."""
    if config_dir:
        return [Path(config_dir)]
    env = os.environ.get("GTRSNIPE_HOME")
    if env:
        return [Path(env)]
    return [Path.cwd() / ".gtrsnipe", Path.home() / ".gtrsnipe"]


def _find_profile(name: str, dirs: List[Path]) -> Optional[Path]:
    if os.sep in name or (os.altsep and os.altsep in name):
        p = Path(name).expanduser()
        return p if p.is_file() else None
    for d in dirs:
        f = d / name
        if f.is_file():
            return f
    return None


def _tokenize_profile(path: Path, known_opts: set, flag_opts: set) -> List[str]:
    """Turn a profile file into argv tokens. Lines: `name`, `name value`,
    `name = value` (leading dashes optional; `#` comments and blanks ignored)."""
    tokens: List[str] = []
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            name, _, value = line.partition("=")
        else:
            parts = line.split(None, 1)
            name, value = parts[0], (parts[1] if len(parts) > 1 else "")
        name, value = name.strip().lstrip("-"), value.strip()
        opt = "--" + name
        if opt in _PROFILE_META:
            continue  # no nested profiles / meta from a file
        if opt not in known_opts:
            sys.stderr.write(f"warning: {path.name}: unknown option '{name}' (skipped)\n")
            continue
        if opt in flag_opts:
            if value and value.lower() in ("false", "no", "0", "off"):
                continue  # a store_true can't be turned off; just omit it
            tokens.append(opt)
        elif value:
            tokens += [opt, value]
        else:
            sys.stderr.write(f"warning: {path.name}: '{name}' needs a value (skipped)\n")
    return tokens


def _save_args(parser, ns, config_dir: Optional[str]) -> None:
    lines: List[str] = []
    for a in parser._actions:
        if a.dest in _SAVE_SKIP_DESTS or not a.option_strings:
            continue
        val = getattr(ns, a.dest, None)
        if val == a.default:
            continue
        opt = max(a.option_strings, key=len).lstrip("-")
        if a.nargs == 0:      # flag
            if val:
                lines.append(opt)
        else:
            lines.append(f"{opt} = {val}")
    target_dir = _config_dirs(config_dir)[0]
    target_dir.mkdir(parents=True, exist_ok=True)
    out = target_dir / ns.save_args
    out.write_text("\n".join(lines) + "\n")
    sys.stderr.write(f"Saved {len(lines)} option(s) to {out}\n")


def apply_profiles(parser: ArgumentParser, argv=None) -> argparse.Namespace:
    """Parse ``argv`` with profile files prepended, then honor --save-args.

    Drop-in replacement for ``parser.parse_args()`` on a parser built with
    :func:`add_profile_args`.
    """
    argv = list(sys.argv[1:] if argv is None else argv)

    pre = argparse.ArgumentParser(add_help=False)
    pre.add_argument("--profile", action="append", default=[])
    pre.add_argument("--no-defaults", action="store_true")
    pre.add_argument("--config-dir", default=None)
    pre.add_argument("--save-args", default=None)
    known, _ = pre.parse_known_args(argv)

    dirs = _config_dirs(known.config_dir)
    known_opts = {o for a in parser._actions for o in a.option_strings}
    flag_opts = {o for a in parser._actions for o in a.option_strings if a.nargs == 0}

    tokens: List[str] = []
    if not known.no_defaults:
        f = _find_profile("defaults", dirs)
        if f:
            tokens += _tokenize_profile(f, known_opts, flag_opts)
    names: List[str] = []
    for spec in (known.profile or []):
        names += [n.strip() for n in spec.split(",") if n.strip()]
    for name in names:
        f = _find_profile(name, dirs)
        if f is None:
            parser.error(f"profile '{name}' not found in: "
                         + ", ".join(str(d) for d in dirs))
        tokens += _tokenize_profile(f, known_opts, flag_opts)

    args = parser.parse_args(tokens + argv)
    if getattr(args, "save_args", None):
        _save_args(parser, args, known.config_dir)
    return args


def setup_parser() -> ArgumentParser:
    """Configures and returns the argument parser for the command-line interface."""
    parser = ArgumentParser(description="Convert music files between various formats, including audio to MIDI to tab.")

    parser.add_argument('-i', '--input', help='Path to the input file (.mid, .mp3, .wav, etc.).')
    parser.add_argument(
        '-o', '--output',
        action='append',
        help='Path(s) to the output file(s) (e.g., -o out.mid -o out.tab -o song.chords.md). '
             'Not required with --play. A .chords/.chords.md output writes a chord sheet.'
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
        '--solve-tuning',
        type=str,
        default=None,
        metavar='NOTES',
        help="Inverse solve: given a comma-separated target melody (note names with "
             "octave, e.g. 'C4,C4,G4,G4,A4,A4,G4'), find a tuning under which an "
             "all-open-string tab plays it. Prints the tuning; add --play to hear it, "
             "or -o FILE.tab/.mid to write it. No -i needed."
    )
    parser.add_argument(
        '--max-strings',
        type=int,
        default=12,
        help='Max strings the tuning solver (and --homograph-mode free) may use (default: 12).'
    )

    homograph_group = parser.add_argument_group(
        'Tab homographs (--homograph: one tab, a different song per tuning)')
    homograph_group.add_argument(
        '--homograph', nargs='+', default=None, metavar='SONG',
        help="Find ONE tab that plays each SONG under its own tuning (2+ songs; the "
             "first is the tab's own). A SONG is a file (.mid[:TRACK], .abc, .tab, "
             ".vex; append @START-END for just onsets START..END) or an inline melody "
             "like 'C4 C4 G4 G4 A4 A4 G4:2' (':beats', '+' chords, 'r' rests). Prints "
             "an eligibility report and the tab. -o FILE.tab writes it; --play plays "
             "it. No -i needed.")
    homograph_group.add_argument(
        '--homograph-mode', choices=['anchored', 'middle', 'free'], default='anchored',
        help="anchored (default): song 1 keeps --tuning, so the tab is an ordinary tab "
             "of it and the other songs are retunes. middle: every song is a retune of "
             "the same strung guitar (tensions meet in the middle). free: any tunings "
             "at all (up to --max-strings strings). The report gives every verdict.")
    homograph_group.add_argument(
        '--homograph-rhythm', default='strict', metavar='strict|RATIO|sequence',
        help="strict (default): onsets match (or the same rhythm at another note "
             "value). RATIO, e.g. 1.5: each gap between onsets may differ by up to "
             "that factor. sequence: pitch order only. The tab carries song 1's rhythm.")
    homograph_group.add_argument(
        '--homograph-subdivide', type=int, default=1, metavar='K',
        help="Re-rhythm (2 songs): let one note stand for up to K notes of the other "
             "('ta' ~ 'ti ti'): repeated notes are smeared into one held note, else the "
             "single note is re-struck. Default 1 = off.")
    homograph_group.add_argument(
        '--homograph-transpose', default='auto', metavar='auto|keep|N',
        help="Transpose songs 2.. to minimize retuning (auto, default), keep their "
             "keys, or shift them by N semitones.")
    homograph_group.add_argument(
        '--homograph-transpose-a', default='auto', metavar='auto|keep|N',
        help="Song 1: auto (default) keeps its key when that works without "
             "re-stringing, else tries +-12 semitones; keep; or shift by N.")
    homograph_group.add_argument(
        '--homograph-max-retune', type=int, default=None, metavar='SEMITONES',
        help="Cap how far any string may be retuned from song 1's tuning.")
    homograph_group.add_argument(
        '--homograph-octaves', action='store_true',
        help="Arrangement liberty: allow octave displacement of individual notes of "
             "songs 2.. (lowers the rank; the report counts displaced notes).")
    homograph_group.add_argument(
        '--homograph-neutral', action='store_true',
        help="Write a neutral tab: strings numbered 1..N, no default tuning, so the "
             "text privileges no song.")
    homograph_group.add_argument(
        '--homograph-play', default='B', metavar='LETTER',
        help="With --play: which song's tuning to play the shared tab in (default: B).")
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

    player_group = parser.add_argument_group('Player mode (--play; interactive terminal)')
    player_group.add_argument(
        '--play', action='store_true',
        help="Play/visualize the song in the terminal instead of writing a file.")
    add_player_args(player_group)

    chart_group = parser.add_argument_group('Chord chart output (-o SONG.chords.md)')
    add_chart_args(chart_group)

    add_profile_args(parser)

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
