# gtrsnipe backlog

The single list of open work, as of **v0.6.6 (2026-09-27)**. It collates the old parking
lot, the CHANGELOG's known limitations, the design docs, the v0.3.0-era audit and plans,
GitHub issues, and findings from recent sessions.

## How this list works: The Dull Protocol

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

### Step 0: decisions ✓ (all decided 2026-09-26, as recommended)

| ID | Decision | Outcome |
|---|---|---|
| D1 | Fix the tab generator's h/p column bug (B02)? It changes the bytes of every existing tab that uses hammer-ons or pull-offs. | **Yes, in 0.6.1.** The tabs become *more* correct (digits land in the right column), so it counts as a fix, not a format break. Note it in the CHANGELOG and re-bless any local golden cases. |
| D2 | Close GitHub issue #4? It was resolved on 2026-09-25 and the reporter never replied. | **Yes.** Close it with a thank-you, in step 1. |
| D3 | Let an explicit `--tuning STANDARD` override a `.tab`'s own header (B04)? | **Yes.** Done in 0.6.1 by recording when `--tuning` is given, rather than changing its default. |
| D4 | Move the v0.3.0-era planning docs (RELEASE-PLAN-v0.3.0, AUDIT-findings, TEST-PLAN, CPU-DECOUPLING) into `docs/dev/archive/`? Their status columns are stale; AUDIT still lists fixed bugs as pending. | **Yes**, in step 1. |
| D5 | Request GigaMIDI access? It's gated, CC BY-NC, and ~0.5 TB extracted on the LaCie. | **Not now.** Revisit if Lakh isn't enough. |
| D6 | PDF tab output: implement it, or delete the empty `PdfTabGenerator` stub? | **Delete the stub** in step 1 (it's imported but does nothing). Pretty PDF output itself stays on the list as F05. |

### Step 1: v0.6.1, a correctness sweep ✓ (released as v0.6.1)

B01 (ABC parser), B02 (h/p columns), B03 (RIFF MIDI), B04 (explicit `--tuning`), plus
B06 (`--num-strings 7`, found along the way), and the D2/D4/D6 housekeeping. The ABC
rewrite was validated against music21 on 1,034 Nottingham tunes (94% note-for-note, the
rest being music21 quirks), which unblocks the folk-tune ABC corpora for the research
track. Triage at the end of this step: the parking lot was empty.

### Step 2: the research track ✓ (v0.6.2–v0.6.5)

R01 corpus loaders and R02 the offset profile (v0.6.2); R03 the Meertens experiment and R07
the alignment proof (v0.6.3); R04 the corpus homograph scan (v0.6.4); R05 published tabs as
written (v0.6.5); R06 the literature search (v0.6.2). Results: `RESULTS-R03-families.md`,
`RESULTS-R04-scan.md`, `RESULTS-R05-aswritten.md`, `PROOF-alignment.md`,
`LITERATURE-offsets.md`. R08 and R09 stay open, low priority.

**Triage at the end of this step (2026-09-27).** The parking lot's six entries became:
- B07, the MIDI track-name bug;
- F06, the playability threshold for homograph tabs (paired with F03);
- R10–R12, the scan and similarity follow-ups;
- R13, the literature search for the stutter-invariance principle.

### Step 3: features, one at a time (next)

B07 ✓ and F06 ✓ (v0.6.6). Next **F03** (playability-based `--analyze`), which can reuse F06's
per-note score.

Then, as before (swap freely if something else is more fun): P01 true note durations in
playback, P03 instrument defaults from the MIDI file, C01 chord names over the tab, F04
tension display, C03 shape-relative chord names, C02 open-position chord voicings, then
C04/C05/F02 together (they share key-aware spelling), F01 VexTab articulations, P02 tempo
changes, P04 pager search, P05 other renderers.

---

## All open items

### Bugs

| ID | Item | Size | Source |
|---|---|---|---|
| B05 | `-i x.tab --play` re-optimizes the tab's fingering instead of playing it as written. It needs a way (e.g. `--as-written`) to keep the tab's own strings and frets. | S–M | session notes |
| B07 | ✓ v0.6.6 **`MidiReader` drops MIDI track names** (mido path). Fixed; tab titles for named tracks now read "Title (Melody)". | S | R01, parking lot |

### Research: homograph phase 3 and the offset profile

| ID | Item | Size | Source |
|---|---|---|---|
| R08 | Homograph solver limits, all low priority: re-rhythm for 3+ songs; exact chord-voice pairing (greedy today); middle-mode offsets for a class split across strings; the 20,000-assignment search cap. | M each | DESIGN-homograph §5 |
| R09 | GigaMIDI (see D5). | — | corpus plan |
| R10 | **Scan with re-rhythm**: a rhythm slop ratio and `--homograph-subdivide` in `scan`/`aswritten`. Today only identical (or proportional) rhythms meet. | M | R04, parking lot |
| R11 | **LMD-full**: build the cache (about 3 h) and scan it. Mostly unattended machine time; R04's curves already look saturated. | L (machine) | R04, parking lot |
| R12 | **Richness under its own optimal warping** as the fair similarity test for R03: a minimum-label path per pair, exact for k ≤ 6. Unlikely to overturn R03. | M–L | R03 "Limits", parking lot |
| R13 | **Literature search for the stutter-invariance principle** (*scottvr, in progress*): the checklist in `PROOF-alignment.md`, "Citations to verify". Needed before any novelty claim about the general statement. | S–M | R07, parking lot |

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
| F05 | **Pretty PDF tab output**: typeset tabs as a PDF worth printing (title and header, clean staff lines, measure bars, tuning key, maybe rhythm stems or notation). Intended eventually. The empty stub goes in step 1 so it isn't mistaken for a feature; this item is where PDF output comes back. | M–L | code stub; D6 |
| F06 | ✓ v0.6.6 **Playability of homograph tabs**: discomfort per note vs A's own best tab, `--homograph-max-discomfort`, `scan --max-discomfort/--max-fret`. Comfort filters hard: 19/50 sampled folk pairs within 50 points per note, 0 within 5. | S + M | R04, parking lot |

### Tests and housekeeping

| ID | Item | Size | Source |
|---|---|---|---|
| H01 | **The golden gate has no local cases on this machine.** Add the wiki examples (Mr Crowley, Bach Cello Prelude, Asturias, Barney Miller) as local golden cases. The expected tabs are now in `docs/wiki/` and `examples/aswritten/`, but the MIDI/audio inputs aren't (they're on the machine in pieces). | S | RELEASE-PLAN v0.3.0 |
| H03 | Wiki: document v0.6.0 (homographs, string physics, `.tab` header behavior). | S–M | release |
