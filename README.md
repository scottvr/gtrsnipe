# gtrsnipe 
(pronounced "guttersnipe")
[see the wiki for detailed example use cases](https://github.com/scottvr/gtrsnipe/wiki)

Convert to and from .mid, .abc, .vex, and .tab files. (and more.)

## v0.4.0
Released 2026-09-24. See [CHANGELOG](https://github.com/scottvr/gtrsnipe/blob/main/CHANGELOG.md)

# What?

gtrsnipe is a guitar transcription tool. Its primary function is to create playable guitar tablature from a variety of sources. It now features a fledgling audio-to-tab pipeline that can take a mixed audio track, isolate the guitar part, and transcribe it into a tab.

It can also convert existing MIDI files into text-based notations or, in reverse, generate a playable MIDI file from a text-based tab.

Beyond writing files, gtrsnipe can **play** a song: `gtrsnipe-play` animates it on an ASCII fretboard or a horizontally-scrolling "Guitar Hero"-style tab staff — optionally with sound (MIDI to a synth/DAW, or a SoundFont) — and `gtrsnipe-chords` breaks a song into a per-measure chord sheet with diagrams. Both reuse the same fretboard mapper, so they work with every supported input format and tuning. (See the sections below.)

At its core, gtrsnipe uses an intelligent fretboard mapper that analyzes notes and chords to find comfortable and logical fingerings on the guitar neck. [This process is highly customizable](https://github.com/scottvr/gtrsnipe/wiki/1.-FretboardMapper-Algorithm-Configuration-and-Tunables), allowing you to fine-tune the output to match your personal playing style and preferences.

-----

# Installation

### Prerequisites

You must have a working Python programming language environment installed (from python.org or your system's software package manager) as well as `git` (from git-scm.com or your system's software package manager.)

### Procedure

It is highly recommended to install gtrsnipe within a python virtual environment.

```
git clone https://github.com/scottvr/gtrsnipe
cd gtrsnipe
python -mvenv .venv
```
Activate the environment:

on Windows: `.venv\Scripts\activate`
on MacOS/Linux: `. .venv/bin/activate`

Then, install the project and its dependencies:

```
pip install -e .
```

The base install is **CPU-only and torch-free** — it covers the full
MIDI/tab/abc/vex pipeline (including the player and chord charts) with no heavy
ML dependencies. Audio features live behind optional extras:

```
pip install -e '.[audio]'        # audio input: librosa pYIN bass pipeline
pip install -e '.[separation]'   # demucs stem isolation (pulls torch)
pip install -e '.[play]'         # player sound out: MIDI to a port (python-rtmidi)
pip install -e '.[synth]'        # player sound out: SoundFont synth (pyfluidsynth)
pip install -e '.[all]'          # everything above
```

> **Python version:** 3.10 and newer. On 3.14 the `[audio]` extra may build
> `llvmlite`/`numba` from source if wheels aren't yet published for your platform.

## Usage 

The installation process makes gtrsnipe available as a command within your activated virtual environment.

## Config profiles (`.gtrsnipe`)

Long command lines get old fast. Save option sets as **profiles** and reuse them.
Profiles are plain files in a `.gtrsnipe` directory (searched as `./.gtrsnipe`,
then `~/.gtrsnipe`, or `$GTRSNIPE_HOME`; `--config-dir DIR` overrides). A profile
named `defaults` is applied automatically (`--no-defaults` skips it), and any CLI
argument you pass still overrides the profile.

```bash
# .gtrsnipe/spanish
sweet-spot-high = 9
string-switch-penalty = 0
ignore-open
prefer-open
let-ring-bonus = 210
```

```bash
gtrsnipe -i piece.mid -o piece.tab --profile spanish        # apply a profile
gtrsnipe -i piece.mid -o piece.tab --profile spanish,short  # several, in order
gtrsnipe -i piece.mid -o piece.tab --sweet-spot-high 12 ...  --save-args mine  # save current opts
```

Format: `name value`, `name = value`, or a bare `name` for on/off flags; `#`
starts a comment. Works with every command (`gtrsnipe`, `gtrsnipe-play`,
`gtrsnipe-chords`) — a profile is just saved arguments. `--save-args NAME` writes
your current (non-default) options to a profile for next time.

## Custom tunings & the tuning solver

Beyond the named tunings, define your own with `--tuning-pitches` (low string to
high), or nudge an existing one with `--drop-low-string`:

```bash
gtrsnipe -i piece.mid -o piece.tab --tuning-pitches "A1,E2,A2,D3,F#3,B3"
gtrsnipe -i piece.mid -o piece.tab --tuning BARITONE_B --drop-low-string 2
```

Custom tunings work everywhere (convert, `--play`, chord charts). Generated tabs
carry a `// Tuning:` header and **round-trip** — feed one back as input and it
decodes in its own tuning; pass an explicit `--tuning`/`--tuning-pitches` to
*re-read* the same fingering in a different tuning and hear what it becomes.
(Tuning tuples and `--show-tuning` are listed low string → high.)

The **inverse** is `--solve-tuning`: give it a melody and it finds a tuning under
which an all-open-string tab plays it — the tab shows only open strings while the
tune lives entirely in the tuning:

```bash
gtrsnipe --solve-tuning "C4,C4,G4,G4,A4,A4,G4"                        # print tuning + tab
gtrsnipe --solve-tuning "C4,C4,G4,G4,A4,A4,G4" --play --audio fluidsynth --soundfont f.sf2  # hear it
gtrsnipe --solve-tuning "C4,C4,G4,G4,A4,A4,G4" -o twinkle.tab -o twinkle.mid   # write it
```

### Tab homographs: one tab, a different song per tuning

`--homograph A B [C …]` goes further: it looks for a single **ordinary, fretted,
playable** tab that plays song A in one tuning and song B in another. Here is a
standard-tuning tab of *Old MacDonald*. Retune four strings (all within their
gauges' safe range) and the very same tab plays *Twinkle, Twinkle*:

```text
$ gtrsnipe --homograph examples/homograph/oldmac.abc examples/homograph/twinkle.abc@1-12 --homograph-octaves
...
// Tuning: E2,A2,D3,G3,B3,E4
//   Key A: E2,A2,D3,G3,B3,E4  = oldmac
//   Key B: E2,A2,Bb2,Bb3,A3,C#4  = twinkle@1-12 (transposed -4)

e|----------|------|-0-0----|      e|--------------------------------|
B|----------|------|-----3-3|      B|-1------------------------------|
G|-------5--|------|--------|      G|--------------------------------|
D|-10-10---5|-7-7-5|--------|      D|--------------------------------|
A|----------|------|--------|      A|--------------------------------|
E|----------|------|--------|      E|--------------------------------|
```

(With `--homograph-octaves`, four of Twinkle's notes drop an octave; the report
says so. `--homograph-mode middle` plays Twinkle exactly, and needs no
re-stringing either.)

Why it works: on any one string, song A's note and song B's note differ by the
same interval (the difference between the two open strings). So two aligned songs
share a tab exactly when their note-for-note intervals split into as many classes
as there are strings. The report's **rank** counts those distinct intervals.
Neither note count nor range matters, and the keys don't either.

The report walks through each check in turn: alignment, rank, then *free* (any
tunings), *anchored* (A keeps `--tuning`, so the tab is an ordinary tab of A),
*middle* (both tunings are retunes of one strung guitar), and *as written* (A read
from a `.tab`: does its own fingering retune?). It stops with a reason at the
first failure. Retunes are checked against **string physics**: tension, the
breaking point of plain steel (about A4 at 25.5″, whatever the gauge), and slack.
Strings that would snap or flop are flagged, with a gauge that would work.

```bash
gtrsnipe --homograph a.mid b.abc -o shared.tab               # anchored to --tuning (default STANDARD)
gtrsnipe --homograph a.mid b.abc --homograph-mode middle     # both tunings retune one guitar
gtrsnipe --homograph song.mid:5@9-24 "E4 D4 C4 D4 E4 E4 E4:2"  # MIDI track 5, onsets 9-24, vs an inline melody
gtrsnipe --homograph a.abc b.abc --homograph-rhythm 1.5      # tolerate loose rhythm (tabs carry little)
gtrsnipe --homograph a.abc b.abc --homograph-subdivide 2     # 'ta' ~ 'ti ti': smear/re-strike to match counts
gtrsnipe --homograph a.abc b.abc --play --homograph-play B   # watch/hear the shared tab in B's tuning
```

Other knobs: `--homograph-transpose`/`-a` (song keys), `--homograph-max-retune`,
`--homograph-octaves` (octave-displace notes to lower the rank), `--homograph-neutral`
(number the strings and omit the default tuning, so the text favors no song),
`--scale-length`, `--string-gauges`. Every liberty taken is disclosed in the report
and the tab header. Theory, proofs, physics, and limits:
[`docs/dev/DESIGN-homograph.md`](docs/dev/DESIGN-homograph.md). Worked examples:
[`examples/homograph/`](examples/homograph/).

## Player / Visualizer

`gtrsnipe-play` renders a song as a live ASCII fretboard instead of writing a
file. It reuses the same parsers and the Viterbi fretboard mapper, so it accepts
every supported input format — with the same rhythm caveats (precise timing from
MIDI, approximate from ASCII tab). A 5-fret window auto-follows the playing up
and down the neck; open strings are shown at the nut.

> Since v0.5.0 the player is also a mode of the main tool: `gtrsnipe -i song.mid
> --play --view tab` is equivalent to `gtrsnipe-play`, but with the converter's
> full option set (audio input, `--transpose`, `--normalize-pitch`, every mapper
> knob). `gtrsnipe-play` remains as a convenience shortcut.

**Playback controls** (interactive terminal): `space` pause/resume; `.`/`,` step
forward/back (while paused); `←`/`→` seek ±1 bar; `[`/`]` tempo down/up; `g`/`end`
jump to start/end; `h` help; `q` quit. (`--clock step` just starts paused — press
`space` to play or `.` to step.)

```bash
# Play a MIDI file at its own tempo
gtrsnipe-play song.mid

# Steady eighth-note metronome at 90 BPM
gtrsnipe-play song.mid --clock metronome --grid 0.5 --tempo 90

# Step through it by hand (press any key to advance, q to quit)
gtrsnipe-play riff.tab --clock step
```

Layout can be rotated and mirrored:

```bash
# Vertical, chord-diagram style (frets top-to-bottom)
gtrsnipe-play song.mid --orientation vertical

# Left-handed (mirrors the neck)
gtrsnipe-play song.mid --hand left
```

Or watch a horizontally-scrolling tab staff — notes flow under a playhead as it
plays, a "7-bit terminal Guitar Hero":

```bash
gtrsnipe-play song.mid --view tab
```

To make sound while it plays, stream MIDI to a synth/DAW (route the port), or
render a SoundFont directly:

```bash
# Stream MIDI to a port (install: pip install 'gtrsnipe[play]')
gtrsnipe-play song.mid --audio midi --midi-port "IAC Driver Bus 1"

# Self-contained SoundFont playback (install: pip install 'gtrsnipe[synth]')
gtrsnipe-play song.mid --audio fluidsynth --soundfont /path/to/font.sf2

# Pick the voice by GM name or number; --list-instruments prints them all
gtrsnipe-play song.mid --audio fluidsynth --soundfont font.sf2 --instrument "nylon"
```

The display animates between notes (`--fps`, default 12) with a live
`bar N/total beat X` readout — the bar ratio doubles as a progress bar, and the
moving readout means long rests in ensemble MIDI keep scrolling instead of
looking frozen. On MacPorts, `pyfluidsynth` may need
`export DYLD_FALLBACK_LIBRARY_PATH=/opt/local/lib` to find the native library.

A decent soundfont I've used is [NitroFont v3.0](https://github.com/nitro-shoe/NitroFont-Rebooted/releases/tag/v3.0)

Key options: `--view {fretboard,tab}`, `--clock {tempo,metronome,step}`,
`--tempo BPM`, `--grid BEATS` (metronome step size), `--window N` (visible fret
count), `--width N` (tab viewport width), `--track N` (select a single MIDI
track, 1-indexed, same as the converter), `--orientation {horizontal,vertical}`,
`--hand {right,left}`, `--fps N` (animation smoothness),
`--audio {none,midi,fluidsynth}` (`--midi-port`, `--soundfont`, `--instrument`
NAME-or-0..127, `--list-instruments`), plus the usual `--tuning`,
`--num-strings`, `--max-fret`, `--capo`, and `--optimizer`.

## Chord charts

`gtrsnipe-chords` breaks a song into one chord per measure and prints a
songbook-style chord sheet: a bar-by-bar progression grid plus a diagram for
each unique chord. It reuses the fretboard mapper, so diagrams are voiced in the
song's own tuning.

```bash
# Print a chord sheet to the terminal
gtrsnipe-chords song.mid

# Save it as Markdown
gtrsnipe-chords song.mid -o song.chords.md
```

> Since v0.5.0 a chord sheet is also just an output format of the main tool:
> `gtrsnipe -i song.mid -o song.chords.md` (a `.chords`/`.chords.md` output writes
> the chart). `gtrsnipe-chords` remains as a convenience shortcut.

Chord *names* (C, Am, E5, E7, C/E, …) are derived by matching pitch classes to
chord templates, with the bass note disambiguating inversions and slash chords.
The diagrams show the chord **as voiced in the input** (the actual octaves,
mapped in your tuning) rather than canonical open shapes — faithful to the song,
and the only correct choice for non-standard tunings.

Key options: `-o FILE`, `--measures-per-line N`, `--chord-tone-threshold F`
(how long a note must sound in a bar to count as a chord tone), `--track N`,
plus the usual `--tuning`, `--num-strings`, `--capo`, `--optimizer`, and
`--prefer-open` (bias diagram voicings toward open strings).

### Command-line help

```
usage: gtrsnipe [-h] [-i INPUT] -o OUTPUT [--capo CAPO]
                [--tuning {STANDARD,E_FLAT,DROP_D,OPEN_G,BASS_STANDARD,BASS_DROP_D,BASS_E_FLAT,SEVEN_STRING_STANDARD,BARITONE_B,BARITONE_A,BARITONE_C,C_SHARP_STANDARD,OPEN_C6,DROP_C,PIANO}]
                [--bass] [--num-strings {4,5,6,7}] [--max-fret MAX_FRET] [--mono-lowest-only] [--velocity-cutoff [0-127]] [--nr]
                [--stem-track {guitar,bass,drums,vocals,piano,other}] [--demucs-model DEMUCS_MODEL] [--no-constrain-frequency]
                [--min-note-override MIN_NOTE_OVERRIDE] [--max-note-override MAX_NOTE_OVERRIDE] [--low-pass-filter] [--pitch-engine {librosa}]
                [--nudge NUDGE] [--first-note-is-downbeat] [-y] [--track TRACK] [--analyze]
                [--transpose TRANSPOSE] [--no-articulations] [--staccato] [--max-line-width MAX_LINE_WIDTH] [--single-string {1,2,3,4,5,6}] [--normalize-pitch]
                [--debug] [--list-tunings] [--show-tuning TUNING_NAME] [--optimizer {viterbi,greedy}] [--fret-span-penalty FRET_SPAN_PENALTY]
                [--movement-penalty MOVEMENT_PENALTY] [--string-switch-penalty STRING_SWITCH_PENALTY] [--high-fret-penalty HIGH_FRET_PENALTY]
                [--low-string-high-fret-multiplier LOW_STRING_HIGH_FRET_MULTIPLIER] [--unplayable-fret-span UNPLAYABLE_FRET_SPAN]
                [--sweet-spot-bonus SWEET_SPOT_BONUS] [--sweet-spot-low SWEET_SPOT_LOW] [--sweet-spot-high SWEET_SPOT_HIGH] [--ignore-open]
                [--legato-time-threshold LEGATO_TIME_THRESHOLD] [--tapping-run-threshold TAPPING_RUN_THRESHOLD] [--no-pre-quantize] [--dedupe]
                [--quantization-resolution {0.0125,0.025,0.0625,0.125,0.25,0.5,1.0}] [--prefer-open] [--fretted-open-penalty FRETTED_OPEN_PENALTY]
                [--barre-bonus BARRE_BONUS] [--barre-penalty BARRE_PENALTY] [--let-ring-bonus LET_RING_BONUS] [--diagonal-span-penalty]

```

### Fretboard optimizer (`--optimizer`)

gtrsnipe chooses where to play each note on the fretboard by maximizing an
additive playability score (fret span, hand movement, string switching, barre
shapes, let-ring, and more). Two strategies are available:

- **`viterbi`** (default) — a dynamic-programming / Viterbi trellis search that
  finds the **globally optimal** fingering sequence for the whole passage. It
  enumerates every valid (distinct-string) fingering per chord and reuses the
  exact same scoring function, so its result is provably at least as good as the
  greedy path. Tie-breaks are deterministic.
- **`greedy`** — the legacy per-chord choice that never reconsiders earlier
  notes. Kept for one release for reproducibility; use `--optimizer greedy` to
  match pre-0.3.0 output.

```
gtrsnipe -i input.mid -o out.tab                      # viterbi (default)
gtrsnipe -i input.mid -o out.tab --optimizer greedy   # legacy behavior
```

### A Note on Bonuses and Penalties: Inverting Scoring Behavior

All scoring parameters, whether they end in -bonus or -penalty, are simply numerical weights. The suffix is used to indicate the parameter's default behavior   penalties are subtracted from the score, and bonuses are added.

You can invert the behavior of any scoring parameter by providing a negative value. This allows for a high degree of customization.

**Example: Creating a "Penalty" from a Bonus**

By default, gtrsnipe rewards fingerings that allow previous notes to ring out (--let-ring-bonus). If you want to create a more staccato or muted style that discourages ringing notes, you can provide a negative bonus, effectively turning it into a penalty:

```
# Penalize fingerings that allow notes to ring out
gtrsnipe -i input.mid --let-ring-bonus -100 ...
```

**Example: Creating a "Bonus" from a Penalty**

By default, the algorithm penalizes wide fret stretches (--fret-span-penalty). If you want to encourage the system to find wide, complex chord voicings, you can provide a negative penalty, which turns it into a bonus:

```
# Reward wide-stretch fingerings
gtrsnipe -i input.mid --fret-span-penalty -10 ...
```

## Command-line Options in Detail

**options:**
-   `-h, --help`            show this help message and exit
-  `-i INPUT, --input INPUT`
                        Path to the input file (.mid, .mp3, .wav, etc.).
-  `-o OUTPUT, --output OUTPUT`
                        Path to the output file (.tab, .mid, etc.).
-  `--nudge NUDGE`         An integer to shift the transcription's start time to the right. Each unit corresponds to roughly a 16th note.
-  `-y, --yes`             Automatically overwrite the output file if it already exists.
-  `--track TRACK`         The track number (1-based) to select from a multi-track MIDI file. If not set, all tracks are processed. For a multitrack midi, you will   
                        want to select a single instrument track to transcribe.
-  `--analyze`             Analyze the input MIDI file to find the pitch range and suggest suitable tunings, then exit.
-  `--transpose TRANSPOSE`
                        Transpose the music up or down by N semitones (e.g., 2 for up, -3 for down).
-  `--no-articulations`    Transcribe with no legato, taps, hammer-ons, pull-offs, etc.
-  `--staccato`            Do not extend note durations to the start of the next note, instead giving each note an 1/8 note duration. When converting from ASCII      
                        tab.
-  `--max-line-width MAX_LINE_WIDTH`
                        Max number of vertical columns per line of ASCII tab. (default: 40)
-  `--single-string {1,2,3,4,5,6}`
                        Force all notes onto a single string (1-6, high e to low E). Ideal for transcribing legato/tapping runs.
-  `--normalize-pitch`     Constrain notes to the playable range of the tuning specified by --tuning.
-  `--optimizer {viterbi,greedy}`
                        Fretboard mapping strategy: 'viterbi' (global DP optimum, default) or 'greedy' (legacy per-step choice).
-  `--debug`               Enable detailed debug logging messages.


**Audio-to-MIDI Pipeline Options:** _(require `pip install 'gtrsnipe[audio]'`; `--stem-track` also needs `[separation]`)_
-  `--nr`                  (Experimental. Enables noise/reverb reduction on the audio stem.)
-  `--stem-track {guitar,bass,drums,vocals,piano,other}`
                        The instrument stem to isolate with Demucs. 'guitar' defaults to the 'other' stem.
-  `--demucs-model DEMUCS_MODEL`
                        The demucs model to use for separation (e.g., htdemucs, htdemucs_fti, htdemucs_6s, mdx_extra).
-  `--constrain-frequency`
                        Constrain pitch detection to the frequency range of the selected tuning.
-  `--low-pass-filter`     Apply a low-pass filter to the audio stem based on the instrument's max frequency.
-  `--pitch-engine {librosa}`
                        Pitch detection engine. Currently librosa (pYIN) only; the experimental basic-pitch engine was removed in v0.3.0.

**Tuning Information:**
-  `--list-tunings`        List all available tuning names and exit.
-  `--show-tuning TUNING_NAME`
                        Show the notes for a specific tuning and exit.

**Mapper Tuning/Configuration (Advanced):**
-  `--fret-span-penalty FRET_SPAN_PENALTY`
                        Penalty for wide fret stretches (default: 100.0).
-  `--movement-penalty MOVEMENT_PENALTY`
                        Penalty for hand movement between chords (default: 3.0).
-  `--string-switch-penalty STRING_SWITCH_PENALTY`
                        Penalty for switching strings (default: 5.0).
-  `--high-fret-penalty HIGH_FRET_PENALTY`
                        Penalty for playing high on the neck (default: 5).
-  `--low-string-high-fret-multiplier LOW_STRING_HIGH_FRET_MULTIPLIER`
                        Multiplier penalty for playing high on the neck on low strings (default: 10).
-  `--unplayable-fret-span UNPLAYABLE_FRET_SPAN`
                        Fret span considered unplayable (default: 4).
-  `--sweet-spot-bonus SWEET_SPOT_BONUS`
                        Bonus for playing in the ideal lower fret range.
-  `--sweet-spot-low SWEET_SPOT_LOW`
                        Lowest fret of the "sweet spot" (default 0 - open)
-  `--sweet-spot-high SWEET_SPOT_HIGH`
                        Highest fret of the "sweet spot" (default 12)
-  `--ignore-open`         Don't consider open when calculating shape score.
-  `--legato-time-threshold LEGATO_TIME_THRESHOLD`
                        Max time in beats between notes for a legato phrase (h/p) (default: 0.5).
-  `--tapping-run-threshold TAPPING_RUN_THRESHOLD`
                        Min number of notes in a run to be considered for tapping (default: 2).
-  `--pre-quantize`        Force a pre-quantization pass, snapping all notes to the quantization grid before mapping.
-  `--dedupe`              Enable de-duplication of notes with the same pitch within a chord. Useful for cleaning up MIDI from non-guitar sources.
-  `--quantization-resolution {0.0125,0.0625,0.125,0.25,0.5,1.0}`
                        Quantization resolution. Used by the mapper to determine simultaneous sounding of notes (chords) and by the ascii tab generator mainly     
                        for spacing purposes.
-  `--prefer-open`         Prefer open strings over their fretted equivalents (e.g., open B over G-string fret 4).
-  `--fretted-open-penalty FRETTED_OPEN_PENALTY`
                        The penalty score applied to fretted notes that could be open strings (default: 20.0).
-  `--barre-bonus BARRE_BONUS`
                        Bonus awarded to fingerings that use a barre/single finger (default: 0.0).
-  `--barre-penalty BARRE_PENALTY`
                        Penalty applied to fingerings that use a barre/single finger (default: 0.0).
-  `--let-ring-bonus LET_RING_BONUS`
                        Bonus awarded for fingerings that allow previous notes to ring out (default: 0.0).
-  `--diagonal-span-penalty`
                        Penalize fingerings with an unplayable fret span between consecutive notes.

**Instrument Options**
-   `--capo CAPO`           Specify a capo position. All fret numbers will be relative to the capo.
-   `--tuning {STANDARD,E_FLAT,DROP_D,OPEN_G,BASS_STANDARD,BASS_DROP_D,BASS_E_FLAT,SEVEN_STRING_STANDARD,BARITONE_B,BARITONE_A,BARITONE_C,C_SHARP,OPEN_C6,DROP_C,PIANO}`
                        Specify the guitar tuning or "PIANO" for full-range midi passthrough. (default: STANDARD).
-   `--bass`                Enable bass mode. Automatically uses bass tuning and a 4-string staff.
-   `--num-strings {4,5,6,7}`
                        Force the number of strings on the tab staff (4, 5, 6, or 7). Defaults to 4 for bass and 6 for guitar.
-   `--max-fret MAX_FRET`   Maximum fret number on the virtual guitar neck (default: 24).
-   `--mono-lowest-only`    Force monophonic output by keeping only the lowest note in any chord.
-   `--min-note-override MIN_NOTE_OVERRIDE`
                        Override the calculated lowest note for frequency constraining (e.g., 'E2'). Requires --constrain-frequency.
-   `--max-note-override MAX_NOTE_OVERRIDE`
                        Override the calculated highest note for frequency constraining (e.g., 'E4'). Requires --constrain-frequency.


## Usage Examples

**Full audio-to-tab transcription**

Run the complete pipeline on a mixed audio file to generate a tab tuned to Drop D.

[`gtrsnipe -i x:\S.O.D.mp3 -o march_of_the_S.O.D.tab --bass --stem --stem-name bass --tuning DROP_D  -y`](https://github.com/scottvr/gtrsnipe/wiki/v0.2.0)

**Audio-to-MIDI only**

Extract the guitar part from a song and save it as a MIDI file, stopping the pipeline there.

`gtrsnipe -i "another_song.wav" -o "guitar_part.mid" --stem`

**Transcribing from Clean Audio**

If you already have a clean, isolated guitar track, you can skip the demucs and noise reduction steps.

`gtrsnipe -i "my_clean_riff.wav" -o "my_riff.tab"`

**MIDI-to-Tab (Classic V1 Functionality)**

[`gtrsnipe -i "MrCrowley.mid" -o "mrcrowley.tab" --track 5`](https://github.com/scottvr/gtrsnipe/wiki/2.-Example-%E2%80%90-Mr-Crowley-organ-intro)

# Other Examples

[All other examples and detailed usage information has been moved to the Wiki](<https://github.com/scottvr/gtrsnipe/wiki/0.-GTRSnipe-(aka-%22guttersnipe%22)>)

## Advanced Usage: Mapper Tuning

The real power of gtrsnipe comes from its customizability. You can fine-tune the fretboard mapping algorithm and the audio separation models to get the perfect transcription. [Detailed documentation with troubleshooting examples are being created in the wiki.](https://github.com/scottvr/gtrsnipe/wik/FretboardMapper-Algorithm-Configuration-and-Tunables)


### Current Supported Instrument Tunings

```
$ gtrsnipe  --list-tunings                                                   
Available Tunings:
- STANDARD              : E4 B3 G3 D3 A2 E2
- E_FLAT                : Eb4 Bb3 Gb3 Db3 Ab2 Eb2
- DROP_D                : E4 B3 G3 D3 A2 D2
- D_STANDARD            : D4 A3 F3 C3 G2 D2
- DROP_C                : D4 A3 F3 C3 G2 C2
- DROP_B                : C#4 F#3 B2 E2 B1
- OPEN_G                : D4 B3 G3 D3 G2 D2
- OPEN_E                : E4 B3 G#3 E3 B2 E2
- DADGAD                : D4 A3 G3 D3 A2 D2
- OPEN_D                : D4 A3 F#3 D3 A2 D2
- OPEN_C6               : E4 C4 G3 C3 A2 C2
- BASS_STANDARD         : G2 D2 A1 E1
- BASS_DROP_D           : G2 D2 A1 D1
- BASS_E_FLAT           : Gb2 Db2 Ab1 Eb1
- SEVEN_STRING_STANDARD : E4 B3 G3 D3 A2 E2 B1
- SEVEN_STRING_DROP_A   : E4 B3 G3 D3 A2 E2 A1
- BARITONE_B            : B3 F#3 D3 A2 E2 B1
- BARITONE_A            : A3 E3 C3 G2 D2 A1
- BARITONE_C            : C4 G3 Eb3 Bb2 F2 C2
```

### Demucs Model for stem separation

**Demucs Model Selection** `(--demucs-model)`

Demucs is a state-of-the-art music source separation model. Several models are available, each with specific characteristics. Choosing the right one can significantly improve the quality of the isolated audio stem.

- **htdemucs**: The default Hybrid Transformer Demucs model. A great all-rounder.
- **htdemucs_ft**: A version of htdemucs fine-tuned on extra data. May offer better quality at the cost of speed.
- **htdemucs_6s**: A 6-source version that can additionally attempt to separate piano and guitar, though quality may vary.
- **hdemucs_mmi**: The v3 Hybrid Demucs model, retrained on more data.
- **mdx / mdx_extra**: Models known for high performance, trained on the MusDB HQ dataset.
- **mdx_q / mdx_extra_q**: Quantized (smaller, faster) versions of the mdx models, which may have slightly reduced quality.








