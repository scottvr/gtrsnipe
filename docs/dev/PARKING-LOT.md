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
- **Before publishing the offset/structure material: finish what R03 left open** (scottvr,
  2026-09-29). R03 was a negative result, not a verdict, and we have tooling nobody else seems
  to have, so testing further is a contribution either way (with the code in the repo):
  - the §6 hypothesis: does low richness with high reuse mark sequences, echoes or
    call-and-response at a fixed interval? Needs labelled examples (e.g. motif/sequence
    annotations, or synthetic sequences as a sanity check);
  - the retrieval experiments R03 didn't run: an alignment-based baseline, the Janssen, van
    Kranenburg & Volk (2017) benchmark, phrase-level retrieval;
  - R12 (richness under its own optimal warping) belongs with these.
- **A flatwound suffix for `--string-gauges`** (from F04, 2026-09-30; scottvr's jazz-set
  example). Flatwound strings weigh more per gauge than the nickel roundwounds the physics
  is calibrated to (`WOUND_FACTOR` 0.83 of solid steel). An `f` suffix needs a real factor,
  calibrated against a maker's published flatwound tensions, not a guessed constant.
- **Computer-vision analogues** (scottvr's question, 2026-09-28: is there relevance to
  CV and image processing, e.g. total variation in image interpolation?). Claude's reading,
  from memory: *check every citation* (these belong on the R13 checklist).
  - **The offset statistics map onto image-regularization terms.** Read δ = b − a as a 1-D
    signal: S is the L0 gradient norm (the count of jumps; Xu, Lu, Xu & Jia 2011, "L0
    smoothing"), TV is the L1 gradient norm (the total variation of Rudin, Osher & Fatemi
    1992), richness is the palette size (the number of distinct levels), entropy is the
    histogram entropy. Being blind to transposition is being blind to a constant (DC) offset.
    "Shannon TV" (Abergel & Moisan, JMIV 2017, if remembered right) is TV computed on the
    band-limited interpolate; it doesn't apply to integer semitones, only perhaps to
    continuous pitch contours from audio.
  - **"Vocabulary vs. switches" has a name in CV.** Energy minimization with *label costs*
    (Delong, Osokin, Isack & Boykov, IJCV 2012) pays once per label used (≈ richness) plus a
    Potts term per label change (≈ S). Multi-model fitting (PEARL: Isack & Boykov, IJCV 2012)
    assigns each point correspondence to one of a few models, with a label cost for each
    model, classically fitting several *homographies*. The tab homograph is 1-D multi-model
    fitting: correspondences (aᵢ, bᵢ), models = constant offsets (a string's retune), at most
    N models, exact inliers. Layered motion (Wang & Adelson 1994) is the same idea for flow.
    Folded into the structure note's revision 3 (2026-09-29), which now presents vocabulary vs.
    switches as this known distinction, and into LITERATURE §6. Still open: verifying the
    citations (R13), and the algorithms (α-expansion with label costs for the fewest-offsets
    warping path, d_richness).
  - **A practical use: robust fitting for the tab checker.** RANSAC or PEARL over offsets
    would find the most likely tuning key for a tab with a few wrong notes and name the
    outliers (the wrong notes), instead of stopping at the first bad string.
  - **An analogy for the paper: hybrid images** (Oliva, Torralba & Schyns, SIGGRAPH 2006).
    One picture reads as two, depending on viewing distance (a spatial-frequency filter). The
    decoder is the key, as the tuning is for a tab.
- **Code bugs found by the docs audit (H06, 2026-09-28)**, see `DOCS-AUDIT.md`. Fixed
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
