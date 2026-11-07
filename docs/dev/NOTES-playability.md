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
[--pair A,B ...] [--tabs DIR] [--json FILE] [-v]` varies one mapper knob at a time over a ladder (weights at
0, 1/8 … 16 × the default; zero-default bonuses at 0, 1, 3 … 3000; the integer and flag
knobs over their ranges), fingers each input under each setting, and counts the *distinct*
tabs. `--tabs` writes every distinct tab out, so the judging is done on tabs, not weights.
`--probes` adds seven constructed passages, one scorer question each. The sweep also checks
that doubling every weight leaves every tab unchanged (it does: only the ratios decide) and
counts fingerings chosen past `unplayable_fret_span`.

**The exchange rates, read off `_score_fingering` with hand travel as the unit.** They are
the defaults restated, not a proposal; any one knob could be the unit. (The column divides
by `movement_penalty`: a 1.7 there is a string switch at the defaults, not a proposed
price for a fret of travel. That misreading started part of the discussion below;
scottvr, 2026-11-04.) *scottvr, same day: a string switch costing more than a fret of
travel is intentional. Staying on a fret, or moving by one, takes more effort from string
to string than the same move up or down one string. For some common patterns it is a wash,
and the prev / prev_prev terms, kludgy or not, tend to make it come out even; a penalized
string hop is unlikely to force an unwanted fingering or forbid a desirable one where a
player would call it even odds. Qualitative experience, not a measured claim; he is open
to constructed cases that test it.* The position-run and open-vs-fretted probes are the
closest existing cases: both flip when the switch rate drops to one fret (q5). Rounding them to
whole frets isn't a scaling question (5/3 stays 5/3 at any scale): it means rounding the
defaults themselves, which the sweep can then check for changed tabs.

| knob | default | applied per | in frets of travel |
|---|---|---|---|
| `movement_penalty` | 3 | fret the *average* fret moves between fingerings | 1 (the unit) |
| `string_switch_penalty` | 5 | string entering or leaving the set used (a single-note switch counts **2**) | 1.7, so 3.3 per single-note switch |
| `high_fret_penalty` | 5 | fret the average sits above the sweet spot | 1.7; × 10 when a low string is used |
| `fretted_open_penalty` | 20 | fretted note whose pitch is an open string (`--prefer-open` only) | 6.7 |
| `fret_span_penalty` | 100 | fret of span inside a chord | 33 |
| `sweet_spot_bonus` | 0.5 | fingering whose average is inside the window (a flat toll for leaving it; the penalty above is the graded one) | 0.17 |
| `let_ring_bonus` (Asturias: 210) | 0 | string of the previous fingering left free | 70 at the Asturias setting |
| the sentinel | 1000 | chord span past the limit (subtracted since 2026-11-04; was a flat **return**); diagonal span (subtracted) | 333 |

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

**The sentinel couldn't rank** (fixed the same day; see q1 below). When no candidate fit the
span limit, every candidate returned the same flat -1000 and the mapper picked arbitrarily (first in sort order, then whatever the
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
- Options discussed: subtract the sentinel instead of returning it (least-bad ranking, as
  the diagonal check already does); or keep the hard rule and make the no-fit case explicit
  in the tab (a marker, a warning naming the chord), since "no fingering fits your hand" is
  information the player wants. Both, as of 2026-11-04 (q1).

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
| `sweet_spot_bonus` | idle at the defaults | 0/3 | 3 | never (no lower edge, so no case) |
| `sweet_spot_bonus` with `sweet_spot_low` 4 | live | 3/3 | 13 | 0 (all three), ×2 (two): the default 0.5 is a working balance point |
| `high_fret_penalty` with `sweet_spot_high` 7 | live | 2/3 | 11 | ×½ and ×4 (Bach), ×¼ (Crowley) |

The verdicts are about the *defaults*, not the knobs ("idle" = no ladder value changed a tab
with every other knob at its default). A knob can be idle because its case never arises
there, so the sweep also runs some knobs in the context they were designed for (the `@`
entries: `sweet_spot_bonus@low4`, `high_fret_penalty@high7`, `barre_bonus@penalty10`).
scottvr's reminder (2026-11-04): find out why the fence is there before taking it down. The
sweet-spot edges were added so the bonus had a range to apply to; a player may set only the
high edge, only the low edge, or how much the window matters; and the barre pair is two
knobs on purpose, for the early user who wanted no barre shapes at all and would not have
thought to type a negative bonus.

On the six fast probes the picture is the same: `sweet_spot_bonus`, `barre_bonus`,
`unplayable_fret_span` and `diagonal_span_penalty` never change a probe; `movement_penalty`,
`string_switch_penalty`, `fretted_open_penalty`, `let_ring_bonus`, `sweet_spot_high` and
`prefer_open` change four of six. Readings:
- `sweet_spot_bonus` changed no tab on these three pieces at the defaults, and that is a fact
  about the pieces: none of them ever had an above-window candidate close to winning, so no
  size of bonus could show. The structure (corrected 2026-11-04, after I had wrongly called
  the bonus redundant with the penalty): an above-window fingering must overcome the bonus
  *plus* `high_fret_penalty` × its distance above the edge. The bonus is a flat toll for
  leaving the window, the penalty a graded one, and they complement each other: with the
  penalty small, a passage near the 19th fret goes to G17–G19 at bonus 0 and comes back to
  e8–e10 at bonus 5. A bonus of 1000 with no bounds set is a real preference ("never leave
  the neck below 12 whatever the movement saved"). With a lower edge the bonus is also the
  only term telling inside from below, which is why `sweet_spot_low` 4 makes it live on every
  piece here, and the default 0.5 then flips at 0 and at 1.0. Working as designed; scottvr
  was right about this from the start (the edges were added after the bonus for exactly this).
- The trade-off knobs (`movement`, `string_switch`, `fretted_open`) are live and flip
  within ×2 of their defaults, i.e. the defaults sit near a boundary, which is what
  hand-balancing one failure at a time would produce.
- `let_ring_bonus` flips at 1–10 points on real pieces, so the Asturias 210 is a priority
  (70 frets of travel: "ringing always wins"), not a trade-off.
- `high_fret_penalty` only matters at 0 on these pieces; the ×10 low-string multiplier
  likewise. Whether they matter on pieces that live above the 12th fret is untested.

**The sus-shape probe under the sweep** (x-5-7-7-0-0 slid to 7, 10, 12 and back; seven
5-note chords): at the defaults *every weight knob is dead*, because every candidate of every
chord returns the flat -1000 and the weights never get a vote. Only `--ignore-open`,
`unplayable_fret_span` 8 and `--optimizer greedy` change its tab. The sentinel doesn't just
fail to rank; it switches the whole scorer off for that chord. (Measured before the q1 fix;
after it, the probe's widest chosen span drops from 19 to 9 and the weights are live again.)

**Ablation pairs** (`--pair A,B`: distinct tabs of B over its ladder, at each value of A), on
the three pieces:

| A | B | reading |
|---|---|---|
| `sweet_spot_low` 0 → 2 … 12 | `sweet_spot_bonus` | 1 distinct at 0; 4–6 at 2–9 (Crowley, Bach), 2 (Asturias); back to 1–4 at 12 |
| `sweet_spot_high` 5 … 24 | `high_fret_penalty` | 7–8 distinct at 5, 4–6 at 7, 1–3 at 9, 1–2 from 12 up: the penalty is "rare" only because these pieces live below the 12th fret |
| `high_fret_penalty` | `low_string_high_fret_multiplier` | Bach: live (5 distinct) when the penalty is small, 2 at the default; Crowley, Asturias: never |
| `diagonal_span_penalty` | `let_ring_bonus` | 4–7 distinct off, 5–8 on: the t-2 term adds a tab or two but let-ring is live either way |
| `barre_penalty` | `barre_bonus` | Crowley 2–4 at every penalty; Asturias and Bach 1 everywhere (no barres to find) |
| `ignore_open` | `unplayable_fret_span` | Asturias only (the unisons): 3 distinct with opens counted, 2 without |

So "dead at the defaults" has two causes to tell apart: a term with no case to decide
(`sweet_spot_bonus`, `high_fret_penalty` on low-neck pieces), and a term that is too small
to decide its case (none found yet). A full ablation, every pair, is 17 × 16 / 2 grids of
up to 81 runs; on these pieces that is about ten minutes, so it can simply be run.

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
1. The sentinel: rank the no-fit case, or flag it, or both? *scottvr (2026-11-04): an obvious
   oversight; for the pieces he was transcribing any choice happened to be as good as another,
   so nothing stood out, but it is not something to leave to chance. Both: rank, and tell the
   player, so that if the fingering still sucks they know the mapper had no real choice. The
   message can live behind the existing debug flood or use a proper level; the verbosity
   structure (today it is everything-or-nothing short of exceptions) is a parking-lot note.*
   Done the same day: the scorer subtracts the 1000 and keeps scoring, so the least bad
   fingering wins on the other terms; both mappers then warn, at the default verbosity, naming
   the chord, the beat, the limit and the shape chosen ("No fingering of the chord at beat
   3.125 (G3 G3) fits within 4 frets; chose the least bad: S3:F0 S4:F5 (span 5)."). Measured
   on the three real pieces, Asturias v6 and the seven probes, both optimizers (22 tabs): 18
   unchanged; Asturias v1 changes 4 of 44 notes (the two unisons go from G0 A10 to G0 D5,
   widest span 10 to 5); the sus probe changes 20 of 35 (widest span 19 to 9, from the A19 e0
   nonsense). Nothing else moved. Tests: `tests/unit/test_mapper_scoring.py`.
2. Open strings in the movement term: a position, or none? His sus-shape example argues the
   chord keeps a position while its open strings don't; a "last fretted position" rule gives
   exactly that. *scottvr (2026-11-04): deliberate, and the intent was exactly the pull-down.
   The term is a thumb on the scale, the cheapest one that needs no extra flag: "avoid a
   big jump to an open shape from a fretted chord, but avoid it less the more of those
   strings you are already playing open." An A barre at the fifth fret moving to open E
   should be tipped toward something closer harder than an open Asus4 making the same
   move. He hasn't run a transcription with debug on in a long while and won't swear it
   holds in every case; there was no functional test for it.* The numbers from
   `_score_fingering` say it does what he intended, by construction: 5-7-7-6-5-5 (average
   5.83) to 0-2-2-1-0-0 (0.83) is 5.0 frets, 15 points at the default; x-0-2-2-3-0 (1.4) to
   the same open E is 0.57 frets, 1.7 points. Each open string already held pulls the
   pre-move average toward the open shape. The cost of the rule is the single-line case
   (open E then fret 7 is seven frets each way); a "last fretted position" rule would keep
   his chord behaviour and drop that, at the price of a state. *scottvr: yes, working as
   designed and justified as it stands, for now, until better ways are sorted out (M06).*
   The one undesirable effect, measured on the open-pedal probe: at the defaults the pedal
   E is fingered at B5 on every beat and never open, because each open E is a trip to the
   nut and back (seven frets each way); with `movement_penalty` 0 the mapper takes e0 every
   time. Both tabs sit in one position and both are playable, so it is a preference, not
   an error, and the asymmetry is the thing to remember: inside a chord the rule rewards
   open strings, inside a fretted line it avoids them. `tests/unit/test_mapper_scoring.py`
   pins the two chord numbers and the line case. *scottvr, same day, on that side effect:
   this is the Asturias family of problems. `let_ring_bonus` and then the diagonal span
   were added in the wiki walk-through by analyzing a failure and answering it with a
   parameter, and they worked. 0-7-0-7-0-7 on one string is easy to play but not exactly
   this; Bach is the other direction, too much on one string. `--single-string` only half
   addresses it, built for an Angus Young lick or the Eruption tremolo, not a whole piece.
   A weight instead of a boolean, or a second boolean, would resolve it and seems kludgy:
   infinite tweakability ends with every song needing a profile, and someone who knows
   enough to write that profile could transcribe by hand. Fine for now; it goes under M06
   as the case a hand-position state should absorb, not a knob.*
3. `sweet_spot_bonus`: working as designed. *scottvr (2026-11-04): the two forces (a flat toll
   for leaving the window, a graded one per fret above it) go in the README beside the three
   related options and in `--help`, not the wiki, which few people find and which he may
   retire in a docs restructure (parked, with a tiered ffmpeg-style `--help`).* Done the same
   day: README option text and the `--sweet-spot-bonus` help.
4. `barre_bonus`/`barre_penalty`: two knobs on purpose (above); only the difference reaches the
   score, which the help text could say. Nothing to change.
5. Round the defaults to whole-fret rates and re-run the sweep to see what changes. *scottvr
   (2026-11-04): go.* Measured on the 22 tabs (three real pieces, Asturias v6, seven probes,
   both optimizers), against the defaults scaled to `movement_penalty` 1 (5/3, 100/3, 5/3,
   20/3, 1/6), which fingers every tab the same except one: Bach under Viterbi moves 26
   notes between two tabs that score *identically* under both configs, a tie broken by
   float noise, so Bach has families of tabs the scorer cannot tell apart (noted; nothing to
   do). Each change below was scored both ways under its own config to separate ties from
   real changes:
   - `high_fret_penalty` 5/3 to 2: nothing. `fret_span_penalty` 100/3 to 33: one Crowley
     note, a tie. `fretted_open_penalty` 20/3 to 7 (only matters under `--prefer-open`):
     nine Bach notes, real but 0.3 points.
   - `string_switch_penalty` 5/3 rounded up to 2: real on Crowley/Viterbi (14 notes) and
     Asturias v6/greedy (4); the bonus value (1/6, 0 or 1) changes nothing on top, as
     expected with no lower edge.
   - truncated to 1 instead (scottvr's question): a switch then costs exactly one fret, and
     eight tabs flip, all real: Bach +96 switches under Viterbi (92 notes), Asturias v6 +16
     (8 notes), the position-run and open-vs-fretted probes too. That is the behaviour the
     intentional 5-vs-3 is there to prevent (his note above the table).
   Decision: the originals are whole numbers already (3, 5, 100, 5, 20, 0.5); the fractions
   only appear in the frets-of-travel column. Nothing to round; q5 closes with no change,
   and the two tables above now carry the cost of each rounding should it come up again.
   *scottvr: no design notes survive and he won't claim intelligent design, but trial and
   error may be why the values are as large as they are: a fret at 3 instead of 1 leaves
   room for nuance, a switch at five thirds of a fret, in whole numbers.*
6. M02 is already in the table: `optimizer` is live on every input. The corpus comparison
   (`--sample nottingham:N`, Lakh for chords) is one command away, once the cubic loop is
   fixed or the sample avoids dense chords. *scottvr (2026-11-04): go.* Done the same day;
   results in the M02 section below.

### M02, first pass (2026-11-04): Viterbi vs greedy across five corpora

The greedy mapper now reports its path score under the same objective as Viterbi (the sum
of its chosen fingerings' scores), so the two are compared score to score, not by proxies
alone. `gtrsnipe-research optimizers --sample nottingham:100 essen:100 mtc-fs:100
lakh-clean:100 pop909:50` (seed 1, defaults, `--data` at the corpus root) reproduces this;
the run below used the same code paths from a scratch script. A jump is a change of
average fret of five frets or more. 450 tunes, 132,326 notes.

| corpus | tunes | notes | same tab | Viterbi better | worse | gain per note, mean (max) | travel g to v | jumps g to v | switches g to v | seconds g to v |
|---|---|---|---|---|---|---|---|---|---|---|
| Nottingham | 100 | 10,385 | 7% | 93% | 0% | 0.35 (1.30) | 2.09 to 2.02 | 605 to 594 | 2,228 to 2,202 | 0.3 to 0.9 |
| Essen | 100 | 5,027 | 20% | 77% | 0% | 0.29 (1.40) | 1.69 to 1.64 | 217 to 210 | 1,188 to 1,124 | 0.1 to 0.5 |
| MTC-FS | 100 | 7,522 | 25% | 74% | 0% | 0.32 (2.47) | 1.78 to 1.72 | 449 to 436 | 1,584 to 1,564 | 0.2 to 0.7 |
| Lakh clean | 100 | 92,888 | 1% | 99% | 0% | 0.41 (3.78) | 2.28 to 2.16 | 10,482 to 9,320 | 83,644 to 82,758 | 14 to 734 |
| POP909 | 50 | 16,504 | 12% | 88% | 0% | 0.29 (1.09) | 1.84 to 1.85 | 901 to 1,037 | 3,942 to 3,310 | 0.8 to 6.2 |
| all | 450 | 132,326 | 13% | 86% | 0% | 0.34 (3.78) | 1.95 to 1.88 | 12,654 to 11,597 | 92,586 to 90,958 | 16 to 743 |

What it says:
- **The improvement generalizes, and it is never a loss.** Viterbi is worse on no tune (it
  can't be: first-order Viterbi is exact on this objective at the defaults, with the t-2
  term off), equal on 13%, better on 86%. The mean gain is a third of a point per note, a
  ninth of a fret of travel per note at the defaults; the median per corpus is 0.18 to
  0.36. The largest gains are on long Lakh melodies (3.8 per note on one 489-note tune).
- **The proxies follow the objective, mostly.** Travel and big jumps fall by 4% and 8% over
  the set, switches by 2%. POP909 is the exception: Viterbi makes *more* big jumps there
  (1,037 against 901) and the same travel, while cutting switches by 16%: the objective
  prices a switch at five thirds of a fret, so on those tunes it bought fewer switches with
  more travel. "Fewer big jumps" is therefore not a property of the optimizer; it is a
  property of the weights, which Viterbi merely optimizes better. M03's difficulty
  measure, not M02, is where a jump count belongs.
- **Time.** On melodies Viterbi costs three to five times greedy (a second a tune at most).
  Lakh's dense tunes are where the cubic inner loop (parked) bites: 734 s against 14 s over
  100 tunes, 187 s on one 4,032-note tune.

Raw results, the 81 distinct tabs and the replicated tabs are in the session scratchpad
(`sweep/real.json`, `sweep/tabs/`, `repro/`); they stay off the repo because the wiki tab
and the corpus pieces are not ours to ship.

### Hand position (2026-11-07): scottvr's note, and the index-finger proxy measured

**The note** (scottvr, a phone note found and copied to
`docs/note-scoring-hand_on_neck_position.txt`; prompted by DOCS-AUDIT WK-5, "`--movement-penalty`
is per fret the hand's average position moves"). The points, in his order:
1. Hand position changes only between notes, never inside a note or chord. A chord's average
   fret is a center point, not a change; if a center is wanted at all it should be the median.
2. The hand is where the index finger is. The forearm passes under the neck, the wrist bends
   to bring the fingertips down onto the face of the neck, so the index finger is a proxy for
   the wrist and the hand is fixed to the wrist. Reach to higher frets is governed by fret
   span, and the span settings exist for hand size; both point at the lowest fretted fret as
   the position, not the mean.
3. This only matters once scoring considers hand position. Movement is scored today from
   prev and prev_prev by fret arithmetic, not by hand position except through that average.
   Not all increments are alike: A major as a full barre at 5 (5-7-7-6-5-5) to B at 7
   (7-9-9-8-7-7) moves the hand two frets with the shape unchanged; it is easy for an
   experienced player, as easy as a single-string 5-to-7 slide, harder than a hammer-on.
4. The right transition cost is probably: how far the shape changes (zero for the barre
   slide; one finger lifted for A to A minor), how far the hand moves (two frets there), and
   the chord's complexity, because keeping a hard shape together while moving it is harder,
   likely scaling with complexity, probably multiplicative rather than additive, possibly on
   a log scale. The difficulty of the barre slide may not be exactly zero, only negligible
   until the shape is complex enough.
5. Direction may matter: the under-and-around routing of the forearm means wrist stress
   changes differently toward the nut and toward the bridge. Both ends are harder; how much
   is player dependent. One sweet spot for single notes and chords is probably enough, but
   write it down when it is decided.
6. The Mr Crowley intro, full chords with single fretted notes between them, is the script
   to walk through if hand (neck position) scoring and finger scoring turn out to be two
   things.

**What Claude knew, and didn't.** Fact 1 of the M01 audit already says it from the code: a
fingering is one number, its average fret, there is no hand and there are no fingers, and a
hand-position state ("where the index sits; notes within reach cost no travel") is the M06
question. WK-5 is a statement about the code, and the code never moves a chord inside
itself: the average is used only in differences between consecutive fingerings (the movement
term) and in the sweet-spot test (where on the neck a fingering sits). So point 1 was
understood, and the audit's wording is right. Points 2, 4 and 5 were new: the anatomical
argument for the index finger (not "the lowest fret" as a convenience but the wrist's proxy,
with reach extending upward from it only), the nut-side discomfort as a separate thing from
the bridge-side one, and the multiplicative complexity scaling. Without the note Claude would
have reached for the mean or for the fret interval, with reach counted symmetrically.

**Measured** (`runs/hand-position-2026-11-07/handpos2.py`, defaults, Viterbi): three rules
for a chord's position in the movement and sweet-spot terms, with single notes scored as
shipped so that the open-string behaviour decided in q2 is untouched: the mean (shipped), the
median, and the lowest fretted fret ("index", all-open counted as the nut). Changed notes
against the shipped tab:

| piece | notes | median | index | why |
|---|---|---|---|---|
| Mr Crowley (wiki) | 168 | 22 | 14 | the fretted line between chords moves to the next string down, see below |
| Asturias v1 | 44 | 0 | 3 | an open B before a G4+B0 chord gets fretted at G4 (a tie under the mean, broken toward the chord's index) |
| Asturias v6 | 45 | 0 | 0 | |
| probe: sus-slide | 35 | 18 | 4 | median: x-5-7-7-0-0 has median 5 and the open strings stop pulling the shape toward the nut, the behaviour confirmed in q2 |
| probes: wide-chord, open-pedal | 22 | 0 | 0 | |
| 5 Nottingham tunes | 412 | 0 | 0 | single notes, by construction |

(A first version that also took open single notes to have no position changed 433 notes in
34 of 50 pieces; all of that is q2's open-string rule, not this question, and the script
`handpos.py` keeps it for the record.)

The Crowley bar is the case the note asked for. The intro opens x-5-7-7-6-x (index at 5,
mean 6.2), then the line E3 F3 G3, then 5-7-7-5-5-x (index at 5). Shipped: the line is
A7 A8 A10. Index rule: D2 D3 D5. Read as a hand: from the index at 5, A7 and A8 are within
reach (ring and little finger, no movement); A10 needs the hand at about 7; the hand goes
5 to 7 and back, two frets each way. The index proxy without a reach rule charges A7 two
frets and A10 five and so prefers to take the whole hand down to the second position, where
D2 D3 D5 sit under it. The mean got the better line by luck: 6.2 is near 7. So swapping the
mean for the index is a regression on his own script piece, and the proposal that works is the
note's two halves together: position is the index finger, and notes within the span above
it cost no travel. That is the hand-position state of fact 1 and M06, not a change of
statistic. The note's own examples under the two rules, transition cost at the defaults:
A to A minor (lift one finger) 0.5 against 0; A with the little finger added on e7 1.0
against 0; A to B as a barre slide 6 under both; open A (x-0-2-2-2-0) to the A barre 18.9
against 14.

**Where this leads** (his call):
1. Mean to index alone: no. Index plus reach: yes, as the M06 hand state. It stays a
   function of the previous and the current fingering, so first-order Viterbi stays exact
   (the landmine guard in `_score_fingering` is about t-2 only).
2. His transition formula fits the exchange-rate framing and is allowed to be multiplicative
   as long as it reads only prev and current. Shape change needs finger assignment, which
   nothing has today (M06 gives it); position change is the index delta beyond reach;
   complexity is span, fretted count and barre. One caution: `fret_span_penalty` at 100 per
   fret is charged on every onset already, the largest term in every real score (Crowley
   -6844 is mostly span), so a complexity factor on movement would count span twice unless
   span's own role is rethought in the same pass.
3. Direction. The code's sweet spot has only a bridge-side penalty (`high_fret_penalty`
   above `sweet_spot_high`; below `sweet_spot_low` nothing happens, which is why the sweep
   found that knob dead on real pieces). A nut-side twin is a one-line term; whether it is
   on is player dependent, so it belongs to a profile with the default off. Nothing measured
   says single notes and chords need different sweet spots.
4. Median: the worst of the three. It keeps the mean's center-point meaning and drops the
   open-string pull-down.
5. The Crowley intro stays the test piece for hand-versus-finger scoring; the bar above is
   the first case.

**Weights are path-dependent** (scottvr, 2026-11-07, on reading the mean/median/index numbers
above). The weights and options arrived one at a time, from a few to dozens quickly, each
tuned against the scorer as it stood that day. So a later weight that looks right today may
be an order of magnitude too heavy, or unneeded, only because of how an earlier one was set
before it arrived; and a change we expect to improve a tab can come out worse for the same
reason. Keep this in mind for every knob-tuning and ablation run in this phase: a
one-knob-at-a-time sweep (which is how the weights were born) can only confirm the path; the
pair sweeps (`--pair A,B`) and refitting the earlier weights when a term is changed are the
tests that can find it. *Claude:* the exchange-rate table in M01 is the map of today's path,
and `fret_span_penalty`'s double role (span charged on every onset, and again if complexity
scales movement) is the first candidate.

**Time-scaled movement cost** (scottvr, 2026-11-07, deciding Claude's question from the M03
survey: implement it, in the scorer as well as the measure; a gut feeling brushed off several
times during development, now possible because a gtrsnipe-generated tab's rhythm is exact
since v0.8.0). His statement: the penalty for a hand move rises as the time from the end of
note or chord 1 to the start of note or chord 2 falls; with a tempo the time is exact, without
one it is relative (MIDI reading has a default tempo, which will do); for tabs in the wild
without the gtrsnipe header the dash counts are not reliable, so the term is either invariant
to that or gated: automatic when the header says the layout is ours, a user flag otherwise.
*Claude, two notes for the design:* (1) Hori & Sagayama scale by the onset-to-onset interval;
the end-to-start gap he names is the time the hand is actually free, and it is zero for
every held or legato line (let-ring, the Asturias pedal), so the two measures differ exactly
where the scorer already has terms. Propose: onset-to-onset as the base with a floor, and
end-to-start measured alongside on the real pieces before choosing. *scottvr, same day:
end-to-start, and it does not conflict. A fretted note lasts exactly as long as the finger
stays on the fret, because lifting the finger ends the note; so the gap from the end of one
note to the start of the next is the time the hand truly has. Pedal notes are open or stay
in one position, so no movement is charged there whatever the gap.* Decided: end-to-start.
Where the gap is zero and the hand must move, the cost is real (the player cuts the note or
arrives late), which onset-to-onset would hide. Two consequences: the term needs note
*ends*, which MIDI has and **no tab does, ours included** (scottvr's correction, same day:
a tab's dashes give exact onsets and nothing else; a note's end is a reading convention,
legato to the next onset, staccato for the grid unit, or string mode until the string is
struck again, and the `// Lengths:` letters are note values, not ends). So on any tab the
end-to-start gap is undefined unless the layout gains an end mark (parked); and score-derived MIDI often
holds every note to the next onset, so a floor on the gap, not a zero, is the practical
minimum. *scottvr, later: since this contradicts the literature we searched, call the
departure out explicitly, with evidence: build both time bases and compare the tabs; where
they differ he plays them, which should settle it. For tabs in the wild he expects
approximate (dash-derived) to beat off, tested the same way.* (2) Backlog M08; the header
documentation is H09.

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
  - **Literature pass done 2026-11-07:** [`LITERATURE-difficulty.md`](../research/literature/LITERATURE-difficulty.md).
    Ten papers (six read in full), three on guitar. The ingredients it supports, the
    aggregation (means and the maximum, not totals), the validation (rank correlation
    against the RCM 2018 syllabus list, 413 pieces in nine levels, matched to free tabs)
    and the ceiling (MSE about 1 on a 10-level scale, at annotator noise) are in its §4.
    Two of the guitar papers define hand position as the index finger, as scottvr's
    hand-position note does; one scales the movement cost by the time available.

