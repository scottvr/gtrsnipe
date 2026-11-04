# Playability: design notes

Notes carried over from the parking lot at the 2026-10-05 triage, for the backlog's
playability items (M01–M07 in [`BACKLOG.md`](BACKLOG.md)). They are the thinking so far,
as written when each idea was parked, not a plan: each item gets its plan when it starts.

## M01–M03: the scoring weights (audit, Viterbi vs greedy, difficulty), and the parked learning ideas

- **Scoring weights: a whole-tab difficulty score, learned weights and style profiles**
  (scottvr, 2026-09-27).
  - Today's weights were hand-balanced one new option at a time. The Asturias wiki page needs
    a long command line to get a playable tab, while Mr Crowley works with defaults.
  - Ideas:
    1. a whole-tab difficulty "meta-score" (fretted notes, total fret travel, position
       shifts, stretches, …);
    2. a difficulty estimate for a song *before* transcription, from the MIDI/ABC alone;
    3. style profiles (flamenco ≈ the Asturias options, rockabilly ≈ barre-friendly) as
       named option bundles;
    4. learning the weights rather than hand-tuning them.
  - Note (Claude): the mapper's score is mostly weight × feature, summed along a Viterbi
    path, which is textbook structured prediction. A *structured perceptron* can learn the
    weights from human-fingered tabs: decode, compare with the human fingering, move the
    weights by the feature difference. That's one Viterbi pass per tab per epoch, and the
    knobs keep their names. Per-style training data gives style profiles.
  - Needs human fingerings. Candidates: GuitarSet (hexaphonic recordings, string-level
    annotations; verify), DadaGP (GuitarPro tabs, gated), scottvr's own tabs.
  - The hard thresholds (the −1000 unplayable span, the sweet-spot window) stay constraints
    rather than learned weights.
  - **First steps, useful even without an optimizer** (discussed 2026-09-27):
    1. **Audit** each score term: its feature, its unit, what it trades against.
    2. **Express the defaults as exchange rates**, with `movement_penalty` = 1 "fret of hand
       travel". The Viterbi fingering depends only on weight *ratios*. Today a string switch
       = 1.7 frets of travel, a fret above the sweet spot = 1.7 (17 on the low strings), a
       fretted-open note = 6.7, chord span = 33 per fret.
    3. **Which weights are structural?** (scottvr, 2026-09-28) Some weights may matter to the
       scorer's basic behavior whatever the player's taste or the genre; others are
       preferences. Find out which, from the code. **Also quantify whether the Viterbi mapper's
       improvement over the old greedy one generalizes.** The docs audit found that under
       Viterbi, the wiki's Asturias steps 2–5 no longer show the problems that the long
       command line was built to fix, and the step-5 flags already give nearly the final tab.
       Measure it across many songs (e.g. the mapper's score per note and hand travel, greedy vs
       Viterbi, on a corpus sample), not on one piece.
    4. **Separate the kinds of knob.** Trade-offs (search log-ratios) are different from
       priorities disguised as big numbers: e.g. `--let-ring-bonus 210` = 70 frets of travel,
       i.e. "ringing always wins". Priorities are a lexicographic ordering, better expressed
       as one. Structural settings (sweet-spot bounds, unplayable span, flags) are discrete.
       `barre_bonus`/`barre_penalty` multiply the same count, so only their difference
       matters: one knob, not two.
    5. **Sensitivity sweep**: vary one knob at a time on a few tricky songs and count the
       *distinct* tabs.
    6. **Open strings** (found by F03's `--analyze`, 2026-09-27): with default weights an open
       string scores no better than a fretted note in the sweet spot. An open-G riff scored
       the same in OPEN_G (all open) as in OPEN_E (a barre at fret 3). `--prefer-open` only
       penalizes fretting a pitch that exists as an open string.
  - **Profile finder**: the tab is piecewise constant in the weights. So:
    1. sample settings widely (log scales, flags included);
    2. decode each and drop duplicate tabs (a few dozen distinct tabs expected per excerpt;
       check);
    3. scottvr ranks tabs, not settings, or picks between pairs;
    4. take the setting at the centre of the winner's region as the style profile, saved as a
       `.gtrsnipe` profile file.

    Richer options: preference-based Bayesian optimization, or the structured perceptron
    trained on his picks (no community tabs to curate). Check that each profile transfers to
    a second song of the same style.

### M01, first pass (2026-11-04): the audit from the code, and the sweep

**The tool.** `gtrsnipe-research sweep SONG... [--probes] [--sample CORPUS:N] [--knobs a,b]
[--tabs DIR] [--json FILE] [-v]` varies one mapper knob at a time over a ladder (weights at
0, 1/8 … 16 × the default; zero-default bonuses at 0, 1, 3 … 3000; the integer and flag
knobs over their ranges), fingers each input under each setting, and counts the *distinct*
tabs. `--tabs` writes every distinct tab out, so the judging is done on tabs, not weights.
`--probes` adds seven constructed passages, one scorer question each. The sweep also checks
that doubling every weight leaves every tab unchanged (it does: only the ratios decide) and
counts fingerings chosen past `unplayable_fret_span`.

**The exchange rates, read off `_score_fingering` with hand travel as the unit.** They are
the defaults restated, not a proposal; any one knob could be the unit. Rounding them to
whole frets isn't a scaling question (5/3 stays 5/3 at any scale): it means rounding the
defaults themselves, which the sweep can then check for changed tabs.

| knob | default | applied per | in frets of travel |
|---|---|---|---|
| `movement_penalty` | 3 | fret the *average* fret moves between fingerings | 1 (the unit) |
| `string_switch_penalty` | 5 | string entering or leaving the set used (a single-note switch counts **2**) | 1.7, so 3.3 per single-note switch |
| `high_fret_penalty` | 5 | fret the average sits above the sweet spot | 1.7; × 10 when a low string is used |
| `fretted_open_penalty` | 20 | fretted note whose pitch is an open string (`--prefer-open` only) | 6.7 |
| `fret_span_penalty` | 100 | fret of span inside a chord | 33 |
| `sweet_spot_bonus` | 0.5 | fingering whose average is inside the window | 0.17 |
| `let_ring_bonus` (Asturias: 210) | 0 | string of the previous fingering left free | 70 at the Asturias setting |
| the sentinel | 1000 | chord span past the limit (a flat **return**); diagonal span (subtracted) | 333 |

**Three modelling facts, from the code.** Hypotheses for the discussion, not verdicts:
scottvr's point stands that the open-string handling was deliberate in places (a sus shape
slid up the neck keeps its open B and E; `--ignore-open` exists for exactly that), and the
sweep, not a code read, says which knobs are wired to something.
1. *No hand, no fingers.* A fingering is one number, its average fret; movement is the
   difference of averages. Index on 5 then ring on 7 and a slide from 5 to 7 cost the same
   two frets. A hand-position state (where the index sits; notes within reach cost no
   travel) is the M06 question, not a weight.
