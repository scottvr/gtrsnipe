# Changelog

All notable changes to gtrsnipe are documented here.
This project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased] — v0.3.0 (planned)

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
- Output-corrupting f-string bugs (VexTab title, ABC instrument name), ABC key /
  measure fidelity, tab out-of-bounds silent note, MIDI time-signature
  denominator, VexTab legato-chain note dropping, capo ordinal suffix. See
  [`docs/dev/AUDIT-findings.md`](docs/dev/AUDIT-findings.md).

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
