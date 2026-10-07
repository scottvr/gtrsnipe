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

On this (private) line the same triage also moved the two composing ideas into the backlog
(R17, R18) and closed the computer-vision entry: its content is in the structure note
(revisions 3 and 4) and LITERATURE §6, and its citations are checked under R13.

2026-10-07: "tabs that keep time" left the lot for the backlog as F08, after a discussion and
four sample layouts. The agreed design, its history and the measurements are in
[`SPEC-tab-rhythm.md`](SPEC-tab-rhythm.md).

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
- **Survey: how do tabs in the wild state their tuning?** (scottvr, 2026-10-07; a mental
  to-do of his, raised when he worried that gtrsnipe's own `// Tuning:` line undercuts the
  homograph argument). What to count on a sample of third-party tabs (kept local, as R14):
  - string labels at the start of the lines: present or not; letters or nothing;
  - whether the labels are the tuning or just string names (a drop-D tab labelled E);
  - an explicit tuning statement, a capo statement, or neither.
  - Why it matters (Claude): the published claim is that ambiguity is real "for a tab
    stripped of its tuning". How often a real tab is in that state is the empirical half of
    it. And the convention fills the gap: Wright's 1995 guide says "TAB will tell you what
    tuning the piece is in. If this isn't given explicitly, assume normal tuning"
    (<https://www.classtab.org/tabbing.htm>). So the objection to meet is not "your tool
    writes the tuning" but "convention supplies one when the text doesn't". gtrsnipe writing
    the key is the argument made visible, not a counterexample: the staff alone doesn't
    determine the notes, so the tool has to say which key it means.
  - Pairs with R14 and with `--omit-comments` / `--homograph-neutral` (the bare text).
- **Key changes: how many keys vs how many changes** (scottvr's question, 2026-10-04: do the
  offset measures have a role in key-finding, e.g. the correlation vs Euclidean gap?). Claude's
  reading; nothing here was searched in the literature.
  - *Not directly.* The offset measures need two note sequences aligned note for note;
    key-finding compares one unordered pitch-class histogram with a template. And the
    correlation/Euclidean gap is a normalization choice (correlation is Euclidean distance
    after centring and scaling each vector). Measured for v0.6.18 on Nottingham and POP909, it
    moved accuracy by at most two points, in no consistent direction.
  - *The real link is the transposition.* Key-finding searches the twelve transpositions for
    the best fit, the same object as the dominant offset behind TI-Hamming.
  - *Where the vocabulary-vs-switches distinction would apply:* a piece that modulates.
    Labelling each window with a key is a segmentation; a cost per key change is the switches
    term (S, a Potts term), and a cost per distinct key used is the richness term (a label
    cost). Whether existing key-tracking models use the second is unchecked.
  - Scripts and cached histograms: `/Volumes/LaCie/data/midi/_tmp/keyest/`.
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
- **Replace the fallback MIDI reader** (from the v0.6.19 bug sweep, 2026-10-05; scottvr: "I
  never was thrilled that I had to have a fallback path"). When mido can't read a file,
  gtrsnipe falls back to py-midi, which is worse than no key signature:
  - on a file mido wrote, it garbled a track's leading events: it lost the key signature and
    the first note, and offset every later time by a fraction of a beat;
  - parsing a track twice doubles its events, and a flat key signature used to lose the
    track (both worked around in v0.6.19).
  - mido with `clip=True` already reads most of the files that needed a fallback. What's left
    could be a small, tolerant Standard MIDI File reader of our own (the format is simple:
    chunks, variable-length times, running status), tested against the files in the wild
    that mido rejects. First step: collect those files and see what actually fails.
- **What a tab states that still isn't kept** (from v0.7.0). Its `// Title:` (the converter
  names every output after the input file); bends, slides, vibrato and other marks.
- **`--omit-comments`: leave header lines out of a tab** (scottvr, 2026-10-07; maybe with a
  list, `--omit-comments tuning,title`, or a separate `--omit-header`). scottvr used "header"
  and "comment" interchangeably and flagged that as worth a discussion. They aren't the same
  thing to a reader:
  - Lines gtrsnipe reads back, so leaving them out changes what the tab *means*: `// Tuning:`
    (the tuning, and the mark that the tab is in gtrsnipe's layout), `// Capo:`, `// Time:`,
    `// Tempo:`.
  - Lines that only inform: `// Title:`, `// Transcribed with:`, `// Fingering:`, the chord
    and shape-name banners, the homograph keys.
  - Related: `--homograph-neutral` already numbers the strings and omits the default tuning.
    A tab with no tuning line is the bare text the homograph argument is about, and any
    "de facto standard" would have to say which lines are part of the notation.
  - scottvr, later the same day: the conflation wasn't only a slip. Sometimes the wish is
    to leave out *everything* written as a `//` comment, whatever it says, so the plain
    form (`--omit-comments` with no list) should mean exactly that.
- **Is the command-line stamp still needed? Ship style profiles instead** (scottvr,
  2026-10-07). Every generated tab carries `// Transcribed with: <the command line>`. It was
  there so a result could be reproduced, back when a good tab took a long line of options;
  profiles now do that job.
  - Test how much it still matters, especially since the Viterbi mapper: how often does a
    good tab need options at all, and do the cases fall into a few styles? This is the same
    question as M02 (Viterbi vs greedy across a corpus) and the "style profiles" idea in the
    scoring-weights notes ([`NOTES-playability.md`](NOTES-playability.md)).
  - If a small set of stylistic profiles covers it: ship them, lead the documentation with
    them, and rework the examples to use them in place of long command lines.
  - Then the stamp could go, or shrink to the profile's name. (Today it also writes the
    user's full file paths into the tab.) It is one of the lines `--omit-comments` covers.
- **Write a file the tab editors open: gtrsnipe as the generator they lack** (scottvr,
  2026-10-07). The tab programs are editors; few of them *make* a tab from MIDI, and gtrsnipe
  does little else. Facts checked that day:
  - Power Tab Editor 2 (open source again, GPL-3.0, github.com/powertab/powertabeditor) has no
    MIDI import. It is issue #251, open since June 2017, labelled high priority and good first
    issue; the maintainer confirmed in November 2024 (discussion #487) that it is still on
    the wish list.
  - Its source tree reads and writes its own `.pt2` (a gzip-compressed serialization of the
    score) and Guitar Pro 7's `.gp`, imports the older Guitar Pro formats, and exports MIDI.
  - So one writer could reach several editors. Guitar Pro's `.gp` is the likeliest target
    (a zip of XML, so no new dependency; which other programs open it is unchecked). Such a
    file carries exact rhythm, techniques, tuning and capo, so the ASCII tab would no longer
    have to be the only place rhythm can live.
  - Related: standard notation in and out (below), and F05 (PDF output), which an editor
    would then do for us.
- **Standard notation, in and out** (scottvr, 2026-10-07). Engrave proper scores (staff, clef,
  time signature) with an existing tool, and, more interesting and probably more feasible,
  *read* scores so they can be written to the formats gtrsnipe already has. Notes (Claude):
  - MusicXML is the interchange format the notation programs share (MuseScore, LilyPond via
    its converter, Finale, Sibelius). Reading it would give exact rhythm, key and time
    signature, which MIDI and tabs don't state; it can also carry string and fret. It is
    XML, so a reader needs no new dependency.
  - For engraving, writing LilyPond or MusicXML and letting those tools draw is far less work
    than drawing. LilyPond can set a tab staff under a notation staff.
  - gtrsnipe already reads one notation format, Humdrum kern, for the research corpora.
- **Learned weights and a profile finder** (from the scoring-weights notes, 2026-09-27; kept
  parked at the 2026-10-05 triage). A structured perceptron trained on human-fingered tabs, or
  sampling settings and letting a player rank the distinct tabs. Both wait for the weights
  audit (M01) and for human fingerings to learn from. Notes: [`NOTES-playability.md`](NOTES-playability.md).
