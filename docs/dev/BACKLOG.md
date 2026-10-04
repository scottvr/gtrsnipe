# gtrsnipe backlog

The single list of open work, as of **v0.6.18 (2026-10-04)**. It collates the old parking
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
the alignment proof (v0.6.3); R04 the corpus homograph scan (v0.6.4); R05 real fingerings as
written, on gtrsnipe's wiki tabs (v0.6.5); R06 the literature search (v0.6.2). Results,
proofs and the literature survey are in [`docs/research/`](../research/README.md). R08 and R09
stay open, low priority.

**Triage at the end of this step (2026-09-27).** The parking lot's six entries became:
- B07, the MIDI track-name bug;
- F06, the playability threshold for homograph tabs (paired with F03);
- R10–R12, the scan and similarity follow-ups;
- R13, the literature search for the stutter-invariance principle.

### Step 3: features, one at a time (next)

B07 ✓ and F06 ✓ (v0.6.6), F03 ✓ (v0.6.7), P01 ✓ (v0.6.8), P03 ✓ (v0.6.9); a docs
interlude (H05, H06; v0.6.10). C01 with C06 ✓ (v0.6.11), F04 ✓ (v0.6.12), C03 ✓ (v0.6.13), and the R03
follow-ups (R12, R15; v0.6.14), C02 ✓ (v0.6.15), C07 ✓ (v0.6.16), C04, C05 and F02 ✓ together
(v0.6.18; v0.6.17 was the public roll-up of 0.6.10–0.6.16). Next: triage the parking lot, then
F01 VexTab articulations, P02 tempo changes, P04 pager search, P05 other renderers, …

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
| R12 | ✓ v0.6.14 **Richness under its own optimal warping**: exact up to 6 offsets, with the other warped offset measures, in R03b (phrase and motif retrieval on MTC-ANN). | M–L | R03 "Limits", parking lot |
| R13 | **Literature search for the stutter-invariance principle** (*scottvr, in progress*): the checklist in `PROOF-alignment.md`, "Citations to verify". Needed before any novelty claim about the general statement. | S–M | R07, parking lot |
| R14 | **Third-party tabs as written**: R05's natural next input (tabs from community sites, checked against a reference MIDI). Kept local for copyright reasons. Pairs with the tab checker (parking lot). | M | R05, docs audit |
| R15 | ✓ v0.6.14 **The R03 follow-ups** (scottvr, 2026-09-29): phrase- and motif-level retrieval on MTC-ANN's annotations, alignment-based baselines (interval and pitch DTW), and the §6 reuse hypothesis. | M | parking lot |

### Player and audio

| ID | Item | Size | Source |
|---|---|---|---|
| P01 | ✓ v0.6.8 **True note durations and rests** in playback (`--legato` for the old way); the MIDI reader keeps notes shorter than a sixteenth; `--sustain string` lets tab notes ring until their string is restruck. | M | CHANGELOG 0.4.0 |
| P02 | Honor tempo changes in playback (constant tempo today). | M | player notes |
| P03 | ✓ v0.6.9 **Default the audio instrument and channel from the MIDI file's program change** (the reader keeps each track's program and channel; `--instrument` still wins). | S–M | parking lot |
| P04 | Search (`/`) and `:goto` in the pager. | S | DESIGN-unified-io |
| P05 | Browser and Qt renderers (they slot in under `render/`). | L | player notes |
| P06 | Windows: document or declare `windows-curses` (the plain output works everywhere). | S | DESIGN-unified-io |

### Chords

