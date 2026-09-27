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
  - **First steps, useful even without an optimizer** (discussed 2026-09-27):
    1. **Audit** each score term: its feature, its unit, what it trades against.
    2. **Express the defaults as exchange rates**, with `movement_penalty` = 1 "fret of hand
       travel". The Viterbi fingering depends only on weight *ratios*. Today a string switch
       = 1.7 frets of travel, a fret above the sweet spot = 1.7 (17 on the low strings), a
       fretted-open note = 6.7, chord span = 33 per fret.
    3. **Separate the kinds of knob.** Trade-offs (search log-ratios) are different from
       priorities disguised as big numbers: e.g. `--let-ring-bonus 210` = 70 frets of travel,
       i.e. "ringing always wins". Priorities are a lexicographic ordering, better expressed
       as one. Structural settings (sweet-spot bounds, unplayable span, flags) are discrete.
       `barre_bonus`/`barre_penalty` multiply the same count, so only their difference
       matters: one knob, not two.
    4. **Sensitivity sweep**: vary one knob at a time on a few tricky songs and count the
       *distinct* tabs.
    5. **Open strings** (found by F03's `--analyze`, 2026-09-27): with default weights an open
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
- **Tab checker** (2026-09-27): `gtrsnipe --homograph their.tab reference.mid
  --homograph-rhythm sequence` already tells a right tab, a right-in-another-tuning tab, and a
  "wrong-wrong" tab apart (see README, "Checking a tab"). Possible follow-ups:
  - a friendlier `--check-tab REF` that lists *every* conflicting note and measure, not just
    the first bad string;
  - partial alignment, for tabs with a few missing or extra notes;
  - batch mode over many tabs of one song, e.g. to rank user-submitted versions.
- **`--min-note-length BEATS`**: drop notes shorter than a threshold, for MIDI from audio
  transcription (from P01, 2026-09-27). Optional: `--velocity-cutoff` is the existing cruft
  filter, and since P01 short notes stay short rather than being stretched.
- **Tab onset decoding wobbles at barlines and two-digit frets**: the wiki's steady-sixteenth
  tabs decode with gaps of 0.375–0.625 beats (seen in R05). Worth a look at how the parser
  counts barline columns and multi-digit frets.
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
