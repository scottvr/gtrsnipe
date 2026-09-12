# gtrsnipe — Release Plan: v0.2.2 hotfix → v0.3.0

_Status: planning. Owner: ScottVR. Drafted 2026-09-12._

This is the master plan for the next release train. It links to four companion
docs in this folder:

- [`AUDIT-findings.md`](./AUDIT-findings.md) — full bug / dead-code inventory.
- [`CPU-DECOUPLING.md`](./CPU-DECOUPLING.md) — making the tool installable & runnable torch-free.
- [`DESIGN-viterbi-mapper.md`](./DESIGN-viterbi-mapper.md) — the "elegant" fretboard-mapper redesign.
- [`TEST-PLAN.md`](./TEST-PLAN.md) — regression suite, fixtures, and CI matrix.

---

## 1. Why this release

Two problems motivated this work:

1. **CPU-only usability.** The tool was built and tuned on one GPU laptop. On a
   plain machine (e.g. an x86 MacBook Air on Python 3.14 that *cannot* install
   PyTorch), `pip install gtrsnipe` is unresolvable because heavy ML packages
   (`demucs`→torch, `basic-pitch`→tensorflow/onnx, `librosa`→numba) sit in the
   base dependency list. The core value — MIDI/tab/abc/vex conversion and the
   settled-on **librosa bass** audio path — needs none of that.

2. **The fretboard mapper's combinatorial explosion.** The mapper enumerates
   `itertools.product(*note_positions)` per chord and then makes a **greedy**,
   locally-optimal choice per time-step. The "elegant math" that fixes this is
   **dynamic programming / the Viterbi algorithm over a trellis** — the same
   family as an HMM decode (named for **Andrey Markov**, the Russian
   mathematician; Viterbi decoding is the shortest-path DP over that chain).
   It turns the exponential *sequence* search into a polynomial, globally
   optimal one. See [`DESIGN-viterbi-mapper.md`](./DESIGN-viterbi-mapper.md).

Along the way an audit (see [`AUDIT-findings.md`](./AUDIT-findings.md)) found
that **`main` is currently broken for its primary use case** and shipped a
handful of output-corrupting bugs.

## 2. Decisions locked for this release

| # | Decision | Rationale |
|---|----------|-----------|
| D1 | **Ship a v0.2.2 hotfix first, then v0.3.0 for features.** | `main` is broken today; users deserve a working tool immediately, and it keeps history clean. |
| D2 | **Prune the weak/experimental ML: remove `basic-pitch`, the ONNX distortion-remover, and the HiFi-GAN vocoder. Keep `demucs` as an optional `[separation]` extra alongside the librosa `[audio]` path.** | basic-pitch underperformed; the onnx/vocoder paths are undocumented experiments that ship broken. Less surface, fewer heavy deps. |
| D3 | **Viterbi is the default optimizer; the current greedy stays reachable via `--optimizer greedy`.** | Global optimum by default, but existing tunings / saved outputs remain reproducible for one release. |
| D4 | **Officially support Python 3.10–3.13; best-effort 3.14. The torch-free core stays 3.14-clean.** | numba/llvmlite have no cp314 wheels yet (librosa would compile llvmlite from source on 3.14). Core (MIDI/tab/abc/vex) is verified working on 3.14. |

## 3. Release train

### v0.2.2 — "unbreak main" hotfix  ✅ DONE (branch `hotfix/v0.2.2`)