### M03, first cut (2026-11-07): the descriptors, and what the two time bases do

`gtrsnipe-research difficulty SONG... [--probes] [--sample CORPUS:N] [--both] [--reach N] [-v]`
(`gtrsnipe/research/difficulty.py`). A tab is read as onsets with the fingering it states (a
`.tab`) or the mapper's (anything else, or `--refinger`). Per onset: the index fret (lowest
fretted), the hand position, fingers down (the lowest fret's notes counted once, an index
barre), span, barre, the hand's shift in frets, the gap it had for it, the move rate in frets
per second, the shape change (string-fret pairs that differ), the inter-onset time and the
technique marks. Per tab: mean, quadratic mean and max of each; shifts per minute; position
range; chord and barre shares; repetitiveness (Lempel-Ziv on the shape sequence); notes per
second; and a provisional index with hand-set weights that nothing depends on.

**The hand model was necessary before any number meant anything.** With position = each
onset's lowest fretted fret (the plain index proxy), a jig at the fifth position showed 130
hand shifts per minute and a mean shift of 1.7 frets per note, because every note on another
fret counted as a move. The lazy hand of fact 1 (M01) fixes it: a shape anchors the index at
its lowest fret; a single note leaves the hand where it is while it lies within `reach` frets
above the index (default 3, four fingers on four frets), else the hand moves the least
distance that fits. That alone took the jig to 54 shifts per minute and Crowley from 60 to
17, which is what a player would count. `--reach 0` reproduces the proxy for comparison. This
is the first working piece of M06's hand state, on the measure side only; the scorer still
has no hand.

