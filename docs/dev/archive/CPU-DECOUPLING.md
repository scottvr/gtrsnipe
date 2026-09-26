# CPU-Only Decoupling & Experimental-ML Prune

_Epic A of v0.3.0. Branch `feat/cpu-core-decouple`. Implements decisions D2
(prune weak ML) and D4 (Python target)._

## Goal

`pip install gtrsnipe` resolves and runs **torch-free** on Python 3.10–3.14, so
a plain machine that cannot install PyTorch still gets the full MIDI/tab/abc/vex
pipeline. Audio features live behind opt-in extras.

**Verified already** on the target x86 MacBook Air (Python 3.14): the core stack
(`mido` + `MIDIFile` + `midiutil` + `numpy 2.5.2`) installs cleanly, and a
generated MIDI → `MidiReader` → `AsciiTabGenerator` renders correct tab with
**zero** heavy modules in `sys.modules`. The only things blocking a real install
today are (a) the packaging (heavy deps in the base list) and (b) the top-level
`import librosa` in `converter.py`.

## 1. Dependency layout

### Core (base install — must stay torch/tensorflow/numba-free)
```
midiutil, mido>=1.3, MIDIFile, numpy>=2.1
```
- `MIDIFile` (PyPI) supplies the uppercase `MIDI` module used by
  `from MIDI import MIDIFile, Events` — **verified** (`pip install MIDIFile` →
  `MIDI/Events/...`). It is already declared; keep it. Do **not** add `py-midi`
  (its lowercase `midi` collides with `MIDI` on case-insensitive filesystems).
- `mido` and `numpy` were undeclared (only transitively present via librosa/demucs);
  declare them explicitly. (`mido` already added in the v0.2.2 hotfix.)

### Extras (post-prune — D2)
```toml
[project.optional-dependencies]
audio      = ["librosa>=0.10", "soundfile", "scipy", "noisereduce"]  # the settled-on librosa/pYIN bass path
separation = ["demucs"]                                              # optional stem isolation (pulls torch)
all        = ["gtrsnipe[audio]", "gtrsnipe[separation]"]
```
**Removed entirely (D2):** the `basicpitch` extra (`basic-pitch` → tensorflow/
tflite/onnx/coremltools) and the `fx` extra (`torch`, `torchaudio`,
`onnxruntime`, `matplotlib` for the distortion-remover + HiFi-GAN vocoder).

### `requires-python`
Change `">=3.8"` → **`">=3.10"`** (numpy≥2.1 requires ≥3.10; also matches D4).
This resolves a real metadata contradiction.

## 2. Prune list (delete)

| Path | Why |
|------|-----|
| `gtrsnipe/audio/pitch_detector_bp.py` | basic-pitch engine (underperformed; pulls TF/ONNX). |
| `gtrsnipe/audio/distortion_remover.py` | experimental ONNX/torch `--remove-fx`. |
| `gtrsnipe/audio/vocoder.py` | HiFi-GAN vocoder (torch). |
| `gtrsnipe/audio/models/hifi_GAN/**` (whole dir) | vendored HiFi-GAN model + `matplotlib` use. |
| `gtrsnipe/audio/what_a_pitch.py`, `toy_polyphonic_pitch_detector.py` | scratch/experimental scripts (confirm with maintainer). |

**CLI surface to remove** (`arguments.py`): `--remove-fx`, `--onset-threshold`,
`--frame-threshold`, `--min-note-len-ms`, `--melodia-trick`, and the
`--pitch-engine` choice `basic-pitch` (librosa becomes the only engine — either
drop `--pitch-engine` or leave it accepting only `librosa`). **Keep**
`--stem-track` / `--demucs-model` (demucs `[separation]`).

**`converter.py`**: delete the `basic-pitch` and `--remove-fx` branches in the
audio pipeline block.

## 3. Lazy-import edits (`converter.py` unless noted)

1. **Delete the top-level `import librosa` (line 19).** It is only used inside
   `dynamic_quantize_song()` and the `if args.dynamic_quantize and is_audio_input:`
   block (+ the `librosa.note_to_hz` fallbacks). Import it *locally* there,
   guarded (see §4). This single change is what makes `import gtrsnipe.converter`
   work on a torch-free box.
2. **Critical — stop the eager demucs→torch pull-in.** In the `if is_audio_input:`
   block (lines 369-371) the imports of `separator`, `cleaner`, and
   `distortion_remover` load *unconditionally* for any audio input — dragging in
   demucs→torch even on the librosa-only bass path. Move each to its point of use:
   `separator` → inside `if args.stem_track:`; `cleaner` → inside the low-pass /
   `if args.nr:` branches. (`distortion_remover` is deleted with the fx prune.)
