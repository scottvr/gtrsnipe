# gtrsnipe 
(pronounced "guttersnipe")
[see the wiki for detailed example use cases](https://github.com/scottvr/gtrsnipe/wiki)

Convert to and from .mid, .abc, .vex, and .tab files. (and more.)

## v0.8.0
Released 2026-10-07. See [CHANGELOG](https://github.com/scottvr/gtrsnipe/blob/main/CHANGELOG.md)

# What?

gtrsnipe is a guitar transcription tool. Its primary function is to create playable guitar tablature from a variety of sources. It now features a fledgling audio-to-tab pipeline that can take a mixed audio track, isolate the guitar part, and transcribe it into a tab.

It can also convert existing MIDI files into text-based notations or, in reverse, generate a playable MIDI file from a text-based tab.

Beyond writing files, gtrsnipe can **play** a song: `gtrsnipe-play` animates it on an ASCII fretboard or a horizontally-scrolling "Guitar Hero"-style tab staff — optionally with sound (MIDI to a synth/DAW, or a SoundFont) — and `gtrsnipe-chords` breaks a song into a per-measure chord sheet with diagrams. Both reuse the same fretboard mapper, so they work with every supported input format and tuning. (See the sections below.) It can also find [**tab homographs**](#tab-homographs-one-tab-a-different-song-per-tuning): one ordinary tab that plays a different song in each of two (or more) tunings.

Smaller tools along the way: chord names written over a tab (`--name-chords`), the chord any fret shape plays (`--name-chord`), a ranking of tunings by how playable a song is in each (`--analyze`), and each string's tension in a tuning, so you know before you retune whether your strings will take it (`--show-tuning`).

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

The installation process makes gtrsnipe available as a command within your activated virtual environment, along with `gtrsnipe-play`, `gtrsnipe-chords` and `gtrsnipe-research` (described below).

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

## Custom tunings

Beyond the named tunings, define your own with `--tuning-pitches` (low string to
high), or nudge an existing one with `--drop-low-string`:

```bash
gtrsnipe -i piece.mid -o piece.tab --tuning-pitches "A1,E2,A2,D3,F#3,B3"
gtrsnipe -i piece.mid -o piece.tab --tuning BARITONE_B --drop-low-string 2
```

Custom tunings work everywhere (convert, `--play`, chord charts). Generated tabs
carry a `// Tuning:` header and **round-trip** — feed one back as input and it
decodes in its own tuning, with its own fingering; pass an explicit
`--tuning`/`--tuning-pitches` to *re-read* the same fingering in a different tuning and
hear what it becomes (see [Tab input](#tab-input-kept-as-written)).
(Tuning tuples and `--show-tuning` are listed low string → high.)

Saving tunings in a .gtrsnipe profile is a way you can always have any tunings
available to you by name without gtrsnipe having to ship them in the source code.
e.g.:
```bash
echo "--tuning-pitches D2,G2,E3,F3,C4,D4" >~/.gtrsnipe/trainwreck
gtrsnipe -i piece.mid -o piece.tab --profile trainwreck
```
(`gtrsnipe --tuning-pitches D2,G2,E3,F3,C4,D4 --save-args trainwreck` writes the same profile.)

**Will my strings take it?** `--show-tuning` shows each string's tension as a retune of your
guitar, and suggests a restring for any string outside safe tension:

```
$ gtrsnipe --tuning-pitches E2,A2,D3,G3,B3,G4 --show-tuning
Tuning: custom
Notes:  E2 A2 D3 G3 B3 G4 (low to high)
Guitar: 10-46 set, 25.5" scale, strung for STANDARD

  string  strung for  tuned to  gauge    tension   vs normal  stress  status
       6          E2        E2  .046w     17.9 lb        +0%          ok
       5          A2        A2  .036w     19.5 lb        +0%          ok
       4          D3        D3  .026w     18.1 lb        +0%          ok
       3          G3        G3  .017      16.6 lb        +0%     19%  ok
       2          B3        B3  .013      15.5 lb        +0%     30%  ok
       1          E4        G4  .010      23.0 lb       +41%     75%  tight (every steel string is at snap risk at G4 on a 25.5" scale)
  (stress: % of breaking strength, plain strings only; wound strings are judged by tension)

1 of 6 strings outside safe tension.
```

- **Your guitar** is the usual set for `--tuning` (10-46 for STANDARD), or your own
  `--string-gauges`. Those are strung for an explicit `--tuning`, else for the tuning shown.
- **With a name** (`--show-tuning DROP_C`), it shows that tuning; with none, the one set by
  `--tuning-pitches` or `--drop-low-string`.
- **Converting with a custom tuning warns** about any string it would overload or leave
  floppy, and `--solve-tuning` notes any pitch past what a steel string can take at your scale
  length. A plain string's breaking pitch depends on the scale, not the gauge: about A4 at 25.5".
- **Gauges:** `w` marks a wound string and `p` a plain one; unsuffixed gauges above .020
  count as wound, so a jazz set's plain .022 G is `22p`. For a re-entrant tuning such as
  Nashville, gauges are read exactly as written, low string first.

**Which tuning suits this song?** `--analyze` fingers the song in every tuning whose range fits
it, your own `--tuning-pitches` included, and ranks them by how playable the tab is:

```bash
gtrsnipe -i song.mid --analyze                                     # rank the tunings that fit
gtrsnipe -i song.mid --analyze --tuning-pitches D2,G2,E3,F3,C4,D4   # with yours among them
gtrsnipe -i song.mid --analyze --bass                              # bass tunings
```

The score is the mapper's, per note, with your current settings, so a profile changes the
ranking. Each row also gives the frets used, hand travel per note and the share of open strings.

Adding custom tunings led to a parlor trick which is sort of the inverse of supplying
a custom tuning to gtrsnipe: give it a melody consisting of <= six distinct pitches, and
gtrsnipe finds an open tuning that can play it. That is, your tab would be all open strings:

```bash
gtrsnipe --solve-tuning "C4,C4,G4,G4,A4,A4,G4"                        # print tuning + tab
gtrsnipe --solve-tuning "C4,C4,G4,G4,A4,A4,G4" --play --audio fluidsynth --soundfont f.sf2  # hear it
gtrsnipe --solve-tuning "C4,C4,G4,G4,A4,A4,G4" -o twinkle.tab -o twinkle.mid   # write it
```

This led to an entire research endeavor still underway and partially documented in this repo:
<a name="tab-homographs-one-tab-a-different-song-per-tuning"></a>

## Tab Homographs
<details>

  <summary>[click to expand] Tab homographs: one tab, a different song per tuning</summary>

`--homograph A B [C …]` goes further: it looks for a single **ordinary, fretted,
playable** tab that plays song A in one tuning and song B in another. Here is a
standard-tuning tab of *Old MacDonald*. Retune four strings (all within their
gauges' safe range) and the very same tab plays *Twinkle, Twinkle*:

```text
$ gtrsnipe --homograph examples/homograph/oldmac.abc examples/homograph/twinkle.abc@1-12 --homograph-octaves
...
// Tuning: E2,A2,D3,G3,B3,E4
// Homograph: this one tab plays a different song in each tuning (low->high):
//   Key A: E2,A2,D3,G3,B3,E4  = oldmac
//   Key B: E2,A2,Bb2,Bb3,A3,C#4  = twinkle@1-12 (transposed -4)
...
e|-----------|---------|-0-0-----|-------|
B|-----------|---------|-----3-3-|-1-----|
G|-------5---|---------|---------|-------|
D|-10-10---5-|-7-7-5---|---------|-------|
A|-----------|---------|---------|-------|
E|-----------|---------|---------|-------|
```

(With `--homograph-octaves`, four of Twinkle's notes drop an octave; the report
says so. `--homograph-mode middle` plays Twinkle exactly, and needs no
re-stringing either.)

Why it works: on any one string, song A's note and song B's note differ by the
same interval (the difference between the two open strings). So two aligned songs
share a tab exactly when their note-for-note intervals split into as many classes
as there are strings. The report's **richness** counts those distinct intervals.
Neither note count nor range matters, and the keys don't either.

The report walks through each check in turn: alignment, richness, then *free* (any
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

Other knobs: `--homograph-max-discomfort` (reject tabs much less playable than A's own; the
report prints each tab's discomfort and fret range), `--homograph-transpose`/`-a` (song keys),
`--homograph-max-retune`,
`--homograph-octaves` (octave-displace notes to lower the richness), `--homograph-neutral`
(number the strings and omit the default tuning, so the text favors no song),
`--scale-length`, `--string-gauges`. Every liberty taken is disclosed in the report
and the tab header. Theory, proofs, physics, and limits:
[`docs/app/DESIGN-homograph.md`](docs/app/DESIGN-homograph.md). Worked examples:
[`examples/homograph/`](examples/homograph/).

#### Checking a tab against a recording's MIDI

The homograph machinery doubles as a tab checker. Give it a tab and a reference MIDI of the
same passage; tabs rarely get the timing right, so match the notes in order:

```bash
gtrsnipe --homograph their.tab reference.mid --homograph-rhythm sequence
```

The **As written** line says what kind of tab it is:
- **ELIGIBLE, no retune:** the tab is right.
- **ELIGIBLE with a retune:** the tab is right in another tuning (e.g. written for drop-D
  but labelled standard).
- **NOT ELIGIBLE, "string N carries 2 different intervals":** the tab is wrong-wrong. No
  tuning makes its fingering play the reference, and the named string is where to look.
- **NOT ALIGNED:** the tab has missing or extra notes.

#### Research tools (`gtrsnipe-research`)

For hunting homographs and studying the offset measures across melody corpora. It
reads the Essen Folksong Collection, the Meertens Tune Collections, Nottingham,
POP909 and Lakh into one monophonic format and caches each as a single file. It
also prints the **offset profile** of two aligned melodies: richness, entropy,
coverage, switches, total variation and reuse (see
[`docs/research/theory/coupled_transposition_structure.md`](docs/research/theory/coupled_transposition_structure.md)).
The corpora aren't included; point `--data` (or `GTRSNIPE_CORPUS_ROOT`) at a
folder holding them. `--data` goes before the subcommand. Caches are written to
and read from that folder's `_cache/`, so the examples after the first assume
`GTRSNIPE_CORPUS_ROOT` is set.

```bash
gtrsnipe-research --data ~/corpora corpus build essen     # read essen/**/*.krn into a cache
gtrsnipe-research corpus show essen:deut4659               # one melody, phrase marks shown as |
gtrsnipe-research profile essen:deut4659#p1 essen:deut4659#p3 --subdivide 2   # compare two phrases ('ta' ~ 'ti ti')
gtrsnipe-research profile a.mid:2@1-4 "C4 D4 E4 C4" --json      # files and inline melodies work too
gtrsnipe-research families mtc-ann                         # tune-family retrieval, measure by measure
gtrsnipe-research scan essen mtc-fs --solve 40 --tabs out/  # phrases of different songs that share a tab
gtrsnipe-research aswritten examples/aswritten/*.tab       # can a tab's own fingering play another song?
gtrsnipe-research segments mtc-ann --level phrase          # phrase/motif retrieval on MTC-ANN's annotations (R03b)
```

</details>


## Tab output: the dashes say how long

In a tab gtrsnipe writes, **the number of dashes after a note is its length**: one dash for
the *base* note (the tune's shortest note value), two more each time the length doubles, one
more for a dot. A header line gives the table:

```
// Rhythm: dash-count, base 1/8   (e=1 e.=2 q=3 q.=4 H=5 H.=6 W=7)

B|-5---5---6---8---|-8---6---5---3---|-1---1---3---5---|-5----3-3-----|
```

That is *Ode to Joy*: quarter notes (three dashes each), then in the last bar a dotted
quarter (four), an eighth (one) and a half (five). To the eye it reads as hand-written tabs
do, longer notes get more room. To gtrsnipe it is exact: the tab read back, or converted to
MIDI or ABC, has the rhythm that was written.

- **`--tab-rhythm {dashes,columns,loose}`** picks the layout.
  - `dashes` (the default): as above.
  - `columns`: every bar is cut into equal time slots, so a note's column across its bar is
    its time. Also exact, needs no legend to read, and is sometimes wide.
  - `loose`: the layout up to v0.7.0. Compact, and its spacing only hints at the rhythm.
- **`--tab-base 1/16`** fixes the note one dash stands for (default: chosen per tune), so
  every tab uses the same table, at some cost in width.
- **A bar holding a length the table lacks** (five sixteenths, a triplet) is written in
  `columns`, and the legend names it (`bars 7, 12 in columns`).
  `--tab-odd-bars {columns,nearest,error}` chooses otherwise.
- **`--tab-letters`** adds a line of note lengths over the staff, on top of any layout:
  `W H q e s t` for a whole note down to a 32nd, a dot adds half, `+` ties two. A letter
  with nothing under it is a rest.

  ```
     q.   e H
  B|-5----3-3-----|
  ```
- **Rows** hold whole bars, as many as fit `--max-line-width` (default 80).
- **A tab made from a tab that didn't state its rhythm stays `loose`**, unless you name a
  layout: gtrsnipe doesn't claim lengths its source never gave.

On 300 folk tunes written out and read back, every bar came back with exactly its rhythm in
`dashes` and in `columns`, against a third of the bars in `loose`. `dashes` is 1.46 times as
wide as `loose` over the whole set. The rules, the reasons and the measurements:
[`docs/app/DESIGN-tab-rhythm.md`](docs/app/DESIGN-tab-rhythm.md).

## Tab input: kept as written

A tab states where each note is played, and gtrsnipe keeps that. Play a `.tab`, convert it
to another tab or chart its chords, and you get the tab's own strings, frets and
hammer-on, pull-off and tap marks, bar for bar.

```bash
gtrsnipe -i riff.tab --play                                   # the tab, as written
gtrsnipe -i riff.tab -o riff.mid                              # its notes
gtrsnipe -i riff.tab -o mine.tab --refinger                   # let the mapper finger it
gtrsnipe -i riff.tab -o up.tab --transpose 2                  # new notes: re-fingered, and the header says so
gtrsnipe -i riff.tab -o up.tab --transpose 2 --no-refinger    # the same shapes, two frets up
gtrsnipe -i riff.tab -o dropd.mid --tuning DROP_D             # the same fingering, heard in drop D
gtrsnipe -i riff.tab -o dropd.tab --tuning DROP_D --refinger  # the same notes, fingered for drop D
```

- **By default** a tab keeps its fingering. It is re-fingered only when an option changes its
  notes (`--transpose`) or says how to finger it (`--single-string`), and then a
  `// Fingering:` line in the output says so. Mapper options do nothing to a kept tab; a
  one-line note says that too.
- **`--refinger`** always lets the mapper choose. The tab is then read in its own tuning and
  capo, and `--tuning` / `--capo` say what to finger it *for*.
- **`--no-refinger`** never moves a note to another string. `--transpose` slides each note
  along its string, and stops with the list of notes that can't.
- **What is read:** strings, frets, the marks `h`, `p` and `t`, the bar lines, and the
  header's tempo, time signature, tuning and capo. The tab's own `// Tuning:` and `// Capo:`
  lines are used unless you give `--tuning` or `--capo`. Bends, slides and other marks aren't
  read.
- **Rhythm is exact when the tab states it:** a `// Rhythm:` line or note-length letters, as
  gtrsnipe writes them (see [Tab output](#tab-output-the-dashes-say-how-long)). A bar that
  doesn't add up to a measure, after a hand edit say, is read like any other tab.
- **Otherwise rhythm is approximate.** Each bar is one measure, and a note's time is its
  column across the bar, which is how people read tabs. A tab's columns don't state
  durations. Of 300 folk tunes written out in the `loose` layout and read back, every note
  stayed in its bar, and a third of the bars came back with exactly their rhythm (steady
  passages do; bars mixing note values don't).

## Player / Visualizer

`gtrsnipe-play` renders a song as a live ASCII fretboard instead of writing a
file. It reuses the same parsers and the Viterbi fretboard mapper, so it accepts
every supported input format — with the same rhythm caveats (precise timing from
MIDI, approximate from an ASCII tab that doesn't state its rhythm). A `.tab` is shown with its own fingering, as written
(`--refinger` shows the mapper's instead). A 5-fret window auto-follows the playing up
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

# Step through it by hand: starts paused; . steps, space plays/pauses, q quits
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
NAME-or-0..127, which defaults to the MIDI file's own instrument; `--list-instruments`),
`--legato`, `--sustain {legato,string}` (see Note lengths below), `--refinger` (tab input),
plus the usual `--tuning`,
`--tuning-pitches`, `--drop-low-string`, `--num-strings`, `--max-fret`, `--capo`, and `--optimizer`.

**Note lengths.** Playback honors each note's own length: a held bass note rings under a
moving melody, and a rest is silent. `--legato` brings back the old behavior, where every
note sounds until the next one starts. A tab only says when to strike a string, not when to
stop it, so for tab input `--sustain` decides (in playback and MIDI output alike):
- `legato` (default): each note sounds until the next onset.
- `string`: each note rings until its own string is struck again, as on a guitar, so
  arpeggios and pedal notes keep sounding (at most one bar).

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
chord templates, with the bass note disambiguating inversions and slash chords. The lowest
note at the start of a bar counts as a chord tone even when it's short, so an arpeggiated bar
is named by its bass (as `--name-chords` names it over a tab).

**Extended chords** are named too: 9, maj9, m9, 7b9, 7#9, 11, m11, 13, maj13, m13 and 7sus4.
Three rules keep a melody note from being taken for an extension:

- The chord must be complete: its defining tones all sound (the fifth may be missing, and a
  13th's 9th), and nothing outside the chord does.
- Its root must be the bass. The same notes over another bass keep the simpler name, or read
  as a slash chord.
- add9 and 6/9 have no seventh to define them, so they are named only for a fret shape
  ([`--name-chord`](#naming-a-chord-shape---name-chord)), where every note is the chord. In a
  bar of music, a C triad with a D over it stays C.

**Names are spelled for the song's key.** The same chord is Ab in Eb major and G# in E major.
The key is, in order: `--key` (`--key Eb`, `--key F#m`, `--key "D dorian"`), the file's own
(ABC's `K:`, a MIDI key signature), else an estimate from the notes. The chart's header says
which, and `--key auto` always estimates.

- The estimate was right for 88% of 1,034 Nottingham folk tunes and 91% of 709 POP909 pop
  songs. The key *signature*, which is all that spelling depends on, was right for 93% and 99%.
  A song gets one key: a key change isn't followed.
- A MIDI file's "C major" is kept only if the notes agree, since sequencers write it by default.
  (All 112 POP909 files that declare a key say C major, and 10 are in it.)
- A slash chord's bass is spelled as the chord spells it: E/G#, not E/Ab.
- `--transpose` moves the key with the notes.

What a diagram shows is a choice, `--chart-voicing`, and the chart's header always says which.
Each diagram is captioned with its shape (`x32010`: low string first, `x` = muted).

- **`source`** (the default) draws each chord **as this song's tab fingers it** (for a `.tab`
  input, the tab's own fingering; otherwise the tab gtrsnipe would write): the bar's
  chord tones, if each string holds one fret and they make one hand shape (at most four
  fingers, an index barre counting as one, within four frets); else the bar's fullest
  simultaneous chord as fingered. A chord with no such bar gets a compact voicing, marked `*`.
- **`compact`** draws a compact root-position voicing of the chord's *name*: the chord tones
  within one octave, one note per string, placed where the mapper can finger them with the
  tightest fret span. It isn't the song's voicing (a C/E bar gets a root-position C).
- **`open`** (or `--prefer-open-chords`) draws the familiar first-position shape where one
  exists: C `x32010`, G `320003`, D `xx0232`, F `xx3211`, and so on. The shapes are found, not
  looked up: every chord tone present (a 4-note chord may drop its fifth), the chord's bass on
  the lowest string played, muted strings only at the bottom so it strums, at most four
  fingers within four frets. So it works in any tuning and with a capo (with capo 2, a D is
  drawn as the C shape you finger). Chords with no open shape get the compact voicing.

Key options: `-o FILE`, `--measures-per-line N`, `--chord-tone-threshold F`
(how long a note must sound in a bar to count as a chord tone), `--track N`,
`--chart-voicing {source,compact,open}` (`--prefer-open-chords` = `open`), `--shape-names`,
`--key KEY`, `--name-chord SHAPE`, plus the usual `--tuning`, `--tuning-pitches`, `--drop-low-string`,
`--num-strings`, `--capo`, and `--optimizer`.

### Shape names (`--shape-names`)

On a baritone or a down-tuned guitar you think in the shapes of standard tuning: the fingering
of a C chord is "a C shape", whatever it sounds like. `--shape-names` names chords that way, a
"generalized capo", in chord charts, `--name-chords` and `--name-chord`:

```bash
gtrsnipe -i song.mid -o song.chords.md --tuning BARITONE_B --shape-names   # C shape, sounds G
gtrsnipe --capo 2 --shape-names --name-chord 320003                          # G shape, sounds A
```

- It works for tunings that are standard shifted evenly on every string (E_FLAT, D_STANDARD,
  C_SHARP_STANDARD, the baritones, the bass and 7-string equivalents, or a custom tuning that
  shifts evenly), plus any capo.
- A drop or open tuning has no standard shape names, so its chords stay in concert pitch.
- A banner always says which convention is in use, and chart diagrams always show the notes
  actually played.

### Chord names over a tab (`--name-chords`)

Add `--name-chords` to ASCII tab output to write chord names above the staff:

```
   C        G             Am
e|--------|-----------3-|-------------|
B|-5------|-------------|---------5---|
G|-5------|---------4---|-----2h5-----|
D|-5------|-------5-----|---2---------|
A|-7------|---2h5-------|-0-----------|
E|-8------|-3-----------|-------------|
```

- Each bar is named as in a chord chart (`--chord-tone-threshold` applies). The lowest note
  at the start of a bar also counts, so an arpeggio's bass isn't lost among short notes.
- A name sits over its bar's first note. It's written where the chord changes, and again at
  the start of each line, which wraps with the tab (`--max-line-width`).
- Only plainly spelled chords are named: every chord tone present except perhaps the fifth,
  at most one extra note. A melody bar or a doubtful chord gets no name rather than a wrong one.
- Each bar is also named by halves, so a bar that changes chord midway gets both names (C
  then G, where naming the whole bar would read "G6"). Finer changes aren't named.
- Names are concert pitch (with a capo or an unusual tuning, the sounding chord), unless you
  ask for [shape names](#shape-names---shape-names).
- Names are spelled for the song's key, as in [chord charts](#chord-charts): `--key`, the
  file's own, else an estimate. A `//` line in the tab's header says which.
- The name line is ignored when the tab is read back in.

### Naming a chord shape (`--name-chord`)

Name the chord a fret shape plays, without any input file. List the frets from the lowest
string to the highest, `x` for a muted string:

```bash
gtrsnipe --name-chord x,3,2,0,1,0 --name-chord x,x,3,2,1,0
#   x,3,2,0,1,0      C          C3 E3 G3 C4 E4
#   x,x,3,2,1,0      Fmaj7      F3 A3 C4 E4
#   (tuning STANDARD (E2,A2,D3,G3,B3,E4); chord names are concert pitch)
gtrsnipe --tuning BARITONE_B --name-chord x,3,2,0,1,0      # the C shape plays G
gtrsnipe --capo 2 --name-chord x02220                      # compact form: B
gtrsnipe --name-chord x32033 --name-chord x3233x --name-chord 3x345x
#   x32033           Cadd9      C3 E3 G3 D4 G4
#   x3233x           C9         C3 E3 Bb3 D4
#   3x345x           G13        G2 F3 B3 E4
gtrsnipe --key E --name-chord x46664                       # C# (with no key: Db)
```

The shape is read in `--tuning` (or `--tuning-pitches`), with `--capo` and `--num-strings`.
The compact form (`x32010`) works when every fret is one digit. With no `--key`, each chord is
spelled in its own simplest key (Bb, Eb, Ab, F#; C#m, G#m), and its notes are spelled to match.

### Command-line help

Run `gtrsnipe --help` for the complete list of options. An abridged reference is in
[Command-line options](#command-line-options) below.

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
  notes. Kept for reproducing older fingerings. Since the 0.6.1 fixes its output
  no longer matches pre-0.3.0 releases exactly.

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

## Command-line options

An abridged reference, grouped as in `gtrsnipe --help`. Run `gtrsnipe --help` for the complete list.

**General**
- `-i INPUT, --input INPUT`: Path to the input file (.mid, .mp3, .wav, etc.).
- `-o OUTPUT, --output OUTPUT`: Path(s) to the output file(s) (e.g., `-o out.mid -o out.tab -o song.chords.md`). Repeatable. Not required with `--play`, `--analyze`, `--solve-tuning` or `--homograph`. A `.chords`/`.chords.md` output writes a chord sheet.
- `--nudge NUDGE`: An integer to shift the transcription's start time to the right. Each unit corresponds to roughly a 16th note.
- `--first-note-is-downbeat`: Shift the entire timeline so that the first note of the song starts at beat 0.
- `-y, --yes`: Automatically overwrite the output file if it already exists.
- `--track TRACK`: The track number (1-based) to select from a multi-track MIDI file. If not set, all tracks are processed. For a multitrack MIDI, you will want to select a single instrument track to transcribe.
- `--analyze`: Rank the tunings whose range fits the song by how playable its tab is in each (the mapper's score per note with your settings, frets, hand travel, open strings), then exit. No `-o` needed; `--bass` ranks bass tunings.
- `--solve-tuning NOTES`: Inverse solve: given a comma-separated target melody (note names with octave, e.g. `'C4,C4,G4,G4,A4,A4,G4'`), find a tuning under which an all-open-string tab plays it. Prints the tuning; add `--play` to hear it, or `-o FILE.tab/.mid` to write it. No `-i` needed.
- `--max-strings MAX_STRINGS`: Max strings the tuning solver (and `--homograph-mode free`) may use (default: 12).
- `--transpose TRANSPOSE`: Transpose the music up or down by N semitones (e.g., 2 for up, -3 for down). Applied first, before the range filter and `--analyze`, so it reaches every output and `--play`; the key moves with the notes.
- `--key KEY`: The song's key (`Eb`, `F#m`, `'D dorian'`). It spells chord names (Ab or G#) in chord charts, `--name-chords` and `--name-chord`, and sets the key signature and note spelling of ABC output. Default: the file's own key (ABC `K:`, a MIDI key signature), else an estimate from the notes; `auto` always estimates. See [Chord charts](#chord-charts).
- `--no-articulations`: Transcribe with no legato, taps, hammer-ons, pull-offs, etc.
- `--refinger`, `--no-refinger`: Tab input: whose fingering to show. By default a tab keeps its own, as written, unless an option changes its notes. `--refinger` always uses the mapper; `--no-refinger` never moves a note to another string. See [Tab input](#tab-input-kept-as-written).
- `--sustain {legato,string}`: Tab input: `legato` (default) holds each note until the next onset; `string` lets it ring until its own string is struck again, as a guitar does (at most one bar). Shapes playback and MIDI output alike.
- `--staccato`: Do not extend note durations to the start of the next note, instead giving each note an 1/8 note duration. When converting from ASCII tab.
- `--max-line-width MAX_LINE_WIDTH`: Max number of vertical columns per line of ASCII tab (default: 80). Bars are never split: a row holds as many whole bars as fit, and a wider bar gets a row to itself.
- `--tab-rhythm {dashes,columns,loose}`: ASCII tab output: how a bar's columns carry time. `dashes` (default): the dashes after a note name its length, with a `// Rhythm:` legend line; exact and compact. `columns`: a note's column across its bar is its time; exact with no legend, sometimes wide. `loose`: spacing only hints at the rhythm (the layout up to v0.7.0). A tab made from a tab that didn't state its rhythm stays `loose` unless you choose. See [Tab output](#tab-output-the-dashes-say-how-long).
- `--tab-base {auto,1/1,1/2,1/4,1/8,1/16,1/32}`: With `--tab-rhythm dashes`: the note that one dash stands for (default: `auto`, the longest note value no longer than the tune's shortest step).
- `--tab-odd-bars {columns,nearest,error}`: With `--tab-rhythm dashes`: what to do with a bar holding a length the table lacks. `columns` (default): write that bar with columns as time and name it in the legend; `nearest`: use the nearest lengths and name the bar as approximate; `error`: stop and list such bars.
- `--tab-letters`: ASCII tab output: a line of note lengths over each row (`W H q e s t`; a dot adds half), on top of any `--tab-rhythm`. Read back when the tab is used as input.
- `--name-chords`: ASCII tab output: chord names above the staff (see [Chord names over a tab](#chord-names-over-a-tab---name-chords)).
- `--single-string {1,2,3,4,5,6}`: Force all notes onto a single string (1-6, high e to low E). Ideal for transcribing legato/tapping runs.
- `--normalize-pitch`: Shift notes (+12 or -12) until they fit within the specified tuning and max fret range. Used when the input has many out-of-range notes that would otherwise be dropped.
- `--debug`: Enable detailed debug logging messages.

**Instrument options**
- `--capo CAPO`: Specify a capo position. All fret numbers will be relative to the capo. A `.tab` input's own `// Capo:` line is used when this isn't given.
- `--tuning NAME`: Specify the guitar tuning, or `PIANO` for full-range MIDI passthrough: every note kept, MIDI output only (default: STANDARD). NAME is any tuning in [the list below](#current-supported-instrument-tunings).
- `--num-strings {4,5,6,7}`: Force the number of strings on the tab staff (4, 5, 6, or 7). Defaults to 4 for bass and 6 for guitar.
- `--max-fret MAX_FRET`: Maximum fret number on the virtual guitar neck (default: 24).
- `--tuning-pitches LOW,..,HIGH`: Define a custom tuning by comma-separated note names, low string to high (e.g. `'A1,E2,A2,D3,F#3,B3'`). Overrides `--tuning`.
- `--scale-length INCHES`: Scale length for string-tension physics (default: 25.5 guitar, 27 baritone, 34 bass).
- `--string-gauges GAUGES`: String gauges for tension physics, low string first like `--tuning-pitches` (a thin-to-thick set such as `'10 13 17 26w 36w 46w'` is flipped for you, except for a re-entrant tuning such as Nashville, which is read as written). `w` = wound, `p` = plain; unsuffixed gauges above .020 count as wound (a plain .022 is `22p`). Default: 10-46 for STANDARD (10-59 7-string, 13-62 BARITONE_B, 45-105 bass), else a balanced set designed for the tuning.
- `--drop-low-string SEMITONES`: Lower the lowest string by N semitones (2 = drop-D style), on any tuning / string count.
- `--bass`: Bass mode: a 4-string staff in the bass version of `--tuning` (BASS_STANDARD by default; with `--tuning DROP_D` or `E_FLAT`, BASS_DROP_D or BASS_E_FLAT; a `BASS_` tuning is used as it is). A tuning with no bass version is an error.
- `--velocity-cutoff [0-127]`: Ignore MIDI notes with a velocity lower than this value (default: 0).
- `--min-note-override MIN_NOTE_OVERRIDE`: Override the calculated lowest note for frequency constraining (e.g., `'E2'`). Ignored with `--no-constrain-frequency`.
- `--max-note-override MAX_NOTE_OVERRIDE`: Override the calculated highest note for frequency constraining (e.g., `'E4'`). Ignored with `--no-constrain-frequency`.

**Audio-to-MIDI pipeline options** _(require `pip install 'gtrsnipe[audio]'`; `--stem-track` also needs `[separation]`)_
- `--nr`: Enables noise/reverb reduction on the audio stem.
- `--stem-track {guitar,bass,drums,vocals,piano,other}`: The instrument stem to isolate with Demucs. The default model, htdemucs_6s, has a `guitar` stem.
- `--demucs-model DEMUCS_MODEL`: The demucs model to use for separation (default: htdemucs_6s). See [Demucs model selection](#demucs-model-for-stem-separation).
- `--no-constrain-frequency`: Audio input: don't constrain pitch detection to the tuning's range (constraining is on by default).
- `--low-pass-filter`: Apply a low-pass filter to the audio stem based on the instrument's max frequency.
- `--pitch-engine {librosa}`: The pitch detection engine to use. Currently `librosa` (pYIN) only; the experimental basic-pitch engine was removed in v0.3.0.

**Tab homographs:** `--homograph SONG [SONG ...]` and the `--homograph-*` options. See [Tab homographs](#tab-homographs-one-tab-a-different-song-per-tuning).

**Tuning information**
- `--list-tunings`: List all available tuning names and exit.
- `--show-tuning [TUNING_NAME]`: Show a tuning's notes and each string's tension on your guitar, with restring suggestions, and exit. With no name, the tuning set by `--tuning-pitches`/`--drop-low-string` (see [Custom tunings](#custom-tunings)).
- `--name-chord SHAPE`: Name the chord a fret shape plays (e.g. `x,3,2,0,1,0`) in the current tuning, and exit. Repeatable (see [Naming a chord shape](#naming-a-chord-shape---name-chord)).

**Player mode** (`--play`; interactive terminal): `--play`, `--view`, `--clock`, `--tempo`, `--grid`, `--window`, `--width`, `--fps`, `--orientation`, `--hand`, `--audio`, `--midi-port`, `--soundfont`, `--instrument`, `--no-clear`, `--legato`. See [Player / Visualizer](#player--visualizer).

**Chord chart output** (`-o SONG.chords.md`): `--measures-per-line` (default: 4), `--chord-tone-threshold` (default: 0.15), `--chart-voicing {source,compact,open}` (what the diagrams show; default: the song's own fingering), `--prefer-open-chords` (= `--chart-voicing open`), `--shape-names` (name chords by the standard-tuning shape; also for `--name-chords` and `--name-chord`). See [Chord charts](#chord-charts).

**Profiles / config** (`.gtrsnipe`): `--profile NAME[,NAME]`, `--no-defaults`, `--config-dir CONFIG_DIR`, `--save-args NAME`. See [Config profiles](#config-profiles-gtrsnipe).

**Mapper tuning/configuration (advanced)**
- `--optimizer {viterbi,greedy}`: Fretboard mapping strategy: `viterbi` (global DP optimum, default) or `greedy` (legacy per-step choice).
- `--mono-lowest-only`: ASCII tab output only: where notes sound together, write just the one on the lowest string. Other outputs and playback keep every note.
- `--fret-span-penalty FRET_SPAN_PENALTY`: Penalty for wide fret stretches (default: 100.0).
- `--movement-penalty MOVEMENT_PENALTY`: Penalty for hand movement between chords (default: 3.0).
- `--string-switch-penalty STRING_SWITCH_PENALTY`: Penalty for switching strings (default: 5.0).
- `--high-fret-penalty HIGH_FRET_PENALTY`: Penalty for playing high on the neck (default: 5).
- `--low-string-high-fret-multiplier LOW_STRING_HIGH_FRET_MULTIPLIER`: Multiplier penalty for playing high on the neck on low strings (default: 10).
- `--unplayable-fret-span UNPLAYABLE_FRET_SPAN`: Fret span considered unplayable (default: 4).
- `--sweet-spot-bonus SWEET_SPOT_BONUS`: Bonus for playing in the ideal lower fret range (default: 0.5).
- `--sweet-spot-low SWEET_SPOT_LOW`: Lowest fret of the "sweet spot" (default: 0, open).
- `--sweet-spot-high SWEET_SPOT_HIGH`: Highest fret of the "sweet spot" (default: 12).
- `--ignore-open`: Don't consider open when calculating shape score.
- `--legato-time-threshold LEGATO_TIME_THRESHOLD`: Max time in beats between notes for a legato phrase (h/p) (default: 0.5).
- `--tapping-run-threshold TAPPING_RUN_THRESHOLD`: With `--single-string`: runs longer than this many notes are considered for tapping (default: 2, i.e. runs of 3 or more).
- `--dedupe`: Enable de-duplication of notes with the same pitch within a chord. Useful for cleaning up MIDI from non-guitar sources.
- `--quantization-resolution {0.0125,0.025,0.0625,0.125,0.25,0.5,1.0}`: Quantization resolution (default: 0.125). Used by the mapper to determine simultaneous sounding of notes (chords) and by the ASCII tab generator mainly for spacing purposes.
- `--prefer-open`: Prefer open strings over their fretted equivalents (e.g., open B over G-string fret 4).
- `--fretted-open-penalty FRETTED_OPEN_PENALTY`: The penalty score applied to fretted notes that could be open strings (default: 20.0).
- `--barre-bonus BARRE_BONUS`: Bonus awarded to fingerings that use a barre/single finger (default: 0.0).
- `--barre-penalty BARRE_PENALTY`: Penalty applied to fingerings that use a barre/single finger (default: 0.0).
- `--let-ring-bonus LET_RING_BONUS`: Bonus awarded for fingerings that allow previous notes to ring out (default: 0.0).
- `--diagonal-span-penalty`: Penalize fingerings with an unplayable fret span between consecutive notes.
- `--no-pre-quantize`: Skip the default pre-quantization pass (which snaps all notes to the quantization grid before mapping).
- `--dynamic-quantize`: Quantize notes to a dynamic beat grid detected from the audio.

## Usage Examples

**Full audio-to-tab transcription**

Run the complete pipeline on a mixed audio file to generate a bass tab in drop D. (`--bass --tuning DROP_D` selects the same tuning.)

[`gtrsnipe -i x:\S.O.D.mp3 -o march_of_the_S.O.D.tab --stem-track bass --tuning BASS_DROP_D -y`](https://github.com/scottvr/gtrsnipe/wiki/v0.2.0)

**Audio-to-MIDI only**

Extract the guitar part from a song and save it as a MIDI file, stopping the pipeline there.

`gtrsnipe -i "another_song.wav" -o "guitar_part.mid" --stem-track guitar`

**Transcribing from Clean Audio**

If you already have a clean, isolated guitar track, you can skip the demucs and noise reduction steps.

`gtrsnipe -i "my_clean_riff.wav" -o "my_riff.tab"`

**MIDI-to-Tab (Classic V1 Functionality)**

[`gtrsnipe -i "MrCrowley.mid" -o "mrcrowley.tab" --track 5`](https://github.com/scottvr/gtrsnipe/wiki/2.-Example-%E2%80%90-Mr-Crowley-organ-intro)

# Other Examples

[All other examples and detailed usage information has been moved to the Wiki](<https://github.com/scottvr/gtrsnipe/wiki/0.-GTRSnipe-(aka-%22guttersnipe%22)>)

## Advanced Usage: Mapper Tuning

The real power of gtrsnipe comes from its customizability. You can fine-tune the fretboard mapping algorithm and the audio separation models to get the perfect transcription. [Detailed documentation with troubleshooting examples are being created in the wiki.](https://github.com/scottvr/gtrsnipe/wiki/1.-FretboardMapper-Algorithm-Configuration-and-Tunables)


### Current Supported Instrument Tunings

`--tuning` accepts every name below, plus `PIANO` (full-range MIDI passthrough).
Strings are listed low to high.

```
$ gtrsnipe --list-tunings
Available Tunings:
- STANDARD              : E2 A2 D3 G3 B3 E4
- E_FLAT                : Eb2 Ab2 Db3 Gb3 Bb3 Eb4
- DROP_D                : D2 A2 D3 G3 B3 E4
- D_STANDARD            : D2 G2 C3 F3 A3 D4
- DROP_C                : C2 G2 C3 F3 A3 D4
- OPEN_G                : D2 G2 D3 G3 B3 D4
- OPEN_E                : E2 B2 E3 G#3 B3 E4
- DADGAD                : D2 A2 D3 G3 A3 D4
- OPEN_D                : D2 A2 D3 F#3 A3 D4
- OPEN_C6               : C2 A2 C3 G3 C4 E4
- C_SHARP_STANDARD      : C#2 F#2 B2 E3 G#3 C#4
- DROP_B                : B1 F#2 B2 E3 G#3 C#4
- BASS_STANDARD         : E1 A1 D2 G2
- BASS_DROP_D           : D1 A1 D2 G2
- BASS_E_FLAT           : Eb1 Ab1 Db2 Gb2
- SEVEN_STRING_STANDARD : B1 E2 A2 D3 G3 B3 E4
- SEVEN_STRING_DROP_A   : A1 E2 A2 D3 G3 B3 E4
- BARITONE_B            : B1 E2 A2 D3 F#3 B3
- BARITONE_A            : A1 D2 G2 C3 E3 A3
- BARITONE_C            : C2 F2 Bb2 Eb3 G3 C4
```

### Demucs Model for stem separation

**Demucs Model Selection** `(--demucs-model)`

Demucs is a state-of-the-art music source separation model. Several models are available, each with specific characteristics. Choosing the right one can significantly improve the quality of the isolated audio stem.

- **htdemucs**: The standard 4-stem Hybrid Transformer Demucs model. A great all-rounder. (Guitar goes to its "other" stem.)
- **htdemucs_ft**: A version of htdemucs fine-tuned on extra data. May offer better quality at the cost of speed.
- **htdemucs_6s**: gtrsnipe's default. A 6-source version that can additionally attempt to separate piano and guitar, though quality may vary.
- **hdemucs_mmi**: The v3 Hybrid Demucs model, retrained on more data.
- **mdx / mdx_extra**: Models known for high performance, trained on the MusDB HQ dataset.
- **mdx_q / mdx_extra_q**: Quantized (smaller, faster) versions of the mdx models, which may have slightly reduced quality.
