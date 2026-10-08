# gtrsnipe backlog

The single list of open work, as of **v0.8.0 (2026-10-07)**. It collates the old parking
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
- **IDs are stable** and never reused. A finished item is marked `✓ vX.Y.Z` in its step under
  [The plan](#the-plan), which keeps its ID and version, and its row leaves
  [Open items](#open-items). The CHANGELOG entry for that version is the permanent record.

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

### Step 3: features, one at a time ✓ (v0.6.6–v0.6.18)

B07 ✓ and F06 ✓ (v0.6.6), F03 ✓ (v0.6.7), P01 ✓ (v0.6.8), P03 ✓ (v0.6.9); a docs
interlude (H05, H06; v0.6.10). C01 with C06 ✓ (v0.6.11), F04 ✓ (v0.6.12), C03 ✓ (v0.6.13), and the R03
follow-ups (R12, R15; v0.6.14), C02 ✓ (v0.6.15), C07 ✓ (v0.6.16), C04, C05 and F02 ✓ together
(v0.6.18; v0.6.17 was the public roll-up of 0.6.10–0.6.16). Still open from this step's list:
F01 VexTab articulations, P02 tempo changes, P04 pager search, P05 other renderers.

**Triage at the end of this step (2026-10-05).** From the parking lot into the backlog: the
open code bugs (B08–B22, H08), the playability group (M01–M07), the tab checker's follow-ups
(F07) and homograph comfort (R16). Their design notes are in
[`NOTES-playability.md`](NOTES-playability.md). Kept parked: more strings for homographs,
`--min-note-length`, the flatwound suffix, optimizer objectives, learned weights, and what the
keys work left out.

### Step 4: a bug sweep, then playability (next)

1. **The bug sweep** ✓ (v0.6.19): B08–B21 and H08; B22 in part (the fallback MIDI reader
   itself is parked for replacement).
   Then B05 ✓ (v0.7.0): a tab is kept as written, and its bars are read as measures.
2. **The measuring stick** (M01–M03): the weights audit, Viterbi vs greedy across a corpus,
   and a first tab difficulty measure. The later playability items depend on it.
3. Then choose: **chosen compromises** (M05 optional notes, M06 a hand profile, then M07
   beginner's-version tabs), or M04, the search for an easier tuning.
4. Whenever the homograph side has time: F07 and R16 (with R14).
5. F08 ✓ (v0.8.0), the dash-count tab layout: agreed and built 2026-10-07.

---

## Open items

Only what is still to do. A finished item's ID and version are in its step under
[The plan](#the-plan), and the CHANGELOG has the detail.

Next free IDs: B24, R19, P07, C08, M08, F09, H09.

### Bugs

| ID | Item | Size | Source |
|---|---|---|---|
| B22 | Partly, v0.6.19: the fallback MIDI reader no longer loses a track over a flat key signature, parses each track once, and reads its first track before scanning it. But py-midi garbles a track's leading events, so key, tempo and meter still aren't reliable there. Parked: replace the fallback reader. | S | v0.6.18 |
| B23 | **Triplets don't survive a conversion.** (1) The default pre-quantize pass snaps every onset to a 32nd-note grid (`--quantization-resolution 0.125`), so a triplet eighth at 1/3 of a beat lands on 0.375, in every output; the grid choices include no triplet grid, and `--no-pre-quantize` is the only way to keep one. (2) The ABC writer rounds a triplet eighth to three 32nds (`E3/2` at `L:1/16`) with or without the grid, so its bar comes out a 32nd too long. The tab layouts (v0.8.0) do carry triplets exactly when they are given them. | M | F08 testing |

### Research: homograph phase 3 and the offset profile

| ID | Item | Size | Source |
|---|---|---|---|
| R08 | Homograph solver limits, all low priority: re-rhythm for 3+ songs; exact chord-voice pairing (greedy today); middle-mode offsets for a class split across strings; the 20,000-assignment search cap. | M each | DESIGN-homograph §5 |
| R09 | GigaMIDI (see D5). | — | corpus plan |
| R10 | **Scan with re-rhythm**: a rhythm slop ratio and `--homograph-subdivide` in `scan`/`aswritten`. Today only identical (or proportional) rhythms meet. | M | R04, parking lot |
| R11 | **LMD-full**: build the cache (about 3 h) and scan it. Mostly unattended machine time; R04's curves already look saturated. | L (machine) | R04, parking lot |
| R13 | **Literature search for the stutter-invariance principle** (*scottvr, in progress*): the checklist in `PROOF-alignment.md`, "Citations to verify". Needed before any novelty claim about the general statement. | S–M | R07, parking lot |
| R14 | **Third-party tabs as written**: R05's natural next input (tabs from community sites, checked against a reference MIDI). Kept local for copyright reasons. Pairs with the tab checker (parking lot). | M | R05, docs audit |
| R16 | **Homograph comfort: offer every compatible string to each interval class.** Today a class may use only its assigned strings plus one spare, so the measured discomfort is an upper bound (a plain transposition still costs 0.57 points per note). Also: under a comfort limit, middle mode is no longer a superset of anchored. | M | F06, parking lot |

### Player and audio

| ID | Item | Size | Source |
|---|---|---|---|
| P02 | Honor tempo changes in playback (constant tempo today). | M | player notes |
| P04 | Search (`/`) and `:goto` in the pager. | S | DESIGN-unified-io |
| P05 | Browser and Qt renderers (they slot in under `render/`). | L | player notes |
| P06 | Windows: document or declare `windows-curses` (the plain output works everywhere). | S | DESIGN-unified-io |

### Chords

Nothing open.

### Mapper and playability

Design notes: [`NOTES-playability.md`](NOTES-playability.md).

| ID | Item | Size | Source |
|---|---|---|---|
| M01 | **Weights audit**: each score term's feature and unit; the defaults as exchange rates (one fret of hand travel = 1); which weights are structural and which are taste; priorities disguised as big numbers; `barre_bonus`/`barre_penalty` as one knob; open strings scoring no better than fretted notes. | M | scottvr, parking lot |
| M02 | **Viterbi vs greedy across a corpus**: does the Viterbi mapper's improvement generalize? Score per note, hand travel and big jumps on a corpus sample, not one piece. | M | scottvr, docs audit |
| M03 | **A tab difficulty measure**: objective complexity from the tab (travel, stretches, speed at tempo, chord changes, barres, position shifts), after a literature search, validated against graded repertoire. | M–L | scottvr |
| M04 | **Search for an easier tuning** than the traditional one: local search on the mapper's score over nearby tunings, string physics as a constraint, the traditional tuning's score reported beside the best found. | M | scottvr |
| M05 | **Optional notes**: let the user change what gets tabbed (`--max-chord-notes`, top-three and shell voicings; then a drop cost per note by musical importance), with what was dropped reported. | M–L | scottvr |
| M06 | **A hand profile**: which fingers are available (accessibility), for chord shapes and for the mapper's span and movement costs. | M | scottvr |
| M07 | **Beginner's-version tabs**: a simplified, disclosed version of a complex tab, from M05 and M06 plus the difficulty measure. | M | scottvr |

### Formats and analysis

| ID | Item | Size | Source |
|---|---|---|---|
| F01 | VexTab output: emit hammer-on, pull-off and tap marks, and rests. | M | CHANGELOG 0.3.0 |
| F05 | **Pretty PDF tab output**: typeset tabs as a PDF worth printing (title and header, clean staff lines, measure bars, tuning key, maybe rhythm stems or notation). Intended eventually. The empty stub goes in step 1 so it isn't mistaken for a feature; this item is where PDF output comes back. | M–L | code stub; D6 |
| F07 | **Tab checker follow-ups**: a `--check-tab REF` that lists every conflicting note and bar (not just the first bad string); partial alignment for tabs with a few missing or extra notes; batch mode over many tabs of one song. | M | parking lot |

### Tests and housekeeping

| ID | Item | Size | Source |
|---|---|---|---|
| H01 | **The golden gate has no local cases on this machine.** Add the wiki examples (Mr Crowley, Bach Cello Prelude, Asturias, Barney Miller) as local golden cases. The expected tabs are now in `docs/wiki/` and `examples/aswritten/`, but the MIDI/audio inputs aren't (they're on the machine in pieces). | S | RELEASE-PLAN v0.3.0 |
| H03 | Wiki: document v0.6.0 (homographs, string physics, `.tab` header behavior). | S–M | release |
