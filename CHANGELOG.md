# Changelog

All notable changes to gtrsnipe are documented here.
This project adheres to [Semantic Versioning](https://semver.org/).

**Versioning while in 0.x.** The minor version marks breaking changes (or a
deliberate milestone); the patch version marks everything else, including
backward-compatible features and fixes. This is the left-most-non-zero rule that npm
and Cargo apply to 0.x version ranges. Full SemVer applies from 1.0.0. The public API
is the CLI flags and the file formats gtrsnipe reads and writes; report wording is
not part of it.

## [0.6.7] — 2026-09-27

Step 3 continues: F03 from `docs/dev/BACKLOG.md`.

### Changed
- **`--analyze` ranks tunings by how playable the song is in each (F03).** It used to list
  the tunings whose range fits.
  - It now fingers the song in each of them, with your own mapper settings, and ranks them
    by the mapper's score per note.
  - Each row shows how many points per note harder than the best tuning it is, the frets
    used, the average hand travel between fretted notes, and the share of open strings.
  - Ties (the default weights don't prefer open strings to a barre) go to less travel,
    then more open strings.
  - A guitar gets guitar tunings (7-string and baritone included) and `--bass` gets bass
    tunings; before, all were mixed. A custom `--tuning-pitches` tuning is ranked too.

### Fixed
- `--analyze` no longer demands `-o/--output`; it never writes one.

## [0.6.6] — 2026-09-27

Step 3 begins: B07 and F06 from `docs/dev/BACKLOG.md`.

### Added
- **Playability of homograph tabs (F06).**
  - Each anchored or middle solution now reports its *discomfort*: how many mapper points
    per note its fingering of song A scores below the tab gtrsnipe writes for A alone, in the
    same tuning and key. It also reports the fret range used.
  - `--homograph-max-discomfort POINTS` rejects placements over the limit. The solver then
    fingers up to 16× more placements looking for one within it.
  - `gtrsnipe-research scan` takes `--max-discomfort` and `--max-fret`, and lists each
    candidate's discomfort.
  - Finding (DESIGN-homograph, RESULTS-R04 "Playability"): string tension barely filters
    shared tabs, but comfort does. Of 50 sampled folk pairs, 49 have a tab, but only 19 have
    one within 50 points per note, 4 within 20, and none within 5. A's own tab scores −2 to
    −7 per note.

### Fixed
- **MIDI track and instrument names were dropped (B07).** The mido path never read
  `track_name`/`instrument_name` events, so every track was "Acoustic Grand Piano". *Tab
  titles for named tracks now read "Title (Melody)".*

## [0.6.5] — 2026-09-27

R05 finishes the research items planned for step 2 of `docs/dev/BACKLOG.md`.

### Added
- **`gtrsnipe-research aswritten TAB…`**: can a tab's *own* fingering be retuned into
  another song?
  - Every note the tab puts on one string must move by one interval.
  - Windows slide over the tab and are tested against evenly spaced corpus passages. The
    output counts trivial hits (each string maps one pitch to one pitch), transpositions of
    the passage itself, and unrelated-sounding hits.
  - The best hits go through the solver's as-written check.
- `docs/dev/RESULTS-R05-aswritten.md`, from Bach's Cello Suite No. 1 Prelude and six
  successive Asturias fingerings (`examples/aswritten/`):
  - As written is about 10,000× stricter than a free fit.
  - Which passages a tab can become depends on the fingering.
  - Past 16 notes, nothing unrelated-sounding fits either piece's real fingering.
- `docs/wiki/`: a snapshot of the whole GitHub wiki, with Windows-safe file names.
- `docs/dev/PROOF-alignment.md`:
  - the stutter-invariance principle: stutter-invariant, subadditive offset statistics stay
    pseudometrics under warping;
  - a subsection relating it to the Fréchet distance, DTW and elastic metrics (ERP, TWED,
    MSM);
  - a checklist of citations to verify.

## [0.6.4] — 2026-09-26

Step 2 of `docs/dev/BACKLOG.md`, continued: R04, the corpus homograph scan.

### Added
- **`gtrsnipe-research scan CORPUS…`**: finds passages of different songs that one tab can
  play under two tunings.
  - It buckets marked phrases (or sliding windows) by rhythm and computes the richness of
    every same-rhythm pair from different works.
  - It counts, per length, what is eligible, what is trivial, and what sounds unrelated.
  - It runs the full homograph solver (anchored and middle, string physics) on the best
    pairs and on a random sample per length, and writes verified shared tabs on request.
  - Options: `--cross-corpus`, `--named-melodies`.
- `docs/dev/RESULTS-R04-scan.md` with charts (`docs/dev/r04_plot.py`, `docs/dev/figures/`):
  - Folk song (Essen + Meertens): a third of same-rhythm 8-note phrase pairs from different
    tunes share a tab and sound unrelated; 8% at 12 notes, 3% at 16.
  - The solver places 93–100% of sampled pairs on a real guitar: A in STANDARD, B a retune
    of the same guitar.
  - Pop (Lakh): mostly trivial pairs (few distinct pitch pairs), but 4,467 unrelated-sounding
    32-note pairs remain.

### Changed
- MIDI melody extraction no longer takes "Voice Oohs"/"Aahs" or pad tracks for the
  melody.

## [0.6.3] — 2026-09-26

Step 2 of `docs/dev/BACKLOG.md`, continued: R03 and R07.

### Added
- **`gtrsnipe-research families CORPUS`**: tune-family retrieval with every offset
  measure (R03).
  - Each measure ranks every melody against the others on one shared pairing: pitch
    sampled at evenly spaced points.
  - Scores are tie-aware MAP and AUC, with bootstrap intervals.
  - Logistic pair models, cross-validated by tune family, test whether the
    candidates add anything to the baselines.
  - Result ([`docs/dev/RESULTS-R03-families.md`](docs/dev/RESULTS-R03-families.md)):
    on MTC-ANN and MTC-FS-INST, transposition-invariant Hamming wins, and richness
    adds nothing (+0.002 to +0.006 MAP). It is a guitar statistic, not a similarity
    measure.
- `docs/dev/PROOF-alignment.md` and `alignment_check.py` (R07): under optimized
  (warping-path) alignment, log-richness, switch count and total variation stay
  pseudometrics; entropy and modal share don't (a 3-note counterexample).
  - `coupled_transposition_structure.md` gets pointers in §4.4 and §7.

## [0.6.2] — 2026-09-26

The first research tools (step 2 of `docs/dev/BACKLOG.md`: R01, R02, R06).

### Added
- **`gtrsnipe-research`**, a new command for work across melody corpora. It isn't
  imported by `gtrsnipe` itself.
  - `corpus build/info/show/list` reads the Essen Folksong Collection, the Meertens
    Tune Collections (MTC-ANN, MTC-FS-INST, with tune-family labels), Nottingham,
    POP909 and Lakh into one monophonic format and caches each corpus as a single
    gzipped file.
    - Kern files go through a new reader that keeps phrase marks. It matches
      music21 note for note on 8,469 of the 8,473 Essen files; the other 4 have
      malformed tie chains, which it holds as one note.
    - For MIDI it takes a melody-named part, or else the skyline of the other parts.
  - `profile A B` prints the offset profile of two aligned melodies: richness,
    entropy, coverage C₁…C₆, transposition-invariant Hamming, switches, total
    variation and reuse. A and B can be corpus melodies or phrases
    (`essen:deut4659#p2`), files or inline melodies.
- `docs/dev/LITERATURE-offsets.md`: the prior-art survey for the offset measures
  and tab homographs.
- `docs/dev/collision_plot_template.py`: a figure template for the corpus scan
  (placeholder curves).

### Fixed
- **Non-editable installs were missing most of gtrsnipe.** The package pattern
  matched only the top-level package, so a wheel (e.g. `pip install
  git+https://…`) held 3 of 56 modules. Editable installs (`pip install -e .`,
  the README's method) were unaffected.

## [0.6.1] — 2026-09-26

A correctness sweep (step 1 of `docs/dev/BACKLOG.md`).

### Fixed
- **ABC input was decoded wrong.** The parser ignored the key signature and read
  chord symbols (`"G7"`), lyrics lines and comments as notes; it got 0 of the 1,034
  Nottingham folk tunes right. It's rewritten and now handles:
  - key signatures, including modes (`Dmix`, `E minor`) and explicit accidentals;
  - accidentals carried through the bar as the ABC version says (as music21 does);
  - ties, including the detached `C2 -C2` form legacy files use, where a tied note
    keeps its accidental;
  - broken rhythm, tuplets, chords, rests and multi-bar rests;
  - mid-tune key, length and meter changes;
  - skipping grace notes, decorations and other non-note text;
  - only the first tune and the first voice.

  It now matches music21 note for note on 94% of those tunes; the rest are music21
  quirks.
- **RIFF-wrapped MIDI** (`RIFF…RMID`, 259 files in Lakh) came back as an empty
  song. It's now read. Files that aren't MIDI at all raise a clear error instead of
  returning nothing, and out-of-range MIDI data bytes are tolerated.
- **Tabs with hammer-ons/pull-offs read back wrong.** The `h`/`p` letter pushed the
  fret digits one column late, so a chord with a hammered note decoded as an
  arpeggio and hammered notes read late. The letter now goes before the digits.
  *Generated tabs with techniques change byte-for-byte (they now read back
  correctly).*
- **`--num-strings 7` dropped the 7-string's low B string.** The range filter used
  STANDARD instead of the resolved tuning, so every note below E2 was discarded.
- An explicit `--tuning STANDARD` now overrides a `.tab`'s own `// Tuning:`
  header. Only the default defers to the header.

### Removed
- The empty `PdfTabGenerator` stub. Pretty PDF output stays on the backlog (F05).

### Changed
- The v0.3.0-era planning docs moved to `docs/dev/archive/`.

## [0.6.0] — 2026-09-26

### Added
- **Tab homographs** (`--homograph A B [C …]`): one ordinary, fretted, playable
  tab that plays a different song in each tuning. Two aligned songs share a tab iff
  their note-for-note intervals split into ≤ N classes (one per string; see
  [`docs/dev/DESIGN-homograph.md`](docs/dev/DESIGN-homograph.md)). The report walks
  through each check in turn: alignment → **richness** (distinct intervals) → *free* /
  *anchored* (A keeps `--tuning`, an ordinary tab of A) / *middle* (both tunings
  retune one strung guitar) / *as written* (does A's own `.tab` fingering retune?).
  It names the first obstacle, verifies every solution by decoding, writes
  `-o shared.tab` with every song's key in the header, and `--play`s it in any
  song's tuning. Songs are files (`.mid[:TRACK]`, `.abc`, `.tab`, `.vex`, each
  with an optional `@START-END` onset window) or inline melodies
  (`"C4 C4 G4:2 r:1 C3+E3+G3"`). Knobs: `--homograph-mode`, `-rhythm` (strict /
  ratio slop / sequence), `-subdivide` ("ta" ≈ "ti ti": smear repeated notes or
  re-strike), `-transpose`, `-transpose-a`, `-max-retune`, `-octaves`, `-neutral`,
  `-play`.
- **String physics** (`gtrsnipe/guitar/strings.py`): tension from gauge / scale /
  pitch (matches D'Addario EXL110 within 1–2%), plain steel's gauge-independent
  breaking pitch (≈ A4 at 25.5″), wound-core headroom, slack limit, and
  restring suggestions. Homograph retunes are costed and flagged with it.
  `--scale-length`, `--string-gauges` configure the instrument.
- Worked public-domain examples in `examples/homograph/`.
- Dev note [`docs/dev/coupled_transposition_structure.md`](docs/dev/coupled_transposition_structure.md)
  (+ `triangle_check.py`): the offset-sequence analysis behind the homograph's
  *richness* (the Hill order-0 count of distinct note-for-note intervals). It covers
  which offset statistics are metrics modulo transposition, the explicit
  counterexamples at other Hill/Rényi orders, and prior-art names.
- An adversarial multi-agent review of the feature found and confirmed 22
  issues before release (middle mode not a superset of anchored, the wound-string
  model, re-rhythm edge cases, rendering). All are fixed, each with a regression test.

### Fixed
- **`-i x.tab` now honors the tab's own `// Tuning:` header** when no tuning is
  given, for the whole run (decode, range filter, mapping, and any tab output),
  as if `--tuning-pitches` had named it. Before, the CLI always passed STANDARD
  pitches to the parser, so the v0.5.0 tab round-trip only worked through the API
  (a DADGAD tab decoded as if standard). An explicit `--tuning`/`--tuning-pitches`
  still overrides; header-less tabs read as 6-string standard, as before.
- Note names `Cb` and `B#` were an octave off (`Cb4` gave B4, `B#3` gave C3), in
  `--tuning-pitches` and anywhere else note names are read.
- `--save-args` no longer writes per-run inputs `--solve-tuning` / `--homograph`
  into a profile (a saved `--solve-tuning` turned every later run into a solve).

## [0.5.0] — 2026-09-25

Unified-I/O refactor (design: [`docs/dev/DESIGN-unified-io.md`](docs/dev/DESIGN-unified-io.md)).
The player, chord charts, and converter are now one tool over a shared option
surface and an event-driven transport. **Existing `gtrsnipe -i x -o y.{tab,mid,abc,vex}`
invocations are unchanged (byte-identical output).**

### Added
- **Custom tunings.** `--tuning-pitches "A1,E2,A2,D3,F#3,B3"` (low string → high)
  defines any tuning, any string count; `--drop-low-string N` lowers the lowest
  string by N semitones (2 = drop-D style) on any tuning. Works across all modes.
- **Inverse tuning solver.** `--solve-tuning "C4,C4,G4,G4,A4,A4,G4"` finds a tuning
  under which an all-open-string tab plays that melody — the tab reveals none of
  the tune (it lives entirely in the tuning). Prints the tuning + tab; `--play` to
  hear it, `-o FILE.tab/.mid` to write it. No `-i` needed. (Also a handy
  alternate-tuning finder.)
- **Config profiles (`.gtrsnipe`).** Save long option sets and reuse them.
  `--profile NAME` (repeatable and/or comma-separated; applied in order) loads
  option files from `./.gtrsnipe`, `~/.gtrsnipe`, or `$GTRSNIPE_HOME`
  (`--config-dir` overrides); a `defaults` profile auto-loads (`--no-defaults` to
  skip). Explicit CLI args always override profile values. `--save-args NAME`
  writes the current non-default options back to a profile. Simple format:
  `name value`, `name = value`, or bare `name` for flags; `#` comments. Works
  across all three commands, since a profile is just prepended argv re-parsed.
- **One canonical tool.** `gtrsnipe` now also:
  - writes a **chord sheet** as an output format: `-o SONG.chords.md` (or `.chords`);
  - **plays/visualizes** with `--play [--view {fretboard,tab}]`, `-o` no longer
    required. Because `--play` runs after the full input preamble, it inherits
    audio-input transcription, `--normalize-pitch`, `--transpose`, and frequency
    range — you can now `gtrsnipe -i song.wav --play`.
- **Full mapper option surface everywhere.** The player and chord charts now
  accept all 33 mapper knobs (`--fret-span-penalty`, `--sweet-spot-*`, `--barre-*`,
  `--let-ring-bonus`, …), not the previous ~6.
- **Transport controls** in the player: `space` pause/resume (toggle), `.`/`,`
  step (while paused), `←`/`→` seek ±1 bar, `[`/`]` tempo, `g`/`end` jump, `h`
  help, `q` quit — with audio resynced on seek/pause.
- **Curses player** on a real terminal: alternate screen (scrollback preserved &
  restored), non-blocking input (live pause during playback), and terminal-resize
  re-layout. Piped/redirected output falls back to a plain stream.

### Changed
- Argument definitions and `MapperConfig` construction are defined once in
  `gtrsnipe/arguments.py` and composed by every CLI (was declared/duplicated 3×).
- The three player Clock classes were replaced by one event-driven `Transport`
  whose audio onsets fire at true times (independent of the display frame rate).
- `gtrsnipe-play` / `gtrsnipe-chords` remain as curated convenience stubs over the
  same engine.
- **Tuning tuples are now ordered low string → high** (the enum data,
  `--show-tuning`/`--list-tunings`, and `--tuning-pitches`), matching how tunings
  are conventionally named. The internal string *index* is unchanged (0 = highest;
  tab staves still put the fattest string on the bottom row) — verified: resolved
  open-string pitches and all tab/mid/abc/vex output are unchanged.

### Fixed
- **ASCII tab parser honors the tuning.** It previously assumed standard/bass
  tuning regardless of `--tuning`, so a tab read under any other tuning produced
  wrong pitches. It now decodes in the configured (named or custom) tuning.
- **Generated tabs round-trip.** The parser reads the `// Tuning:` header and
  accepts any string labels (not just `eBGDAE`), so a generated tab can be re-read
  as input in its own tuning — or in a different one (explicit `--tuning` wins).
- **6-string low-E no longer dropped.** String-count detection uppercased `e`/`E`
  to one key, mis-counting 6 strings as 5 and dropping low-E notes on single-block
  tabs; it now uses the tuning header's count (else the first contiguous run).

### Testing
- Opt-in, profile-driven golden-output regression gate (`tests/golden/`, skips
  when no local fixtures are present) — turn a tuned real piece into a pre-release
  check without committing copyrighted inputs.

## [0.4.0] — 2026-09-24

### Added
- **Player / fretboard visualizer** (`gtrsnipe-play`). Renders any supported
  input (MIDI/ABC/VexTab/ASCII-tab) as a time-driven ASCII fretboard: an
  auto-following 5-fret window that tracks the playing up and down the neck.
  Three timing modes via `--clock`: `tempo` (at the song's tempo), `metronome`
  (a fixed `--grid` beat step), and `step` (advance manually with a keypress,
  quit with `q`). Reuses the existing parser + Viterbi mapper unchanged; the
  timeline, clock, and renderer layers are decoupled so browser/Qt renderers
  can be added later without touching the core. Rhythm fidelity follows the
  input — precise from MIDI, approximate from ASCII tab.
  - `--track N` selects a single MIDI track (1-indexed), matching the converter.
  - `--orientation {horizontal,vertical}` rotates the board (frets as columns,
    or chord-diagram style top-to-bottom); `--hand {right,left}` mirrors the
    neck for left-handed players.
  - `--view tab` renders a horizontally-scrolling ASCII tab staff instead of the
    neck — notes flow right-to-left under a fixed playhead as the clock advances
    (a "7-bit terminal Guitar Hero"). `--width` sets the viewport columns.
  - `--audio {midi,fluidsynth}` makes the player emit sound. `midi` streams
    note-on/off to a MIDI port (route it to a DAW/VST host or system synth) via
    `mido` + `python-rtmidi` (the new `[play]` extra); `fluidsynth` renders a
    SoundFont directly with no external host (`pyfluidsynth`, the `[synth]`
    extra). Missing backends fail with an install hint, not a traceback.
  - `--instrument` selects the voice by General MIDI program number (0-127) or
    name substring (e.g. `nylon`, `distortion guitar`); `--list-instruments`
    prints the GM set.
  - Smooth scrolling: the display animates between onsets at `--fps` (default 12)
    and shows a continuous `bar N/total beat X.x` readout — the bar ratio doubles
    as a progress bar, and the moving readout means long rests in ensemble MIDI
    keep visibly playing instead of looking like the app hung.

### Fixed
- **Last note no longer cut off.** Auto-clock playback marked the final frame
  with no dwell, so its note was struck and immediately released; every frame
  now dwells for its duration.
- **FluidSynth error clarity.** When the native `libfluidsynth` C library is
  missing (but pyfluidsynth is installed), the error now points at the C library
  (port/brew/apt) and the MacPorts `DYLD_FALLBACK_LIBRARY_PATH` tip, instead of
  telling the user to reinstall pyfluidsynth.
- **librosa 1.0 compatibility.** The audio-transcription path crashed with
  `module 'librosa.beat' has no attribute 'tempo'` on modern librosa. Tempo
  estimation now resolves `librosa.feature.rhythm.tempo` / `librosa.feature.tempo`
  / `librosa.beat.tempo` across versions (tested end-to-end on librosa 1.0.0).

### Known limitations
- Player audio sustains each note until the next onset (legato); a note's own
  duration and rests are not yet honored in playback — visuals are unaffected.
  Honoring true note-offs needs an event-level audio scheduler (roadmap).
- **Chord charts** (`gtrsnipe-chords`). Segments a song into one chord per
  measure (pitch classes unioned across the bar, weighted by duration, with the
  bass note resolving inversions/slash chords) and emits a Markdown/ASCII chord
  sheet: a bar-by-bar progression grid plus an ASCII diagram for each unique
  chord. Diagrams use a compact, playable root-position voicing generated in the
  song's tuning (the lowest tight-span register the mapper can finger), not the
  literal bar contents. Chord naming lives
  in `gtrsnipe.core.chords` (pure pitch-class template matching: triads, power
  chords, 6/7/maj7/m7/m7b5, sus2/sus4, dim/aug/dim7). Extended chords (9/11/13)
  and enharmonic key-aware spelling (sharps only) are deferred.

## [0.3.0] — 2026-09-23

Release plan and design docs live in [`docs/dev/archive/`](docs/dev/archive/RELEASE-PLAN-v0.3.0.md).

### Added
- **Global fretboard optimization.** A dynamic-programming / Viterbi trellis
  mapper replaces the greedy per-chord search, producing globally optimal, more
  playable fingerings. New `--optimizer {viterbi,greedy}` (default `viterbi`);
  the previous greedy behavior remains available via `--optimizer greedy`.
- **Optional-dependency extras** so the base install is torch-free:
  `pip install 'gtrsnipe[audio]'` (librosa bass pipeline),
  `pip install 'gtrsnipe[separation]'` (demucs stem isolation).

### Changed
- **BREAKING (packaging):** audio dependencies are no longer installed by
  default. `pip install gtrsnipe` now installs only the CPU-only MIDI/tab/abc/vex
  core. **If you use audio input, install `pip install 'gtrsnipe[audio]'`**
  (and/or `gtrsnipe[separation]`).
- `requires-python` raised to `>=3.10`. Python **3.10–3.13** are fully supported;
  **3.14** is supported for the core (audio extras are best-effort on 3.14 until
  numba publishes 3.14 wheels — use 3.10–3.13 for the librosa path).
- Fretboard mapper tie-breaking is now deterministic (lexicographically smallest
  fingering); previously it depended on hash/iteration order. Outputs may differ
  from prior versions only on exact score ties. Use `--optimizer greedy` to
  reproduce pre-0.3.0 behavior for one release.

### Removed
- The experimental `basic-pitch` pitch engine, the ONNX distortion-remover
  (`--remove-fx`), and the HiFi-GAN vocoder — with their basic-pitch-only flags
  (`--onset-threshold`, `--frame-threshold`, `--min-note-len-ms`,
  `--melodia-trick`). The librosa engine is the supported audio path.

### Fixed
- Output-corrupting f-string bugs: VexTab title and ABC instrument name emitted
  the literal placeholder text (`{song.title}`, `(track.instrument_name)`)
  instead of the real values.
- Tab out-of-bounds string index: a negative index silently wrote a note onto
  the wrong string; both bounds are now guarded.
- MIDI time-signature denominator: non-power-of-2 signatures (e.g. 4/6) were
  silently truncated to a wrong denominator; they now warn and fall back to 4/4.
- Tab measure sizing now honors the time-signature denominator (correct bar
  lines for 6/8, 3/8, 2/2), matching the ABC generator.
- ABC header validity: the `T:` (title) line now precedes `K:` (which closes the
  header); the instrument name is emitted as a comment rather than an invalid
  body `T:`.
- Capo ordinal suffix (`3rd`/`21st`/`22nd`, not `3th`/`21th`/`22th`).
- Note-name↔pitch round-trip for negative octaves (e.g. `C-1`, MIDI 0).
- Double-quantization on the `--dynamic-quantize` audio path (a second pass
  re-quantized already-quantized events against a grid recomputed from the raw
  input).
- Crash on `--dedupe` (an undefined `_normalize_pitch` helper).
- Removed a stray `DEBUG PARSER` `print()` from the tab parser.

See [`docs/dev/archive/AUDIT-findings.md`](docs/dev/archive/AUDIT-findings.md).

### Known limitations
- **VexTab** does not yet emit hammer-on/pull-off/tap articulation symbols or
  rests for time gaps between notes (the ASCII tab generator does). Tracked for a
  future release.
- **ABC** key signature is always emitted as `K:C` (the `Song` model carries no
  key), and accidentals are spelled as sharps regardless of key.

## [0.2.2] — 2026-09-12

### Fixed
- **Critical:** a stray `exit(1)` (regression from the v0.2.1 refactor) inside the
  non-piano branch of `converter.main()` aborted every guitar/bass conversion
  before any output was written. Guitar/bass `.tab/.abc/.vex/.mid` output works
  again.
- Removed leftover `DEBUG` `print()` statements from `converter.py`.

### Changed
- Declared `mido` as a dependency — it is the primary MIDI parser
  (`formats/mid/reader.py`) and was previously undeclared, so a clean install
  could not import the package.

## [0.2.1]
- Performance fixes; `--constrain-pitch` renamed to `--normalize-pitch`;
  `--pitch-mode` removed (its old `drop` behavior is the default).

## [0.2.0]
- Audio-to-tab pipeline; convert audio/MIDI/text formats into ASCII tablature.

## [0.1.1]
- Convert to/from `.mid`, `.abc`, `.vex`, and `.tab`.