3. **Wrap** each moved/lazy audio import and the librosa pitch-engine import in
   `try/except ImportError` routed through `_require_extra(...)` (§4).
4. **`audio/__init__.py`** stays empty, so `from .audio.dynamic_tempo import
   analyze_dynamic_tempo` (converter line 9) triggers no sibling audio imports —
   `dynamic_tempo` needs only numpy. **Audit it explicitly** (it is the one
   always-imported audio module) to confirm numpy-only.
5. **`formats/mid/reader.py`**: no code move — `import mido` / `from MIDI import …`
   are light pure-Python and stay top-level; both are core deps. Leave the
   `MIDIFile`-vs-`midiutil` aliasing alone (the maintainer's intentional
   namespace handling).

## 4. Graceful degradation

Add a helper used by every lazy audio import's `except ImportError`:

```python
def _require_extra(extra: str, feature: str, *, cli: bool):
    msg = (f"Feature {feature!r} needs optional dependencies that aren't installed.\n"
           f"  Install them with:  pip install 'gtrsnipe[{extra}]'")
    if cli:
        logger.error(msg)
        raise SystemExit(1)          # clean exit, no traceback, for the CLI
    raise ImportError(msg)           # library callers get an exception, not a killed process
```

- **CLI vs. library (critic catch R9):** `main()` calls with `cli=True` (clean
  `SystemExit`); anything importable as a library re-raises `ImportError` so a
  consumer's process isn't killed.
- **Mapping:** librosa/pYIN pitch + dynamic-quantize + cleaner → `[audio]`;
  `--stem-track`/demucs → `[separation]`. A core-only install running
  MIDI/tab/abc/vex never reaches an `except` branch; an audio user on a torch-free
  box sees `pip install 'gtrsnipe[audio]'` instead of a raw `ModuleNotFoundError`.

## 5. Python 3.14 reality (D4)

- **Core**: verified working on 3.14 — always installable/runnable.
- **`[audio]`**: librosa → numba → llvmlite, which has **no cp314 wheel** yet (on
  3.14, `pip` fetches the `llvmlite` *source tarball* and would compile it). So
  `pip install 'gtrsnipe[audio]'` is **best-effort on 3.14**; use Python 3.10–3.13
  (a pyenv/conda venv) for the librosa bass pipeline until numba ships 3.14
  wheels. Check `pip index versions numba llvmlite` first.
- **`[separation]`**: torch has no cp314 x86-mac wheel → 3.10–3.13 only.
- **Do NOT fold librosa into core** to "simplify" — that reintroduces the numba
  wall for every user, defeating the whole split.

> **Explicit resolution of the "settled-on path may be uninstallable" tension:**
> On the 3.14 Air, the *core* MIDI/tab/abc/vex workflows work fully; the librosa
> *audio* transcription needs a 3.10–3.13 environment. That's an accepted,
> documented trade-off, not a core regression — the primary new goal (CPU
> MIDI→tab) is met on 3.14.

## 6. Acceptance criteria

1. Fresh venv, `pip install .` (core only) succeeds on Python 3.14 x86 — no
   torch/tensorflow/numba/demucs/basic-pitch/scipy in the resolution.
2. `python -c "import gtrsnipe.converter"` succeeds with zero heavy deps
   (regression guard for the removed top-level `import librosa`).
3. `python -c "from gtrsnipe.formats import abc, mid, tab, vex"` succeeds core-only.
4. After a MIDI→tab run, **none** of `{torch, torchaudio, tensorflow, librosa,
   numba, demucs, basic_pitch, onnxruntime, scipy}` is in `sys.modules`
   (the single highest-value guard — see [`TEST-PLAN.md`](./TEST-PLAN.md)).
5. Core-only, an audio input exits code 1 with the correct `pip install
   'gtrsnipe[...]'` hint (per feature) — no traceback.
6. `pip install '.[audio]'` on a numba-capable Python runs `song.wav → out.tab`
   via the librosa path **without** importing torch.

## 7. Migration note (breaking change — R6)

Moving librosa/soundfile/scipy/noisereduce/demucs out of the base set is a
**breaking change** for existing audio users on upgrade. Ship in **v0.3.0** with
a CHANGELOG entry: _"Audio features are now optional extras. If you use audio
input, install `pip install 'gtrsnipe[audio]'` (librosa bass path) and/or
`gtrsnipe[separation]` (demucs). basic-pitch and the experimental fx/vocoder
paths have been removed."_
