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
- **A flatwound suffix for `--string-gauges`** (from F04, 2026-09-30; scottvr's jazz-set
  example). Flatwound strings weigh more per gauge than the nickel roundwounds the physics
  is calibrated to (`WOUND_FACTOR` 0.83 of solid steel). An `f` suffix needs a real factor,
  calibrated against a maker's published flatwound tensions, not a guessed constant.
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
- **Optimizer profiles with different *objectives*, not just weights** (scottvr, 2026-09-30;
  e.g. "shred" vs "easy"). Profiles already change weights. What else could change:
  - **new features plus weights** (still today's objective): sweep-friendly shapes (one note
    per adjacent string), tapping and legato runs, position changes, open strings;
  - **a different aggregation, which no weighting can reproduce**: the mapper minimizes a
    *sum* of step costs; "minimize the hardest moment" minimizes the *maximum* step cost. The
    same Viterbi machinery does it with max in place of + (a bottleneck path, as for R07's
    largest jump J), or lexicographically: the easiest worst moment first, then the least
    total effort;
  - **longer memory for run-level preferences** (three notes per string, sweep shapes), which
    means a larger Viterbi state;
  - **the vocabulary-vs-switches split, for hand positions**: a cost at every position change
    (a Potts term) vs a cost per distinct position used over the song (a label cost, "stay in
    two positions").
  Pairs with the weights audit and the Viterbi-vs-greedy study above.
- **Keys: what v0.6.18 left out** (from C04/C05/F02, 2026-10-04).
  - **Key changes.** A song has one key. A piece that modulates is spelled in its opening or
    overall key throughout; MIDI key changes after the first are ignored. Following them
    needs a key per section (windowed estimates, with a cost for changing key).
  - **A `// Key:` line in tab headers**, so a tab carries its key through a round trip. Today
    a tab has no key and its chord names are spelled from an estimate. (It would change every
    tab's header, so it needs the golden cases checked.)
  - The fallback MIDI reader (py-midi) doesn't read the key signature.
  - **A stricter estimate when it matters.** The profile method is right about nine times in
    ten. The usual errors are a fifth away or the relative key; the first and last bass notes
    and the final chord would catch many of them.
  - **Inversions of extended chords** (C9/E) aren't named: an extended name needs its root in
    the bass. Chord-chart diagrams for extended chords come from a fixed four-note voicing.
  - `--transpose` still runs after the range filter (see the code-bugs entry below).
- **Code bugs found by the docs audit (H06, 2026-09-28).** Fixed
  already (v0.6.10): the six tunings `--tuning` rejected; the inverted or off-by-one help
  texts; and `--stem-track`, which crashed on every run since v0.3.0 (a NameError) and never
  mapped guitar to the "other" stem for 4-stem models. Still open:
  - `--bass` overrides any `--tuning`, including `BASS_DROP_D`.
  - `player/clock.py` is dead code (nothing imports it).
  - Viterbi tests the design doc promised but that don't exist: an exact-tie test, a test of
    the second-order "landmine guard", and a `hard_enum_cap` test.
  - `map_multi_string` returns early (no groups, no path) without resetting
    `last_path_score`, so a reused mapper keeps the previous value. Harmless today: every
    caller builds a new mapper.
  - The player's help overlay omits `home`, `enter` and `p`.
  - Errors exit 0: `converter.py` logs "An error occurred" but returns status 0, so scripts
    can't tell a failed conversion from a good one.
  - `gtrsnipe-research profile`, when phrases don't align, suggests `--homograph-subdivide`
    (the message comes from the shared homograph code); its own flag is `--subdivide`.
  - `--analyze` on a tab input ranks the tab's own `// Tuning:` header as an extra
    "CUSTOM E2,A2,D3,G3,B3,E4" row even when it is a named tuning (STANDARD then appears
    twice, and "18 of 18 tunings" counts it). A long CUSTOM name also breaks the column
    alignment. Found in the README trueing pass, 2026-10-03.
  - `gtrsnipe-chords` prints "Could not find a playable fingering…" warnings from its
    register search even when the sheet comes out fine.
  - `gtrsnipe-play` with a missing file shows a traceback instead of a clean error.
  - The converter prints both "Successfully saved to X" and "Successfully saved X".
  - `--tuning PIANO` always fails ("can only be used with MIDI output"), even with
    `-o x.mid`: the check is unconditional (since at least v0.2.2).
  - `--transpose` runs after the range filter and `--normalize-pitch`: notes that would fit
    after transposing are dropped first, and transposed notes can fall out of range (the
    v0.2.0 wiki's bass recipe, `--transpose -12` with BASS_DROP_D, hits this).
  - `--mono-lowest-only`'s help ("force monophonic output") overstates: it affects ASCII tab
    rendering only, and keeps the note on the lowest string.
  - (`--play` on a `.tab` re-fingers it: that's backlog B05.)
