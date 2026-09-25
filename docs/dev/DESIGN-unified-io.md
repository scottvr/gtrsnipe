# Unified I/O — Renderer × Sink × Schedule (TTY = pager + transport)

*Status: implemented in v0.5.0 (branch `refactor/unified-io`).*

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
| `--audio`             | onset → notes    | MIDI port / synth | transport   |

- **Renderer** (visual): `render_at(timeline, beat_time) -> str`. Whole-document
  generators keep `generate(song)` unchanged (byte-identical output — a hard
  constraint; mapping was NOT hoisted out of them).
- **Sink**: `setup/write/read_key(blocking)/teardown`. `PlainSink` (stream +
  terminal/scripted keys), `CursesSink` (alt screen, non-blocking poll, resize,
  restore — only built in `main()` on a real TTY), `AudioSink` (non-visual).
- **Transport** (`transport.py`): event-driven loop that advances to
  `min(next_onset, next_redraw)`. Audio fires at **true onset times** (not
  fps-quantized); rendering throttles to `--fps`; wall-clock **anchored** via an
  injected monotonic `now` (no drift). Replaces the three Clock classes. `step`
  vs `tempo` = initial paused/playing state; metronome = a re-timed timeline
  (`metronome_timeline`).
- **Driver** (`app._Driver`): binds renderer + sink + audio to the Transport's
  `render/fire/silence/read_key/show` callbacks; keeps the loop testable with an
  injected clock + scripted keys.

## Keys (pager ∪ media-transport convention)

`space` pause/resume (paused: step) · `. ,` step fwd/back · `← →` seek ±1 bar ·
`[ ]` tempo ∓ · `g`/`home`, `end` jump start/end · `h`/`?` help · `q` quit.
`space` collision (page-down vs play/pause) resolved contextually, the mpv way.

## Shared arg layer (`arguments.py`)

`add_tuning_args`, `add_mapper_args`, `add_player_args`, `add_chart_args`,
`build_mapper_config(args, *, tuning, num_strings)`, `resolve_num_strings`. The
converter, `gtrsnipe-play`, and `gtrsnipe-chords` all compose them → every option
reaches every mode, defined once.

## CLI

Flat `gtrsnipe -i … -o …` unchanged (byte-identical). Additions: `-o x.chords.md`
(chord sheet output format), `--play [--view tab] [--audio …]` (interactive; `-o`
optional). `gtrsnipe-play`/`gtrsnipe-chords` remain as curated convenience stubs
sharing the same engine (`run_player_from_args`, `build_chord_sheet`).

## Notes / deferred

- Audio still sustains to the next onset (legato); the event loop makes true
  note-durations/rests cheap to add later (enqueue note-off at onset+duration).
- Backlog: `--name-chords`, `--prefer-open-chords`, shape-relative naming,
  playability-based `--analyze`, search `/` + `:goto` command line.
- Windows needs `windows-curses`; PlainSink is the fallback everywhere.
