# Test & Regression Plan

_Epic D of v0.3.0. Branch `test/regression-suite`. Gates the release._

The repo currently ships **zero** tests and **zero** sample files. This plan
builds a tiered `pytest` suite whose core tiers run **torch-free** so CI can gate
on a plain machine.

## 1. Fixtures (`tests/fixtures/`, `tests/golden/`)

| Fixture | Source | Notes |
|---------|--------|-------|
| `hand/scale.mid` | authored in-repo | C-major scale C4..C5, 8 notes, 4/4. Generate deterministically via `MidiGenerator`. |
| `hand/tiny.abc`, `hand/tiny.vex`, `hand/tiny.tab` | authored in-repo | headers + a few notes, one chord, one rest — for parser/generator/round-trip units. |
| `midi/mr_crowley.mid` | wiki example 2 | multi-track; organ intro on **track 5** (`--track 5`). Must be sourced & committed. |
| `midi/bach_cello_suite1_prelude.mid` | wiki example 3 | public-domain (Bach). |
| `midi/asturias-leyenda.mid` | wiki example 4 | public-domain (Albéniz); golden case study. |
| `audio/barney_miller_theme.(wav\|mp3)` | wiki "Barney Miller" | **copyright-sensitive** — commit a short clip only if licensing permits, else gate behind `GTRSNIPE_AUDIO_FIXTURE` env path and skip when absent. |
| `golden/*.tab` | captured once from a **fixed** build | Capture **after** the v0.2.2 `exit(1)` fix; normalize out the `// Transcribed with:` header (it embeds absolute paths). |

`tests/conftest.py`: a golden-comparison normalizer (strips/normalizes the
`// Transcribed with:` line) and `importorskip` guards for `librosa`/`soundfile`
and `demucs`/`torch`.

## 2. Unit tier — torch-free, runs on the core install

- `test_theory` — `note_name_to_pitch('E2')==40, ('A4')==69, ('Eb2')==39`;
  `pitch_to_note_name(60)=='C4'`; identity round-trip 21..108; `midi_to_hz(69)≈440`.
- `test_abc_parser` / `test_abc_generator` / `test_abc_roundtrip` — headers,
  note/chord/rest handling; **generator test guards bug #3** (instrument literal);
  round-trip guards #7/#8.
- `test_vex_parser` / `test_vex_generator` — duration & fret/string tokens;
  **generator test guards bug #2** (title literal); extend parser test to cover the
  **legato-drop bug #10**.
- `test_tab_parser` — rhythm-from-spacing, staccato on/off; **assert `capsys`
  empty** (guards debug prints #11).
- `test_ascii_generator` — 6 rows e/B/G/D/A/E, frets in `[0,max_fret]`,
  `max_line_width` wrapping, `// Transcribed with:` header carries `command_line`,
  **capo ordinal correct (guards #12: "3rd"/"21st")**.
- `test_midi_reader::test_scale_counts` — `scale.mid` → 8 ascending C4..C5, times
  monotonic, durations>0.
- `test_midi_reader::test_track_select` — `mr_crowley.mid` `track=5` yields only
  organ events; `None` yields strictly more (validates `--track 5`).
- `test_midi_generator` — generate→write→re-parse recovers pitch set + tempo +
  time-sig; **include a non-power-of-2 denominator case (guards #13)**.
- `test_io` — `save_text_file`/`save_midi_file`/`read_text_file` behavior (guards audit #4).

## 3. Mapper tier (new — Epic B)

- `test_viterbi_traceback` — hand-built ≥3-stage trellis with a tie; assert the
  recovered path indices are correct (guards the traceback correction).
- `test_viterbi_determinism` — construct an exact score tie; assert the
  lexicographically-smallest fingering is chosen, stable across runs.
- `test_viterbi_ge_greedy` — on a small corpus, assert `J(viterbi) >= J(greedy)`
  for every track (holds because no lossy beam).
- `test_second_order_equivalence` — a `let_ring_bonus>0 + diagonal_span_penalty`
  input: assert the pair-state (`O(K³)`) result matches the intended second-order
  optimum, and that the first-order collapse is **not** used for that config.
- `test_scorer_history_guard` — the landmine guard: fails if `_score_fingering`
  gains a reference deeper than `prev_prev`.
- `test_dead_end_group` — a group with an unmappable pitch is dropped, context
  doesn't advance, surrounding groups still map (parity with greedy).

## 4. Golden tier

- `golden_asturias_final` — full CLI with the case-study flags
  (`--let-ring-bonus … --diagonal-span-penalty --prefer-open …`); after header
  normalization, byte-identical to `golden/asturias.leyenda.golden.tab`.
- `golden_mr_crowley_track5`, `golden_bach_prelude` — default-weights MIDI→tab baselines.

**Two-step blessing (Risk R1):** capture goldens first with **bug-fixes-only under
greedy** (`--optimizer greedy`), commit & review; then regenerate under the default
Viterbi and human-diff-review the delta separately. Keep the greedy-baseline golden
as a distinct check so the two changes are validated independently.

## 5. Packaging / isolation tier — the highest-value guards

- `test_core_install_resolves` — fresh venv, `pip install .` (core only) resolves
  on 3.14 with no torch/tensorflow/numba/demucs/basic-pitch/scipy.
- `test_no_heavy_imports` — **the key guard:** `import gtrsnipe.converter; assert
  not ({'torch','torchaudio','tensorflow','librosa','numba','demucs','basic_pitch',
  'onnxruntime','scipy'} & set(sys.modules))`. Run on a **supported** CPython too,
  so the guarantee is enforced even if the 3.14 job is flaky.
- `test_require_extra_hints` — core-only, each audio trigger exits cleanly with the
  correct hint: audio input → `gtrsnipe[audio]`; `--stem-track` → `gtrsnipe[separation]`.
  One case per extra; assert `SystemExit(1)` + no traceback (CLI) and `ImportError`
  (library call).

## 6. Integration tier

- MIDI↔ABC and MIDI↔tab round-trips, multi-output (`-o a.mid -o b.tab`) in one run.
- `integration_audio_librosa_bass` — Barney Miller librosa bass path
  (`--pitch-engine librosa --bass`); `importorskip('librosa','soundfile')`.
- `integration_audio_demucs_stem` — `--stem-track bass` then librosa;
  `importorskip('demucs')`; **allow-failure** job.

## 7. CI matrix (D4)

- **Job 1 — core (required, fast):** Python **3.10, 3.11, 3.12, 3.13, 3.14** ×
  core install. Runs unit + mapper + golden + packaging tiers. Fails on any stray
  DEBUG stdout. Includes `test_no_heavy_imports`. This is the merge gate.
- **Job 2 — audio (required):** Python **3.11–3.13** × `.[audio]`. Integration
  round-trips + librosa bass path. (3.14 excluded until numba ships wheels — R3.)
- **Job 3 — separation (allow-failure, non-blocking):** Python 3.11/3.12 ×
  `.[audio,separation]`. demucs path behind `importorskip`; cache model weights;
  `continue-on-error`.

No `basicpitch`/`fx` jobs — those paths are removed (D2).
