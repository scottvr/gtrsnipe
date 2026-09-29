# Unified I/O — Renderer × Sink × Schedule (TTY = pager + transport)

*Status: implemented in v0.5.0 (branch `refactor/unified-io`). Since then: playback
stops each note at its own end (v0.6.8, P01), and the audio instrument defaults to
the MIDI file's own program (v0.6.9, P03).*

## Why

Three console tools (`gtrsnipe` convert, `gtrsnipe-play`, `gtrsnipe-chords`) each
had their own argparse. That meant (1) shared flags declared 3× and `MapperConfig`
built 3×, and (2) the player/chords exposed only ~6 of the converter's 33 mapper
knobs — no frequency range, transpose, normalize, or audio input either.

The unifying idea: **the player is not a different kind of thing from a file
output — it is a time-modulated write to a filehandle (stdout).** So every output
is one abstraction:

> **output = (renderer, sink, schedule)** — *what* bytes, *where*, *when*.

The control channel a plain write lacks (keys) is not a design problem but an
**unimplemented convention**: an interactive streaming TTY program is a **pager**
(`less`) plus, because our content moves in time, a **media transport** (mpv).

## Model

| capability            | renderer         | sink              | schedule    |
|-----------------------|------------------|-------------------|-------------|
| `-o x.tab/.mid/.abc/.vex` | existing generators | file          | instant     |
| `-o x.chords.md`      | chord chart      | file / stdout     | instant     |
| `--play` fretboard/tab| `render_at(t)`   | TTY (curses)      | transport   |
| `--audio`             | note-on at onset, note-off at the note's end | MIDI port / synth (program and channel from the MIDI file unless `--instrument`) | transport   |

- **Renderer** (visual): `render_at(timeline, beat_time) -> str`. Whole-document
  generators keep `generate(song)` unchanged (byte-identical output — a hard
  constraint; mapping was NOT hoisted out of them).
- **Sink**: `setup/write/read_key(blocking)/teardown`. `PlainSink` (stream +
  terminal/scripted keys), `CursesSink` (alt screen, non-blocking poll, resize,
  restore — only built in `main()` on a real TTY), `AudioSink` (non-visual).
- **Frames** (`frame.py`, built by `timeline.py`): one per onset, with its
  pitches and, aligned with them, each note's own end (`ends`). A held note rings
  past later onsets; a rest is silent. With `--legato` every end is the next
  onset (the pre-0.6.8 playback).
- **Transport** (`transport.py`): event-driven loop that advances to
  `min(next onset, next release, next redraw, end)`. Audio fires at **true onset
  times** (not fps-quantized); rendering throttles to `--fps`; wall-clock
  **anchored** via an injected monotonic `now` (no drift). Replaces the three
  Clock classes. `step` vs `tempo` = initial paused/playing state; metronome = a
  re-timed timeline (`metronome_timeline`).
- **Releases**: each fired note's end goes on a heap of (beat, pitch,
  generation). Re-striking a pitch bumps its generation, so the earlier note's
  release is skipped and can't cut the new note short. Pause, seek and step
  silence everything and clear the heap.
- **Driver** (`app._Driver`): binds renderer + sink + audio to the Transport's
  `render/fire/release/silence/read_key/show` callbacks; keeps the loop testable
  with an injected clock + scripted keys. When the frames carry ends, `fire`
  *strikes* the new notes and leaves the others ringing until `release`; frames
  without ends fall back to *attack*, which stops every ringing note first.

## Keys (pager ∪ media-transport convention)

`space` (or `enter`, `p`) pause/resume · `. ,` step fwd/back (while paused) ·
`← →` seek ±1 bar · `[ ]` tempo ∓ · `g`/`home`, `end` jump start/end · `h`/`?`
help (pauses; `space` resumes) · `q` quit. There are no paging keys yet, so
`space` has no page-down meaning to collide with; pager search (`/`) and
`:goto` are backlog P04.

## Shared arg layer (`arguments.py`)

- **Option groups:** `add_tuning_args`, `add_mapper_args`, `add_player_args`,
  `add_tab_input_args` (`--sustain`), `add_chart_args`.
- **Profiles:** `add_profile_args` declares `--profile`, `--no-defaults`,
  `--config-dir` and `--save-args`; `apply_profiles(parser, argv)` replaces
  `parse_args`, prepending the options saved in the `defaults` profile and any
  `--profile`.
- **Tunings:** `resolve_custom_tuning` (`--tuning-pitches`, `--drop-low-string`),
  `open_string_pitches_for` (decodes a `.tab` in its real tuning),
  `resolve_named_tuning`, `resolve_num_strings`.
- **Config:** `build_mapper_config(args, *, tuning, num_strings)`, the one
  `MapperConfig` builder; a custom tuning overrides the `tuning` and
  `num_strings` passed in.

The converter, `gtrsnipe-play`, and `gtrsnipe-chords` all compose them → every option
reaches every mode, defined once. (`--play` options and `--sustain` go to the
converter and `gtrsnipe-play`; chart options to the converter and
`gtrsnipe-chords`.)

## CLI

Flat `gtrsnipe -i … -o …` unchanged (byte-identical). Additions: `-o x.chords.md`
(chord sheet output format), `--play [--view tab] [--audio …]` (interactive; `-o`
optional). `gtrsnipe-play`/`gtrsnipe-chords` remain as curated convenience stubs
sharing the same engine: `gtrsnipe-play` calls `run_player` directly, and
`gtrsnipe --play` goes through `run_player_from_args`; `gtrsnipe-chords` and
`-o x.chords.md` both call `build_chord_sheet`.

## Notes / deferred

- **Done in v0.6.8 (P01):** true note lengths and rests, as note-offs queued at
  each note's end. `--legato` restores the old sustain-to-next-onset playback, and
  `--sustain string` lets notes read from a tab ring until their own string is
  struck again (at most one bar).
- **Done in v0.6.7:** playability-based `--analyze` (F03).
- **Open** (in [`BACKLOG.md`](../dev/BACKLOG.md)): `--name-chords` (C01),
  `--prefer-open-chords` (C02), shape-relative chord names (C03), pager search `/`
  and `:goto` (P04).
- Windows needs `windows-curses`; PlainSink is the fallback everywhere. Documenting
  or declaring it is P06.
