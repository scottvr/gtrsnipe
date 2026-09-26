# gtrsnipe backlog

The single list of open work, as of **v0.6.0 (2026-09-26)**. It collates the old parking
lot, the CHANGELOG's known limitations, the design docs, the v0.3.0-era audit and plans,
GitHub issues, and findings from recent sessions.

## How this list works

- **New ideas go in [`PARKING-LOT.md`](PARKING-LOT.md).** One or two lines each; capture
  only, no need to start them or even think them through.
- **Triage** (at the end of each step below) moves every parking-lot entry into this
  list, or declines it, and clears the parking lot.
- **One step at a time.** Finish it, release it, then triage and pick the next.
- **Releases are patch-first** (see the CHANGELOG header): a minor bump only for breaking
  changes to the CLI flags or file formats.
- **IDs are stable.** Mark finished items `✓ vX.Y.Z`; drop them at the next triage (the
  CHANGELOG is the permanent record).

Sizes: **S** is an hour or less, **M** is about a session, **L** is several sessions.

---

## The plan

### Step 0: decisions (yours; minutes)

| ID | Decision | Recommendation |
|---|---|---|
| D1 | Fix the tab generator's h/p column bug (B02)? It changes the bytes of every existing tab that uses hammer-ons or pull-offs. | Fix it in 0.6.1. The tabs become *more* correct (digits land in the right column), so it counts as a fix, not a format break. Note it in the CHANGELOG and re-bless any local golden cases. |
| D2 | Close GitHub issue #4? It was resolved on 2026-09-25 and the reporter never replied. | Close it with a thank-you. |
| D3 | Let an explicit `--tuning STANDARD` override a `.tab`'s own header (B04)? | Yes. It's small: `--tuning` defaults to "not given" instead of STANDARD. |
| D4 | Move the v0.3.0-era planning docs (RELEASE-PLAN-v0.3.0, AUDIT-findings, TEST-PLAN, CPU-DECOUPLING) into `docs/dev/archive/`? Their status columns are stale; AUDIT still lists fixed bugs as pending. | Yes. |
| D5 | Request GigaMIDI access? It's gated, CC BY-NC, and ~0.5 TB extracted on the LaCie. | Not now. Revisit if Lakh isn't enough. |
| D6 | PDF tab output: implement it, or delete the empty `PdfTabGenerator` stub? | Delete the stub for now (it's imported but does nothing). Re-add it when you want PDFs. |

### Step 1: v0.6.1, a correctness sweep (about one session)

B01 (ABC parser), B03 (RIFF MIDI), B04 (explicit `--tuning`), B02 (if D1), plus the
D2/D4/D6 housekeeping. B01 matters beyond ABC input: it unblocks the folk-tune ABC corpora
for the research track.

### Step 2: the research track

In order: R01 corpus loaders, R02 offset-profile analyzer, R03 the Meertens experiment
(starts once you've submitted the download form), R04 the corpus homograph scan, R05
published tabs as written. R06 (literature search) and R07 (the alignment proof) can run
any time. Each tool ships as a patch release.

### Step 3: features, one at a time

A suggested order (swap freely if something else is more fun): P01 true note durations
in playback, P03 instrument defaults from the MIDI file, C01 chord names over the tab,
F04 tension display, F03 playability-based `--analyze`, C03 shape-relative chord names,
C02 open-position chord voicings, then C04/C05/F02 together (they share key-aware
spelling), F01 VexTab articulations, P02 tempo changes, P04 pager search, P05 other
renderers.

---

## All open items

### Bugs

| ID | Item | Size | Source |
|---|---|---|---|
| B01 | **ABC parser ignores key signatures** (`K:`), bar-scoped accidentals, and ties, and reads chord symbols in quotes (`"G"`) as notes. Any ABC tune with a key signature decodes wrong. | M | parking lot; corpus work |
| B02 | **Tab generator h/p column bug.** The `h`/`p` prefix is written at the note's column, so its digits land one column late. A chord with one hammered note decodes as a two-note arpeggio, and single hammered notes read slightly late. (The homograph render avoids it by omitting articulations.) | S | homograph review |
| B03 | **MIDI reader returns an empty song for RIFF-wrapped MIDI** instead of reading it or raising an error. There are 259 such files in Lakh. | S | corpus agent |
| B04 | An explicit `--tuning STANDARD` can't override a `.tab`'s own header, because it's indistinguishable from the default. | S | D3 |
| B05 | `-i x.tab --play` re-optimizes the tab's fingering instead of playing it as written. It needs a way (e.g. `--as-written`) to keep the tab's own strings and frets. | S–M | session notes |

### Research: homograph phase 3 and the offset profile

| ID | Item | Size | Source |
|---|---|---|---|
| R01 | **Corpus loaders.** Essen (kern/ABC) through music21. POP909's MELODY track, cutting legato overlaps at the next onset. Lakh melody extraction: a melody-named track if there is one, else the highest line. Skip Lakh's ~660 non-MIDI files. | M | corpus plan |
| R02 | **Offset-profile analyzer** (the structure note's experiment): richness, entropy, C₁…C₆, switch count S, total variation TV, and reuse for two melodies. | S–M | structure note §11 |
| R03 | **Meertens experiment.** On MTC-ANN tune families, does the offset profile beat the transposition-invariant Hamming and interval-Hamming baselines? Needs the download form. | M | structure note §11 |
| R04 | **Corpus homograph scan.** For each aligned pair, find the longest window with richness ≤ 6. Bucket passages by rhythm pattern first so pairs × offsets stays tractable, and run the full solver only on hits. | L | DESIGN-homograph §5 |
| R05 | **Published tabs as written** against candidate B's. Inputs stay local, like the golden cases. | M | DESIGN-homograph §5 |
| R06 | **Literature search** before any novelty claim: δ/γ-approximate matching, SIA/SIATEC, voice-leading geometry, Müllensiefen & Frieler. | S–M | structure note §10 |
| R07 | **Prove (or refute) the alignment claim**: log-richness stays a metric under composable monotone alignments. | S | structure note §7 |
| R08 | Homograph solver limits, all low priority: re-rhythm for 3+ songs; exact chord-voice pairing (greedy today); middle-mode offsets for a class split across strings; the 20,000-assignment search cap. | M each | DESIGN-homograph §5 |
| R09 | GigaMIDI (see D5). | — | corpus plan |

### Player and audio

| ID | Item | Size | Source |
|---|---|---|---|
| P01 | **True note durations and rests** in playback. Each note currently sustains to the next onset; the event-driven Transport makes proper note-offs cheap. | M | CHANGELOG 0.4.0 |
| P02 | Honor tempo changes in playback (constant tempo today). | M | player notes |
| P03 | **Default the audio instrument and channel from the MIDI file's program change.** The reader keeps the instrument name but not the GM program number. | S–M | parking lot |
| P04 | Search (`/`) and `:goto` in the pager. | S | DESIGN-unified-io |
| P05 | Browser and Qt renderers (they slot in under `render/`). | L | player notes |
| P06 | Windows: document or declare `windows-curses` (the plain output works everywhere). | S | DESIGN-unified-io |

### Chords

| ID | Item | Size | Source |
|---|---|---|---|
| C01 | **`--name-chords`**: chord names above the tab staff, aligned, and wrapping in step with `--max-line-width`. | M | player notes |
| C02 | **`--prefer-open-chords`**: open-position voicings. Mapper weights alone don't change the diagrams (tested). The voicing generator must pick the register by open strings and low position, and add doublings so full shapes can form. | M–L | player notes |
| C03 | **Shape-relative chord names** (`--shape-names`, a "generalized capo"). Always print a banner saying so. Only valid for uniformly shifted tunings (baritone, E♭, D standard); fall back to concert pitch for drop and open tunings, and say so. | M | player notes |
| C04 | Extended chords (9ths, 11ths, 13ths). | M | CHANGELOG 0.4.0 |
| C05 | Key-aware enharmonic spelling (sharps only today). Shares work with F02. | M | CHANGELOG 0.4.0 |

### Formats and analysis

| ID | Item | Size | Source |
|---|---|---|---|
| F01 | VexTab output: emit hammer-on, pull-off and tap marks, and rests. | M | CHANGELOG 0.3.0 |
| F02 | ABC output: a real key signature (`K:`) and flat spellings. This needs a key on the Song model. | M | CHANGELOG 0.3.0 |
| F03 | **Playability-based `--analyze`**: score each candidate tuning by the mapper's cost, not just whether the range fits. ("Bonkers in standard, easy in drop-D.") | M | player notes |
| F04 | **Tension display outside homographs**: `--show-tuning` with gauges and tensions, and a warning when a custom tuning would snap a string. | S | parking lot |
| F05 | PDF tab output (see D6). | M | code stub |

### Tests and housekeeping

| ID | Item | Size | Source |
|---|---|---|---|
| H01 | **The golden gate has no local cases on this machine.** Add the wiki examples (Mr Crowley, Bach Cello Prelude, Asturias, Barney Miller) as local golden cases. Needs your files. | S | RELEASE-PLAN v0.3.0 |
| H02 | Archive the v0.3.0-era docs (see D4). | S | audit |
| H03 | Wiki: document v0.6.0 (homographs, string physics, `.tab` header behavior). | S–M | release |
| H04 | Close issue #4 (see D2). | S | GitHub |