2. *Open strings have a position in the movement term and not in the span terms.* The
   chord-span check drops them under `--ignore-open`, the diagonal check always drops them,
   the movement term never does: open E then fret 7 is seven frets of travel, and an open
   string in a chord pulls its average down.
3. *A string switch is counted by symmetric difference*, so a single note changing string
   costs two units, not one.

**The sentinel can't rank.** When no candidate fits the span limit, every candidate returns
the same flat -1000 and the mapper picks arbitrarily (first in sort order, then whatever the
path prefers), with the transition terms never consulted. Both mappers do it; the line dates
from the July 2025 refactor, so it is not a Viterbi regression. Where it bites:
- the sus-shape probe, x-5-7-7-0-0 slid to 7, 10, 12: with open strings counted, 0 of 108
  candidates fit 4 frets, and the chosen fingerings span up to 19 frets (A19 with e0); with
  `--ignore-open`, 6 fit and the tab is sane (span 2). One run of its seven chords takes
  13.7 s (the cubic inner loop; parked);
- Asturias v1's doubled unisons (G3 G3): the same pitch on two strings never fits 4 frets,
  so all 12 candidates tie at -1000 and fret 10 on the A string beats fret 5 on the D string
  because the flat return discarded the movement cost that would have ranked them. `--dedupe`
  (as the wiki's final command does) removes the chord; `--ignore-open` fixes the open case.
- Options to discuss: subtract the sentinel instead of returning it (least-bad ranking, as
  the diagonal check already does); or keep the hard rule and make the no-fit case explicit
  in the tab (a marker, a warning naming the chord), since "no fingering fits your hand" is
  information the player wants.

**The sweep on three real pieces** (the wiki's Mr Crowley organ intro, 168 notes; Asturias
v1, 44; the full Bach prelude, 654), distinct tabs per knob over its ladder, pooled:

| knob | verdict | live | distinct (sum) | nearest change from the default |
|---|---|---|---|---|
| `movement_penalty` | live | 3/3 | 15 | ×½ (all three), ×2 (two) |
| `string_switch_penalty` | live | 3/3 | 17 | ×2 (all three), ×½ (two) |
| `fretted_open_penalty` | live | 3/3 | 15 | ×½ (all), ×2 (two) |
| `let_ring_bonus` | live | 3/3 | 17 | 1 to 10 |
| `sweet_spot_low` | live | 3/3 | 10 | 2 |
| `prefer_open`, `diagonal_span_penalty`, `optimizer` | live | 3/3 | 6 each | the flag |
| `sweet_spot_high` | live | 2/3 | 12 | 9, 15 |
| `fret_span_penalty` | live | 2/3 | 7 | 0 (Crowley), ×4 (Asturias) |
| `ignore_open` | live | 2/3 | 5 | the flag |
| `barre_bonus` / `barre_penalty` | rare | 1/3 | 5 / 7 | 30 / 10 (Crowley only) |
| `high_fret_penalty`, `low_string_high_fret_multiplier` | rare | 1/3 | 4 | 0 (Bach only) |
| `unplayable_fret_span` | rare | 1/3 | 5 | 3, 5 (Asturias only) |
| `sweet_spot_bonus` | **dead** | 0/3 | 3 | never |

On the six fast probes the picture is the same: `sweet_spot_bonus`, `barre_bonus`,
`unplayable_fret_span` and `diagonal_span_penalty` never change a probe; `movement_penalty`,
`string_switch_penalty`, `fretted_open_penalty`, `let_ring_bonus`, `sweet_spot_high` and
`prefer_open` change four of six. Readings:
- `sweet_spot_bonus` at 0.17 frets decides nothing anywhere. Dead knob.
- The trade-off knobs (`movement`, `string_switch`, `fretted_open`) are live and flip
  within ×2 of their defaults, i.e. the defaults sit near a boundary, which is what
  hand-balancing one failure at a time would produce.
- `let_ring_bonus` flips at 1–10 points on real pieces, so the Asturias 210 is a priority
  (70 frets of travel: "ringing always wins"), not a trade-off.
- `high_fret_penalty` only matters at 0 on these pieces; the ×10 low-string multiplier
  likewise. Whether they matter on pieces that live above the 12th fret is untested.

**Replicating the wiki, both mappers** (each documented command run on the documented tab's
own notes, `--refinger`; "same" = notes with the wiki's string and fret):

| case | Viterbi | greedy | unplayable chosen |
|---|---|---|---|
| Mr Crowley, `--sweet-spot-high 8` | 138/168 | **168/168** | 0 |
| Asturias v6, the final flag set | **45/45** | **45/45** | 0 |
| Asturias v1 notes, defaults | 30/44 | 32/44 | 2 (the unisons) |
| Asturias v6 notes, defaults | 26/45 | 26/45 | 0 |

So the documented commands still do what the pages say, greedy reproduces the Crowley tab
exactly (the 30 Viterbi differences are the docs-audit's known "22 of 70 chords"), and v0.2's
*default* Asturias tab is not reproducible by either mapper today (the defaults or the
candidate order have changed since; the two unison chords are unplayable-chosen in both).

**For the discussion with scottvr** (his call, not mine):
1. The sentinel: rank the no-fit case, or flag it, or both?
2. Open strings in the movement term: a position, or none? His sus-shape example argues the
   chord keeps a position while its open strings don't; a "last fretted position" rule gives
   exactly that.
3. `sweet_spot_bonus`: delete, or make it big enough to mean something (it is the only term
   that *rewards* being in the window; the penalty above the window is what works today).
4. `barre_bonus`/`barre_penalty`: one knob, signed.
5. Round the defaults to whole-fret rates and re-run the sweep to see what changes.
6. M02 is already in the table: `optimizer` is live on every input. The corpus comparison
   (`--sample nottingham:N`, Lakh for chords) is one command away, once the cubic loop is
   fixed or the sample avoids dense chords.

Raw results, the 81 distinct tabs and the replicated tabs are in the session scratchpad
(`sweep/real.json`, `sweep/tabs/`, `repro/`); they stay off the repo because the wiki tab
and the corpus pieces are not ours to ship.

## M03: a tab difficulty measure

- **A tab difficulty measure** (scottvr, 2026-09-30). Tab sites sort by difficulty labels
  that uploaders assign by opinion. Objective *complexity*, measured from the tab, could serve
  as a proxy for difficulty, which is complexity relative to a player.
  - Ingredients we already have: F06's discomfort and F03's per-note mapper score, hand
    travel and big jumps (the naive-vs-gtrsnipe comparison), fret range. To add: notes per
    second at tempo, stretches, chord changes per bar, barres, techniques, position shifts.
  - Validation: expert-graded repertoire (graded exam syllabi such as Rockschool, Trinity,
    ABRSM-style guitar grades) gives an ordering to test against (rank correlation), which is
    better ground truth than uploaders' labels. Tab-site labels could be a second, noisier
    check.
  - A literature search comes first: automatic difficulty estimation exists at least for
    piano, and some for guitar. Relates to the weights audit's "whole-tab difficulty
    meta-score" and "difficulty before transcription" above.

## M04: search for an easier tuning

- **Search for an easier tuning than the one assumed** (scottvr, 2026-10-02). Not only "is
  standard the easiest?" (probably usually), but the specific case of a piece traditionally in
  an alternate tuning, where some non-traditional tuning might score easier or less complex.
  - Most pieces exist: F03's `--analyze` already ranks the *named* tunings by the mapper's
    score; F04's string physics says which tunings a strung guitar can take; the homograph
    solver already searches per-string retunes.
  - New: search the space of tunings, not just the list, e.g. each string within a few
    semitones of the traditional or standard tuning, by local search on the mapper's score,
    rejecting tunings that overload a string, and charging a little for each retuned string.
  - Report the traditional tuning's score next to the best found, and say what was gained.
  - Calibration: "easier" isn't "better". A piece's tuning also sets its drones, ringing open
    strings and resonance (often the reason it's in that tuning), so the output is an option
    for a player, not a correction. Pairs with the difficulty measure below and with the
    optimizer-objectives entry.

## M05: optional notes

- **Optional notes: let the user change *what* gets tabbed, not just where** (scottvr,
  2026-09-27). Today every sounding pitch must be fingered. If a chord needs a barre, there's
  no way to ask for a 3-string partial voicing. Players who want partial shapes (beginners,
  campfire style, funk/rock rhythm) need this, and it is broader than C02 (open voicings).
  Design notes (Claude):
  - **Simple knobs:**
    - `--max-chord-notes N`: keep the top N notes (or the N most essential);
    - a voicing style: `top3`, shell (root/3rd/7th), power (root/5th);
    - existing relatives: `--dedupe` and `--mono-lowest-only`.
  - **Principled version: every note gets a *drop cost* from its musical importance**,
    and the Viterbi mapper may omit a note when fingering it costs more.
    - Doubled octaves and 5ths are cheap to drop; 3rds and 7ths are expensive; the melody
      note is never dropped.
    - The chord identifier (`gtrsnipe-chords`) already knows which tone is which.
    - One knob, the drop cost scale, trades faithfulness against ease.
    - This fits the weights audit's exchange-rate units: "I'd drop a doubled root rather
      than move 5 frets".
  - Report what was dropped, the way the homograph report discloses its liberties.

## M06: a hand profile

- **A hand profile: which fingers are available** (scottvr, 2026-10-03). Accessibility, not
  style: a player missing a fingertip, or who avoids the ring finger for any reason, should get
  chord shapes and fingerings their hand can make (e.g. `--fingers 1,2,4`, or a profile).
  - Chord shapes: `open_positions` already counts fretted strings; with a profile it would
    assign real fingers (index barre allowed or not) and reject shapes needing a missing one.
  - Tabs: the mapper's span and movement costs assume four fingers; a profile would narrow
    the playable span and penalize stretches the hand can't make.
  - Natural companions: the "optional notes" entry (top-three voicings, shells, power
    chords; scottvr's "funk" and, jokingly, "Iommi factor" modes) -- all chosen compromises,
    each disclosed, never silent.

## M07: simplified "beginner's version" tabs

- **Simplified "beginner's version" tabs** (scottvr, 2026-10-03). The constraints being built
  for chords (open shapes, a hand profile, optional notes such as top-three voicings) could
  constrain a whole tab, giving a version of a complex tab that isn't exact but is enough for
  someone just learning to play.
  - The same machinery: the mapper with the hand profile's limits; drop costs by musical
    importance (the "optional notes" entry: keep the melody and the bass, drop doublings and
    inner voices first); open shapes where chords occur.
  - Fidelity stays the default, as with `--chart-voicing source`. A simplified tab must say so
    in its header and list what it changed (notes dropped, octaves moved), the way the
    homograph report discloses its liberties.
  - Probably an easy feature once those pieces exist, but it likely depends on the
    complexity/difficulty measure (below) to know *what* to simplify, and by how much: revisit
    together with it and the hand profile.