| ID | Item | Size | Source |
|---|---|---|---|
| C01 | ✓ v0.6.11 **`--name-chords`**: chord names above the tab staff, over each bar's first note, where the chord changes and at each line start; half-bar changes named; only plainly spelled chords. | M | player notes |
| C02 | ✓ v0.6.15 **`--prefer-open-chords`**: open-position chord shapes found by search (any tuning, capo), with a fingerability rule; every diagram captioned with its shape. | M–L | player notes |
| C03 | ✓ v0.6.13 **Shape-relative chord names** (`--shape-names`): named as in standard tuning with no capo, for evenly shifted tunings plus any capo; drop/open tunings stay in concert pitch; a banner always says which. Charts, `--name-chords`, `--name-chord`. | M | player notes |
| C04 | ✓ v0.6.18 **Extended chords**: 9, maj9, m9, 7b9, 7#9, 11, m11, 13, maj13, m13, 7sus4 (and add9, 6/9 for fret shapes). Named only when complete, with the root in the bass, so a melody note isn't taken for an extension. | M | CHANGELOG 0.4.0 |
| C05 | ✓ v0.6.18 **Key-aware spelling**: a key on the song (`--key`, the file's own, else estimated and said so); chord names spelled for it (Ab in Eb, G# in E). | M | CHANGELOG 0.4.0 |
| C06 | ✓ v0.6.11 **`--name-chord SHAPE`**: name a fret shape (`x,x,3,2,1,0`) in any tuning, with no input file. | S | scottvr, parking lot |
| C07 | ✓ v0.6.16 **Chart voicing modes** (scottvr, 2026-10-03): `--chart-voicing source` (default: the song's own fingering, where one hand shape holds it), `compact`, `open`; the header states the mode; charts name bars as `--name-chords` does. | M | scottvr |

### Formats and analysis

| ID | Item | Size | Source |
|---|---|---|---|
| F01 | VexTab output: emit hammer-on, pull-off and tap marks, and rests. | M | CHANGELOG 0.3.0 |
| F02 | ✓ v0.6.18 **ABC output with a real key signature** (`K:`), notes spelled in the key, and accidentals that read the same under every propagation rule. MIDI output carries the song's own key too. | M | CHANGELOG 0.3.0 |
| F03 | ✓ v0.6.7 **Playability-based `--analyze`**: fingers the song in every fitting tuning and ranks them by the mapper's score per note, with frets, hand travel and open strings. (It showed the default weights don't prefer open strings to a barre: a weights-audit item.) | M | player notes |
| F04 | ✓ v0.6.12 **Tension display outside homographs**: `--show-tuning` with gauges and tensions as a retune of your guitar; warnings for custom tunings; `--solve-tuning` notes pitches past steel. Also re-entrant gauge order and the documented `p` suffix. | S | parking lot |
| F05 | **Pretty PDF tab output**: typeset tabs as a PDF worth printing (title and header, clean staff lines, measure bars, tuning key, maybe rhythm stems or notation). Intended eventually. The empty stub goes in step 1 so it isn't mistaken for a feature; this item is where PDF output comes back. | M–L | code stub; D6 |
| F06 | ✓ v0.6.6 **Playability of homograph tabs**: discomfort per note vs A's own best tab, `--homograph-max-discomfort`, `scan --max-discomfort/--max-fret`. Comfort filters hard: 19/50 sampled folk pairs within 50 points per note, 0 within 5. | S + M | R04, parking lot |

### Tests and housekeeping

| ID | Item | Size | Source |
|---|---|---|---|
| H01 | **The golden gate has no local cases on this machine.** Add the wiki examples (Mr Crowley, Bach Cello Prelude, Asturias, Barney Miller) as local golden cases. The expected tabs are now in `docs/wiki/` and `examples/aswritten/`, but the MIDI/audio inputs aren't (they're on the machine in pieces). | S | RELEASE-PLAN v0.3.0 |
| H03 | Wiki: document v0.6.0 (homographs, string physics, `.tab` header behavior). | S–M | release |
| H05 | ✓ v0.6.10 **Docs reorg** (interlude in step 3): `docs/app/` (how gtrsnipe works), `docs/research/` (theory, literature, results), `docs/dev/` (process); a map in `docs/README.md`. | S | scottvr, 2026-09-28 |
| H06 | ✓ v0.6.10 **State-of-the-docs audit**: every doc marked current, stale or wrong, with the fixes needed; agree the list, then apply it. | M | scottvr, 2026-09-28 |