Scope was deliberately minimal (see [`AUDIT-findings.md`](./AUDIT-findings.md) #1, #11, Finding C):

- Removed the stray `exit(1)` (`converter.py:599`) that made the guitar/bass
  output loop dead code. **Verified end-to-end**: the CLI now writes tab where
  before it silently produced nothing.
- Removed four leftover `DEBUG` `print()`s.
- Declared **`mido`** (imported by `formats/mid/reader.py`, previously
  undeclared). Deliberately did **not** add `py-midi`: the fallback parser uses
  the `MIDIFile` package's uppercase `MIDI` module (already declared), and
  py-midi's lowercase `midi` collides with it on case-insensitive filesystems.
- Bumped version `0.2.1 → 0.2.2`.

> **Recommended follow-up for the hotfix (optional, one-liners):** two other
> output-corrupting bugs are the same class as the `exit(1)` regression and could
> be cherry-picked into a `v0.2.2.x`: the VexTab title f-string
> (`vex/generator.py:27`) and the ABC instrument-name f-string
> (`abc/generator.py:72`). They are currently slotted into v0.3.0 Sprint 1
> (`fix/output-correctness`) to respect the agreed hotfix scope.

### v0.3.0 — CPU-only core + Viterbi mapper (integration branch `release/v0.3.0`)

Four epics, described below and detailed in the companion docs.

## 4. Epics

### Epic A — CPU-only decoupling & experimental-ML prune  (`feat/cpu-core-decouple`)
Make `pip install gtrsnipe` resolvable and runnable torch-free on 3.10–3.14.
Split deps into a light core + `[audio]`/`[separation]` extras, make `librosa`
and the audio submodules lazy, add friendly "install the extra" messaging,
prune basic-pitch/onnx/vocoder, and fix `requires-python`. Full spec:
[`CPU-DECOUPLING.md`](./CPU-DECOUPLING.md).

### Epic B — Viterbi/DP fretboard mapper  (`feat/viterbi-mapper`)
Replace greedy per-step selection with a global trellis DP. Enumerate **all**
valid (distinct-string) fingerings per chord — bounded, so no lossy beam — and
run first-order Viterbi by default, exact second-order (pair-state) only when
`let_ring_bonus>0 AND diagonal_span_penalty`. Reuse `_score_fingering` verbatim.
Add `--optimizer {viterbi,greedy}` (default `viterbi`). Full spec:
[`DESIGN-viterbi-mapper.md`](./DESIGN-viterbi-mapper.md).

### Epic C — Output-correctness bugs & dead-code  (`fix/output-correctness`)
Fix the f-string/template bugs that emit literal placeholder text, the ABC
key/measure fidelity issues, the tab out-of-bounds silent note, the MIDI
time-signature denominator, the VexTab legato drop, and strip ~100 lines of
dead/commented code. Full inventory: [`AUDIT-findings.md`](./AUDIT-findings.md).

### Epic D — Regression suite & CI  (`test/regression-suite`)
Tiered unit + golden + packaging tests, fixtures sourced from the wiki
examples, and a CI matrix. Includes the highest-value decoupling guard: a test
asserting `torch`/`numba`/`tensorflow` never enter `sys.modules` on a core run.
Full spec: [`TEST-PLAN.md`](./TEST-PLAN.md).

## 5. Branches

```
main
└─ hotfix/v0.2.2                 ✅ committed (the unbreak-main fix)
   └─ release/v0.3.0             integration branch (built on the hotfix)
      ├─ feat/cpu-core-decouple  Epic A
      ├─ feat/viterbi-mapper     Epic B
      ├─ fix/output-correctness  Epic C
      └─ test/regression-suite   Epic D
```

Nothing has been pushed to `origin` yet — awaiting go-ahead.

## 6. Sprint slicing

- **Sprint 1 — "correct & installable" (ships a genuinely usable core).**
  Epic A (decouple + prune + declare deps) + Epic C release-blockers (f-string
  bugs, tab OOB, debug prints) + start Epic D (unit tier + the `sys.modules`
  import guard + packaging test). Merge to `release/v0.3.0`.
- **Sprint 2 — "fidelity & the mapper."** Epic B (Viterbi) + remaining Epic C
  (ABC key/measure, MIDI time-sig, VexTab legato, dead-code) + finish Epic D
  unit/golden tiers. **Re-bless golden files in two steps** (bug-fixes-only
  under greedy first, then again after Viterbi) so the two changes are validated
  independently (Risk R1).
- **Sprint 3 — "polish & release."** Docs/README refresh, CHANGELOG + migration
  note, `--optimizer` documentation, tag `v0.3.0`.

## 7. Risk register

| ID | Risk | Likelihood | Impact | Mitigation |
|----|------|-----------|--------|------------|
| R1 | Golden files re-blessed carelessly after the mapper swap mask a real regression | Med | High | Bless in two steps (bug-fixes-only greedy → Viterbi), human-diff-review each. |
| R2 | py3.14 lacks wheels for core deps (`numpy>=2.1`, `mido`, `MIDIFile`) on the Air | Low | High | Verified `mido`/`MIDIFile`/`midiutil`/`numpy 2.5.2` install and the core runs on the actual 3.14 Air. Pin known-good floors. |
| R3 | `[audio]` (librosa→numba) uninstallable on py3.14 | High (on 3.14) | Med | Documented: core gives MIDI/tab/abc/vex on 3.14; the librosa bass path needs a Python with numba wheels (3.10–3.13). Not a core regression. |
| R4 | Viterbi traceback / determinism bug ships | Med | High | Dedicated multi-stage-trellis traceback test + real-tie determinism test (see design §Corrections). |
| R5 | Beam pruning silently drops the transition-optimal fingering | **Eliminated** | — | Design enumerates **all** distinct-string fingerings (bounded ≤720/chord); no lossy beam in the normal case. `hard_enum_cap` is a pathological safety valve that logs when it triggers. |
| R6 | The dep-split is itself a **breaking change** — existing `pip install gtrsnipe` audio users lose deps on upgrade | High | Med | Minor-version bump (0.3.0) + CHANGELOG migration note ("audio users: `pip install 'gtrsnipe[audio]'`"). |
| R7 | Determinism change alters long-standing outputs on exact ties | Low | Low | Documented as intentional stable behavior; `--optimizer greedy` reproduces old behavior for one release. |
| R8 | `requires-python=">=3.8"` contradicts `numpy>=2.1` (needs ≥3.10) | — | Med | Set `requires-python=">=3.10"` in the pyproject work (Epic A). |
| R9 | `_require_extra` raising `SystemExit` kills library consumers | Low | Med | CLI path exits cleanly; library path raises `ImportError` with the same hint (see CPU-DECOUPLING §Graceful degradation). |

## 8. Open questions for the maintainer

1. **Fixtures.** The repo ships zero sample files. The wiki examples (Mr Crowley,
   Bach Cello Prelude, Asturias, Barney Miller) need MIDI/audio committed under
   `tests/fixtures/`. Bach/Albéniz are public-domain; the Barney Miller audio is
   copyright-sensitive — gate behind an env-var path or commit only a short clip
   if licensing permits. See [`TEST-PLAN.md`](./TEST-PLAN.md).
2. **`what_a_pitch.py` / `toy_polyphonic_pitch_detector.py`.** These look like
   scratch/experimental scripts. Confirm they can be deleted with the ML prune.
3. **MIDI-package namespace.** You noted intentionally "trampling one midi
   package's namespace." No `sys.modules` shim exists in code — it appears to be
   the benign `midiutil.MIDIFile`-vs-`MIDI.MIDIFile` aliasing. Confirm before any
   import refactor touches `reader.py`.
