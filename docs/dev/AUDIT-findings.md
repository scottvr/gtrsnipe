# Audit Findings — Bug & Dead-Code Inventory

_Produced by a multi-agent code audit (subsystem readers + adversarial
verification), 2026-09-12. Severity is from the user-facing symptom on the
primary CPU workflows. "Status" tracks the v0.2.2 hotfix vs. pending v0.3.0 work._

## Release-blocking / correctness bugs

| # | Sev | File:line | Defect | Fix | Status |
|---|-----|-----------|--------|-----|--------|
| 1 | **Critical** | `converter.py:599` | Stray `exit(1)` inside `if not is_piano_mode:` → the output loop is **dead code** for guitar/bass; no `.tab/.abc/.vex/.mid` is written. | Remove it; control falls through to output generation. | ✅ **fixed in v0.2.2** |
| 2 | **Critical** | `vex/generator.py:27` | Plain string `"text Title: {song.title}"` missing the `f` prefix → VexTab output contains literal `{song.title}`. | Add `f` prefix; confirm `text Title:` is valid VexTab. | ⏳ `fix/output-correctness` |
| 3 | **Critical** | `abc/generator.py:72` | Literal `'(track.instrument_name)'` instead of the variable → every non-piano track's `T:` line emits literal `(track.instrument_name)`. | Interpolate the variable. | ⏳ `fix/output-correctness` |
| 11 | Cleanup | `converter.py` (×4), `tab/parser.py:88` | Leftover `DEBUG` `print()`s on stdout. | Delete; assert `capsys` empty in tests. | ✅ converter prints fixed in v0.2.2; `tab/parser.py:88` ⏳ |
| C | High | `pyproject.toml` | `mido` imported by `mid/reader.py` but undeclared; `numpy` only present transitively. | Declare `mido` (done) and `numpy>=2.1` (Epic A). | ✅ `mido` in v0.2.2; `numpy` ⏳ Epic A |

## Fidelity bugs (v0.3.0 `fix/output-correctness`)

| # | Sev | File:line | Defect | Fix |
|---|-----|-----------|--------|-----|
| 7 | Med | `abc/generator.py:61,72` | `T:` emitted **after** `K:C` (inside tune body; strict parsers may ignore). Hardcoded `K:C` + sharps-only `_midi_pitch_to_abc` → key always misrepresented as C major. | Move `T:` before `K:`; derive key from source; support flats. |
| 8 | Med | `abc/generator.py:99-111` | `beats_in_current_measure` advanced by *quantized* duration while `current_beat` uses *raw* duration → bar-line drift / spurious/omitted rests. | Use one consistent (quantized) counter. |
| 9 | Med | `tab/parser.py:166-168` | `_tab_pos_to_midi` returns `0` (≈ C-1) on out-of-bounds `string_idx` → silent spurious low note. | Return `None`/raise + bounds guard; skip. |
| 10 | Med | `vex/parser.py:53,75-97` | Legato subdivision regex only matches the single explicit `/string`, so intermediate hammer/pull notes (e.g. `:16 5h7p5/3`) are **silently dropped**. | Parse legato chains; expand intermediate frets; subdivide duration. |
| 13 | Med | `mid/generator.py:37` | `den_power_of_2 = int(math.log2(den))` truncates for non-power-of-2 denominators → wrong MIDI time-sig denominator. | Validate power-of-two or map explicitly. |
| 12 | Low | `tab/generator/ascii.py:256-259` | Capo ordinal only handles 1st/2nd → "3th Fret", "21th Fret". | Correct st/nd/rd/th logic. |
| ABC-parser | Low | `abc/parser.py:14,24-33` | Header regex runs over the whole string (body lines starting `X:` misparsed); `M:`/`L:` order-dependence. | Scope header scan; make `L:` authoritative. |
| VEX-dur | Low | `vex/parser.py:14` | Unknown duration token silently becomes a quarter note (no warning). | Warn on unrecognized token. |

## Removed with the ML prune (D2) — no fix needed

`audio/pitch_detector_bp.py`, `audio/distortion_remover.py`, `audio/vocoder.py`,
`audio/models/hifi_GAN/**` (incl. `hifigan_inference.py`, `utils.py` matplotlib
use, hardcoded paths), and the `--remove-fx`/basic-pitch CLI surface. These were
flagged with `bug`/`hardcoded-path` and "ships broken"; deletion resolves them.
Confirm `what_a_pitch.py` and `toy_polyphonic_pitch_detector.py` (scratch scripts)
can go too.

## Dead code to strip (`fix/output-correctness`)

- `vex/parser.py:105-190` — ~85-line commented-out alternate `VextabParser` class.
- `tab/generator/pdf.py` — empty `PdfTabGenerator` stub + its re-export (implement or remove).
- `tab/generator/ascii.py` — dead `last_event_time_for_calc` (l.133), unused
  `_is_chord_playable` (l.196-220), unused `default_note_length` param + dead block (l.43-48).
- `mid/generator.py` — unused imports; stale "Pass 1/Pass 3" comments in `tab/parser.py`.
- `converter.py` — the duplicate intermediate-MIDI-path computation (two identical
  blocks around lines 381-390 and 407-417) and the unreachable code after the first
  `return` in `dynamic_quantize_song` (lines 162-166).

## Dev tool

- `tools/debug_generator.py` — two `bug` flags; broken roundtrip tool. Fix or
  exclude from release (superseded by `test_abc_roundtrip`).

## Notes carried forward from the audit

- Several source blocks were truncated during synthesis; before closing each
  sprint, re-run a fresh full-tree import scan and re-confirm the `missing_deps`
  list (Risk R5).
- Bug #1's role in the failing Asturias golden is **assumed**, not proven end-to-end
  against the original golden (source truncated). The v0.2.2 fix was verified to
  restore output on a synthetic MIDI; confirm against the real fixture when it lands.
