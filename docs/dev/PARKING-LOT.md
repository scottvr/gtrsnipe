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

Triaged again on 2026-10-05 (after step 3). Into the backlog: the open code bugs (B08–B22,
H08), the playability group (M01–M07), the tab checker (F07) and homograph comfort (R16).
Their design notes moved to [`NOTES-playability.md`](NOTES-playability.md). What follows
stayed parked.

## Ideas

- **More strings for homographs** (scottvr, 2026-09-27).
  - 7- and 8-string guitars: 7-string tunings and `--num-strings 7` already exist, and the
    solver's free mode allows up to 12 strings. Anchored/middle need an 8-string tuning and
    gauge set. Richness ≤ 7 or 8 widens eligibility.
  - "Ludicrous mode": a 12-string with all 12 strings tuned independently. Physical twist:
    fretting a course sounds *both* its strings, so each tab note becomes a dyad unless one
    string of the course is avoided. The model would need courses, not strings.
- **`--min-note-length BEATS`**: drop notes shorter than a threshold, for MIDI from audio
  transcription (from P01, 2026-09-27). Optional: `--velocity-cutoff` is the existing cruft
  filter, and since P01 short notes stay short rather than being stretched.
- **A flatwound suffix for `--string-gauges`** (from F04, 2026-09-30; scottvr's jazz-set
  example). Flatwound strings weigh more per gauge than the nickel roundwounds the physics
  is calibrated to (`WOUND_FACTOR` 0.83 of solid steel). An `f` suffix needs a real factor,
  calibrated against a maker's published flatwound tensions, not a guessed constant.
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
  - **A stricter estimate when it matters.** The profile method is right about nine times in
    ten. The usual errors are a fifth away or the relative key; the first and last bass notes
    and the final chord would catch many of them.
  - **Inversions of extended chords** (C9/E) aren't named: an extended name needs its root in
    the bass. Chord-chart diagrams for extended chords come from a fixed four-note voicing.
- **Learned weights and a profile finder** (from the scoring-weights notes, 2026-09-27; kept
  parked at the 2026-10-05 triage). A structured perceptron trained on human-fingered tabs, or
  sampling settings and letting a player rank the distinct tabs. Both wait for the weights
  audit (M01) and for human fingerings to learn from. Notes: [`NOTES-playability.md`](NOTES-playability.md).