**The two time bases (M08), first numbers.** On every input we have, the end-to-start base
sits on its floor almost everywhere, so its move rate is just shift divided by the floor
(0.05 s): Crowley's mean move rate is 13.4 frets per second end-to-start against 1.7 onset to
onset, and its hardest move 80 against 12.8. The reason is the inputs, not the rule: a tab
states no note ends (its durations are the dash counts to the next note), the folk corpora
hold every note to the next onset (Nottingham releases 0.1% of notes early, Essen 3%, MTC
2%), and the mapper's probes are built that way too. The only corpus with real releases is
POP909 (67% of notes end before the next onset, median duration 0.76 of the interval); Lakh
has some (25%). So the M08 comparison cannot be run on tabs or folk tunes at all: it needs
POP909-like input, or MIDI of real performances, and even there the floor is the knob that
decides most of the difference. Two consequences: (1) for tabs in the wild the end-to-start
base is not merely approximate, it is undefined, and onset to onset is the only rule
available there; (2) the same is true of a gtrsnipe tab (scottvr's correction above: the
layout carries onsets, and ends are a reading convention), so an end mark in the layout is
what it would take, which is parked; H09 still holds for the onsets. The scorer-side comparison (where fingerings may differ) is
still to run, on POP909.

**Other things the first run shows.** The as-written tabs that predate v0.8.0 read with
approximate rhythm (`~rhythm` in the table), and their seconds are not to be trusted:
Asturias v1 comes out as 44 notes in 3.9 s, so every time-based descriptor of a tab without
`// Rhythm:` is unreliable, exactly the gating scottvr described. Crowley (as written, 70
onsets): 1.7 fingers down and a 0.8-fret span on average, 31% barres, hand never above 6.
Asturias v6: half a finger, no span, hand at 4 at most, repetitiveness 0.75. The provisional
index ranks the sus-slide probe hardest, which is right (wide shapes moving fast), and the
open-pedal probe at the bottom.

