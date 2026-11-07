# gtrsnipe backlog

The single list of open work, as of **v0.8.1 (2026-11-07)**.

## How this list works: The Dull Protocol

- **New ideas go in [`PARKING-LOT.md`](PARKING-LOT.md).** One or two lines each; capture
  only, no need to start them or even think them through.
- **Triage** (at the end of each step below) moves every parking-lot entry into this
  list, or declines it, and clears the parking lot.
- **One step at a time.** Finish it, release it, then triage and pick the next.
- **Releases are patch-first** (see the CHANGELOG header): a minor bump only for breaking
  changes to the CLI flags or file formats.
- **Every task is a checkbox line.** `- [ ] **ID** text (size; source)`. When it ships, tick
  it in place and add the version: `- [x] **ID** text ✓ v0.8.1`. Nothing moves between
  sections. Ticked lines may be deleted at the next triage, since the CHANGELOG entry for
  that version is the permanent record and git history keeps the line.
- **Unreleased changes** are listed under `## [Unreleased]` at the top of the CHANGELOG as
  they are committed; the release renames the heading. Commit as work lands; push only with
  a version bump.
- **IDs are stable** and never reused. Next free: B26, R19, P07, C08, M09, F09, H10.

Sizes: **S** is an hour or less, **M** is about a session, **L** is several sessions.

---

## The plan

- [x] **Step 0** decisions D1–D6, 2026-09-26, all as recommended: fix the h/p column bug
  (D1); close issue #4 (D2); an explicit `--tuning` overrides a `.tab` header (D3); archive
  the v0.3.0 plans (D4; deleted again 2026-11-07, git history keeps them); no GigaMIDI for
  now (D5, see R09); delete the PDF stub, keep F05 (D6).
- [x] **Step 1** a correctness sweep: B01–B04, B06 ✓ v0.6.1.
- [x] **Step 2** the research track: R01–R07 ✓ v0.6.2–v0.6.5. Results, proofs and the
  literature survey are in [`docs/research/`](../research/README.md).
- [x] **Step 3** features one at a time: B07, F06, F03, P01, P03, H05–H07, C01–C07, F02, F04,
  R12, R15 ✓ v0.6.6–v0.6.18.
