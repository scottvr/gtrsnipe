# Parking lot

Quick capture for new ideas. Write one or two lines each; there's no need to think them
through or start them. Nothing here is scheduled.

At each triage, every entry either moves into [`BACKLOG.md`](BACKLOG.md), the single list
of open work with a plan, or is declined, and is removed from this file. (This is part of
The Dull Protocol, described at the top of the backlog.)

Earlier entries (custom tunings, profiles, homographs, MIDI player defaults) were
triaged on 2026-09-26, and the step-2 entries (now B07, F06, R10–R13) on 2026-09-27. The
finished ones are in the CHANGELOG, the open ones are in the backlog, and the original
notes are in git history.

## Ideas

- **Homograph comfort: offer every compatible string to each interval class** (from F06,
  2026-09-27). Today a class may use only its assigned strings plus one spare, so the
  measured discomfort is an upper bound. For example, a plain transposition still costs
  0.57 points per note because all its notes sit on one string. Offering any string whose
  tuning fits the class would lower it. Also: under a comfort limit, middle mode is no longer
  a superset of anchored (its bigger pool pushes anchored placements past the budget).
- **More strings for homographs** (scottvr, 2026-09-27).
  - 7- and 8-string guitars: 7-string tunings and `--num-strings 7` already exist, and the
    solver's free mode allows up to 12 strings. Anchored/middle need an 8-string tuning and
    gauge set. Richness ≤ 7 or 8 widens eligibility.
  - "Ludicrous mode": a 12-string with all 12 strings tuned independently. Physical twist:
    fretting a course sounds *both* its strings, so each tab note becomes a dyad unless one
    string of the course is avoided. The model would need courses, not strings.
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