**M08, scorer side (2026-11-07).** Built: `--movement-time-base onset|end` multiplies the
movement penalty by `--movement-reference` (0.5 s) over the gap, floored at
`--movement-min-gap` (0.05 s); off by default. The gap is a per-stage constant, so Viterbi
stays exact (the landmine test now pins the fourth argument). The generators pass the
song's tempo; `--analyze`, the chord charts and the player still map at the default 120.
First run (`runs/m08-2026-11-07/`, 60 pieces, 25,497 notes; every input at tempo 120):

| input | onset base changes | end base changes | onset vs end differ |
|---|---|---|---|
| Mr Crowley (168 notes) | 18 | 4 | 18 |
| Asturias v1 / v6 | 0 / 11 | 0 / 11 | 0 / 0 |
| probes (7) | 3 pieces, 0–2 notes | same | position-run only |
| POP909 (18 tunes) | 13% of notes | 33% | on every tune |
| Lakh clean (15) | 14% | 20% | every tune |
| Nottingham (10) | 9% | 42% | every tune |

What it says so far: the onset base is a moderate thumb on the scale (a tenth of the notes
on melodies, a tenth of Crowley). The end base on inputs that hold every note to the next
onset (tabs, folk, the probes) is not a timing rule at all but a ten-fold movement penalty,
which is why it rewrites 42% of a Nottingham tune; only POP909 and Lakh, where notes are
released early, test what it is for. The G2-to-B2 unit case shows the intended effect: with
a quarter second the mapper takes the string switch instead of a four-fret move, and with a
whole second it moves again. The listening set for scottvr is in `runs/m08-2026-11-07/tabs/`
(Crowley, Asturias v6, two probes, four POP909 tunes, three tabs each) with a README on what
the comparison can and cannot show. Open: the reference and floor are guesses; the floor is
the whole story wherever notes are held, so a release-aware input (POP909, performance MIDI,
or a tab layout with an end mark) is the only ground on which end-to-start can be judged.

**Still to do in M03** (backlog): shape uncommonness (needs a reference corpus of shapes);
the graded set (RCM list matched to free tabs); the validation; and then the weights.

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
  - A hand *position* state belongs here too (M01 q2, 2026-11-04): open strings are free
    inside a chord and a trip to the nut inside a line, so an open pedal under a line at
    the fifth position gets fretted. Not a weight; a knob per case is the road to a profile
    per song, which scottvr declined.
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