- [ ] **Step 4** a bug sweep, then playability:
  - [x] the bug sweep, B08–B21, H08, B22 in part ✓ v0.6.19; B05 tabs kept as written ✓ v0.7.0
  - [x] F08 the dash-count tab layout ✓ v0.8.0
  - [ ] **the measuring stick** (M01–M03); the later playability items depend on it
    - [x] M01 the weights audit, the sweep tool, the six questions answered in
      [`NOTES-playability.md`](NOTES-playability.md) ✓ v0.8.1
    - [x] M02 Viterbi vs greedy, 450 tunes, never worse, better on 86% ✓ v0.8.1
    - [ ] M03 a tab difficulty measure
      - [x] literature search, `docs/research/literature/LITERATURE-difficulty.md` (2026-11-07)
      - [x] the ingredients as per-onset descriptors from a tab (index-finger travel scaled by
        time, fingers down, stretch, barre, notes per second, chord changes, position shifts,
        repetitiveness) and their profile (mean, quadratic mean, max); the lazy hand model
        (`gtrsnipe-research difficulty`, 2026-11-07)
      - [ ] shape uncommonness (needs a reference corpus of fingered shapes)
      - [x] a first graded set: the RCM 2018 list matched to classtab.org's archive, 50 sure
        matches copied to `/Volumes/LaCie/data/midi/graded/rcm/` with a manifest (2026-11-07)
      - [ ] the 65 weak candidates in that manifest checked by hand (scottvr); Trinity or
        ABRSM as a second list; ClassClef / GAPS for what classtab lacks
      - [x] first rank correlations, 49 pieces: hand move rate 0.71, the provisional index
        0.66, length 0.60 (a confound); in `NOTES-playability.md` (2026-11-07)
      - [ ] validate properly: more pieces, real tempi, adjacent accuracy, the length confound
        handled; then fit the weights
      - [ ] ship as `gtrsnipe-research difficulty` with a per-tab report
    - [ ] M08 the time-scaled movement cost, in the scorer and the measure (scottvr,
      2026-11-07: implement)
  - [ ] then choose: **chosen compromises** (M05 optional notes, M06 a hand profile, then M07
    beginner's-version tabs), or M04, the search for an easier tuning
  - [ ] whenever the homograph side has time: F07 and R16 (with R14), and the composed pieces
    (R17, R18)

---

## Open items

### Bugs

- [ ] **B22** Partly done in v0.6.19: the fallback MIDI reader no longer loses a track over a
  flat key signature, parses each track once, and reads its first track before scanning it.
  But py-midi garbles a track's leading events, so key, tempo and meter still aren't reliable
  there. Parked: replace the fallback reader. (S; v0.6.18)
- [x] **B24** Tab reader: string lines without labels (`|---`, `||---`), labels without a
  bar, bare dashes; classtab's `=` sustain marks. Found on the classtab archive: 74 of a
  400-tab sample read as empty. ✓ unreleased, 2026-11-07
- [x] **B25** Viterbi stage loop: first order searched the t−2 predecessors once per
  current fingering instead of once per previous one (`O(K³)` for nothing); second order
  called the scorer per t−2 candidate when it reads only that candidate's fret range.
  Hoisted, bucketed, step scores memoised per song; identical paths and scores (oracle test
  `tests/mapper/test_viterbi_equivalence.py`); chordal second-order pieces 10–18× faster.
  Next step if needed: split the scorer into per-fingering and per-transition parts.
  ✓ unreleased, 2026-11-07
- [ ] **B23** **Triplets don't survive a conversion.** (1) The default pre-quantize pass snaps
  every onset to a 32nd-note grid (`--quantization-resolution 0.125`), so a triplet eighth at
  1/3 of a beat lands on 0.375, in every output; the grid choices include no triplet grid, and
  `--no-pre-quantize` is the only way to keep one. (2) The ABC writer rounds a triplet eighth
  to three 32nds (`E3/2` at `L:1/16`) with or without the grid, so its bar comes out a 32nd
  too long. The tab layouts (v0.8.0) do carry triplets exactly when they are given them.
  (M; F08 testing)

### Research: homograph phase 3 and the offset profile

- [ ] **R08** Homograph solver limits, all low priority: re-rhythm for 3+ songs; exact
  chord-voice pairing (greedy today); middle-mode offsets for a class split across strings;
  the 20,000-assignment search cap. (M each; DESIGN-homograph §5)
- [ ] **R09** GigaMIDI (see D5: not now; revisit if Lakh isn't enough). (corpus plan)
- [ ] **R10** **Scan with re-rhythm**: a rhythm slop ratio and `--homograph-subdivide` in
  `scan`/`aswritten`. Today only identical (or proportional) rhythms meet. (M; R04)
- [ ] **R11** **LMD-full**: build the cache (about 3 h) and scan it. Mostly unattended machine
  time; R04's curves already look saturated. (L, machine; R04)
- [ ] **R13** **Citation check** (scottvr, in progress; StegTab identified 2026-09-28).
  Verify the citations the copyright paper (and any later note) actually uses. The structure
  note (revision 4) makes no claim of a new mathematical result and says which combinations
  weren't found documented, so no further novelty search is planned. (S–M; R07)
  - [ ] the StegTab row in `LITERATURE-offsets.md`: URL, title, access date (✎ scottvr); its
    later academic variants are unexamined (from the 2026-09-28 docs audit, LI-4)
  - [ ] the survey rows marked "check level not recorded" (DOI only): Callender–Quinn–Tymoczko,
    Tymoczko, Hall & Tymoczko, De Souza, Seeger, Kanno, Rahmatian's quote, Aczél–Forte–Ng
    (docs audit, LI-5)
  - [ ] the computer-vision names in the structure note §10
  - [ ] PROOF-alignment's "Citations to verify" list (Allali et al.'s "return is charged
    again" is inferred, not confirmed)
- [ ] **R14** **Third-party tabs as written**: R05's natural next input (tabs from community
  sites, checked against a reference MIDI). Kept local for copyright reasons. Pairs with the
  tab checker (F07) and the parked Power Tab reader. **Input found 2026-11-07:** classtab.org's
  archive (3,977 classical tabs with 2,341 MIDI twins, local under `data/classtab-zip/`),
  of which a quarter state no tuning, the "stripped" case the homograph argument is about;
  the tuning survey's numbers are in the parking lot. (M; R05)
- [ ] **R16** **Homograph comfort: offer every compatible string to each interval class.**
  Today a class may use only its assigned strings plus one spare, so the measured discomfort
  is an upper bound (a plain transposition still costs 0.57 points per note). Also: under a
  comfort limit, middle mode is no longer a superset of anchored. (M; F06)
- [ ] **R17** **Compose a piece for two tunings** (scottvr, 2026-10-05): a homograph by
  design, where every example so far pairs two existing tunes. Composing lets the offsets be
  chosen first (which strings carry which interval) and the comfort be designed in. Wants a
  helper that shows what each tab position sounds like in the second tuning; R16 makes the
  result more playable. (M + composing)
- [ ] **R18** **Compose a polyphonic piece for two tunings** (scottvr, 2026-10-05): the same
  with more than one voice at a time. The theorem allows chords (one note per string at a
  time); every example so far is a single line. (M + composing)

### Player and audio

- [ ] **P02** Honor tempo changes in playback (constant tempo today). (M; player notes)
- [ ] **P04** Search (`/`) and `:goto` in the pager. (S; DESIGN-unified-io)
- [ ] **P05** Browser and Qt renderers (they slot in under `render/`). (L; player notes)
- [ ] **P06** Windows: document or declare `windows-curses` (the plain output works
  everywhere). (S; DESIGN-unified-io)

### Chords

Nothing open.

### Mapper and playability

Design notes: [`NOTES-playability.md`](NOTES-playability.md), including the 2026-11-07
hand-position discussion (the index finger as the hand's position, reach by span) that feeds
M03 and M06.

- [ ] **M03** **A tab difficulty measure**: objective complexity from the tab (travel,
  stretches, speed at tempo, chord changes, barres, position shifts), after a literature
  search, validated against graded repertoire. (M–L; scottvr)
  - [x] every subset of the wiki's Asturias option set (2^10) on the three original pieces:
    interactions, substitutes and dead knobs in "The option set as a 2^k sweep" in
    [`NOTES-playability.md`](NOTES-playability.md) (2026-11-07)
  - [ ] the same sweep against the 44 graded classtab tabs (editors' fingerings), then fit
    weights to them (scottvr: fit to the graded set, and to the originals, and to both)
  - [ ] defaults vs profiles (scottvr, 2026-11-07): fit the defaults to the upper syllabus
    levels and the non-pedagogical sample; ship beginner and intermediate profiles for the
    first-position repertoire, where the defaults agree least (notes: "Agreement by grade")
  - [ ] scottvr's ear check on the three calibration tabs in `runs/m03-graded-set-2026-11-07/listen/`
- [ ] **M04** **Search for an easier tuning** than the traditional one: local search on the
  mapper's score over nearby tunings, string physics as a constraint, the traditional tuning's
  score reported beside the best found. (M; scottvr)
- [ ] **M05** **Optional notes**: let the user change what gets tabbed (`--max-chord-notes`,
  top-three and shell voicings; then a drop cost per note by musical importance), with what
  was dropped reported. (M–L; scottvr)
- [ ] **M06** **A hand profile**: which fingers are available (accessibility), for chord
  shapes and for the mapper's span and movement costs; and the hand-position state (position
  is the index finger; notes within the span above it cost no travel). (M; scottvr)
- [ ] **M08** **Time-scaled movement cost**: a hand move costs more the shorter the gap from the
  end of the previous note to the next onset (decided 2026-11-07: end-to-start, since lifting
  the finger ends the note; exact with a tempo, relative without; MIDI's default tempo serves). Gated on
  rhythm reliability: automatic when the tab's header marks gtrsnipe's layout, a user flag
  for tabs in the wild. Design notes under "Time-scaled movement cost" in
  [`NOTES-playability.md`](NOTES-playability.md); Hori & Sagayama 2016 is the precedent. (M;
  scottvr, M03 survey)
  - [x] both time bases built on the measure side (`--both`); first numbers in
    `NOTES-playability.md`: tabs and folk corpora have no note ends, so end-to-start sits on
    its floor there; POP909 (67% early releases) is the input that can tell them apart
  - [x] the scorer-side version (`--movement-time-base onset|end`, 2026-11-07) run on 60
    pieces; numbers in `NOTES-playability.md`, listening set in `runs/m08-2026-11-07/`
  - [ ] scottvr plays the differing tabs and judges; then the reference (0.5 s) and floor
    (0.05 s) get set from that, and the default decided
  - [ ] for tabs in the wild, compare approximate (dash-derived) against off, the same way
  - [ ] the outcome is called out explicitly either way, in the notes and any paper, with
    the evidence beside it: if end-to-start wins, as a departure from Hori & Sagayama; if
    onset-to-onset wins, as a rationale they did not give (scottvr, 2026-11-07)
- [ ] **M07** **Beginner's-version tabs**: a simplified, disclosed version of a complex tab,
  from M05 and M06 plus the difficulty measure. (M; scottvr)

### Formats and analysis

- [ ] **F01** VexTab output: emit hammer-on, pull-off and tap marks, and rests. (M;
  CHANGELOG 0.3.0)
- [ ] **F05** **Pretty PDF tab output**: typeset tabs as a PDF worth printing (title and
  header, clean staff lines, measure bars, tuning key, maybe rhythm stems or notation).
  Intended eventually; the empty stub was deleted in v0.6.1 (D6) so it isn't mistaken for a
  feature. (M–L)
- [ ] **F07** **Tab checker follow-ups**: a `--check-tab REF` that lists every conflicting note
  and bar (not just the first bad string); partial alignment for tabs with a few missing or
  extra notes; batch mode over many tabs of one song. (M; parking lot)

### Tests and housekeeping

- [ ] **H01** **The golden gate has no local cases on this machine.** Add the wiki examples
  (Mr Crowley, Bach Cello Prelude, Asturias, Barney Miller) as local golden cases. The
  expected tabs are in `docs/wiki/` and `examples/aswritten/`, but the MIDI/audio inputs
  aren't (they're on the machine in pieces). (S; RELEASE-PLAN v0.3.0)
- [ ] **H03** Wiki: document v0.6.0 (homographs, string physics, `.tab` header behavior).
  (S–M; release)
- [ ] **H07** **The story** (`docs/research/story/`): from the idea to the research, in
  chapters scottvr can link from an HTML page, as fodder for posts and the paper. First draft
  v0.6.10. Since 2026-10-08 it is one account by two authors: scottvr is revising each
  chapter inline on the `story-scottvr` branch, and a chapter that still has its "scottvr's
  account" section is one he hasn't reached. Stays private until he has reviewed all of it.
  (M; scottvr, 2026-09-28)
  - [ ] Gemini's role (the `collision_plot_template.py` credit) is his to describe, in
    chapter 10 (✎; docs audit decision 5)
- [ ] **H09** **Document why the tab header matters** (scottvr, 2026-11-07): until every tab
  is made by gtrsnipe or the practice spreads, the gtrsnipe lines in a tab's comment header
  (`// Transcribed with:`, `// Rhythm:`, `// Lengths:`) tell gtrsnipe, and anyone else, that
  the dashes can be relied on for timing. Users should want to keep them. Touches the parked
  `--omit-comments` and command-line-stamp entries. (S)
