# Changelog

All notable changes to gtrsnipe are documented here.
This project adheres to [Semantic Versioning](https://semver.org/).

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
    and shows a continuous `bar N beat X.x` readout — so long rests in ensemble
    MIDI keep moving instead of looking like the app hung.

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

Release plan and design docs live in [`docs/dev/`](docs/dev/RELEASE-PLAN-v0.3.0.md).

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

See [`docs/dev/AUDIT-findings.md`](docs/dev/AUDIT-findings.md).

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
