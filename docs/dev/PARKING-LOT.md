# Parking lot

Quick capture for new ideas. Write one or two lines each; there's no need to think them
through or start them. Nothing here is scheduled. Each entry is a checkbox line; at each
triage it either moves into [`BACKLOG.md`](BACKLOG.md), the single list of open work with a
plan, or is declined, and is removed from this file. (This is part of The Dull Protocol,
described at the top of the backlog.) Triaged 2026-09-26, 2026-09-27, 2026-10-05 and
2026-10-07; the finished entries are in the CHANGELOG, the open ones in the backlog, and the
original notes in git history.

## Ideas

- [ ] **A note-end mark in the tab layout** (from M08, 2026-11-07). The dash-count layout
  states onsets exactly; a note's end is a reading convention (legato, staccato, string). The
  end-to-start time base needs ends, so a mark for "released here" (a rest symbol on the
  string, or a letters-line rest) would make a gtrsnipe tab carry what MIDI carries. Changes
  the layout, so it needs the golden cases and the round-trip checked; pairs with H09.
  scottvr's candidates (2026-11-07, thought about before, never written out): underscores
  while a note sounds and dashes for silence (`----5___----7_9_----`); or a mark at the
  note's end, `>` (`----5-->----7>9>----`) or a subtler `.` that calls back to notation. A
  single pipe was rejected: confusing for readers on a full six-string chord, and a note
  spanning a bar line would need read-ahead or a second pass. To discuss when it comes up.
- [ ] **A verbosity structure for the mapper's messages** (scottvr, 2026-11-04, while answering
  M01 q1). Today the mapper is everything-or-nothing short of exceptions: `--debug` is a
  `-vvvvvvvvv` flood meant for him to see why a score didn't match his head, and the rest is
  a handful of warnings. The no-fit warning ("No fingering of the chord at beat ... fits
  within N frets; chose the least bad ...") went in at warning level so the player is told.
  If such messages turn out indistinguishable from clear choices, they can live behind a
  verbosity flag forever; either way the levels (what a player sees by default, what `-v`
  adds, what `--debug` dumps) want deciding once, with the tiered `--help` below.
- [ ] **Tiered `--help`, ffmpeg-style** (scottvr, 2026-11-04). The option count makes the full help a
  firehose. Today: a short usage by default and the grouped detail on `--help`. Next: several
  levels, from usage, to one group's detail on request (`--help mapper`, `--help tab`, ...), to
  everything. Means more argparse groups than we have, extending what the grouped help started.
- [ ] **Docs restructure; retire the wiki** (scottvr, 2026-11-04). Few people find the wiki tab or click
  wiki links in a README, and the README has grown huge. Move what the wiki says into the docs
  tree (the examples are already snapshotted under `docs/wiki/`), split the README, and keep the
  option text in one place that both the README and `--help` draw from (the README's option
  bullets are hand-copied from the help today).

- [ ] **The Viterbi mapper's inner loop is cubic in the candidate count** (found by the M01 sweep,
  2026-11-04). For each stage it loops over (current, previous, previous-previous) even when the
  score doesn't read t-2, so a 5-note chord with ~250 fingerings costs seconds per stage: the
  sus-shape probe takes 13.7 s for seven chords. Collapsing the first-order case to "best
  predecessor per previous fingering, computed once per stage" is exact (same tie-breaking:
  first index with the maximum) and quadratic. Real pieces are fine today (Asturias ≤ 20
  candidates per chord, 0.02 s), so this only matters for dense chords and for sweeps.
- [ ] **`--track` on a type-0 MIDI** (2026-11-04): a single-track file with several channels (the
  "Mr Crowley.mid" in `archives-to-go-through/`) fails with "file has 1 tracks". The research
  corpus reader already splits by (track, channel); the converter could select a channel the
  same way (`--track` by channel when the file has one track, or a `--channel` flag).
- [ ] **Read Power Tab (`.ptb`) and tab PDFs** (scottvr, 2026-11-04): `archives-to-go-through/` holds
  collections of third-party tabs as Power Tab files and PDFs (a Top-100 classic rock set among
  them), which would be R14's "tabs as written" input if gtrsnipe could read them. scottvr
  recalls the Power Tab Editor author open-sourcing it and starting a powertab2, both on
  GitHub (to verify); its source reads `.ptb` and writes `.pt2`/`.gp`, so the format is
  documented in code. PDFs would need text extraction of the tab lines first. Pairs with the
  parked "write a file the tab editors open" entry below.

- [ ] **Report the unfiltered counts, and revisit the "sounds unrelated" threshold** (scottvr,
  2026-10-21). The R04 scan excludes pairs that sound alike (C₁ ≤ ½ and contour agreement
  ≤ 0.6), and where any such threshold sits is arguable. Two asks:
  - Always state the totals *before* each filter, so a reader can see what the decision "these
    sound similar" removes and judge whether it is even a valid filter. The R04 tables give
    pairs / eligible / trivial / unrelated-sounding per length, but the pairs that fit six
    strings *and* sound alike are never discussed as a result in their own right.
  - The easy path is interesting too, at least as raw statistics. Pairs of distinct, separately
    claimed compositions by different authors that match closely (even ~90% in the *same*
    tuning, which the scan discards as "a capo, not a homograph") are a baseline worth computing
    and noting in the data, even if they are a different study topic. Lots of songs have
    similar passages; if they didn't, homographs would be even harder (which we showed, taking
    the hard path in the name of good science). Discounting pieces because "they already sound
    similar anyway" hides that baseline.
  - The example to keep in mind: the first Lakh run's best 24-note pair, Debby Boone's *You
    Light Up My Life* intro against a figure from Metallica's *For Whom the Bell Tolls*
    (`@1-24` / `@141-164`). The shared tab is real and verified note for note, but it is two
    repeated 6-note cells, so it was filtered as trivial (RESULTS-R04 §4, story 06). Not
    evidence, but a good demo.
  - **To discuss together (scottvr, 2026-11-04):** what "alike" or "similar" means here, as
    something *heard*; whether there is a cutoff at all; and how to report the remainder. The
    cases to tell apart: the same piece under another name (*Ça plane pour moi* vs *Jet Boy,
    Jet Girl*), a transposition only, a tempo difference only, tempo plus transposition,
    truncation or extension, and so on down to "fits six strings but sounds alike".

- [ ] **More strings for homographs** (scottvr, 2026-09-27).
  - 7- and 8-string guitars: 7-string tunings and `--num-strings 7` already exist, and the
    solver's free mode allows up to 12 strings. Anchored/middle need an 8-string tuning and
    gauge set. Richness ≤ 7 or 8 widens eligibility.
  - "Ludicrous mode": a 12-string with all 12 strings tuned independently. Physical twist:
    fretting a course sounds *both* its strings, so each tab note becomes a dyad unless one
    string of the course is avoided. The model would need courses, not strings.
- [ ] **`--min-note-length BEATS`**: drop notes shorter than a threshold, for MIDI from audio
  transcription (from P01, 2026-09-27). Optional: `--velocity-cutoff` is the existing cruft
  filter, and since P01 short notes stay short rather than being stretched.
- [ ] **A flatwound suffix for `--string-gauges`** (from F04, 2026-09-30; scottvr's jazz-set
  example). Flatwound strings weigh more per gauge than the nickel roundwounds the physics
  is calibrated to (`WOUND_FACTOR` 0.83 of solid steel). An `f` suffix needs a real factor,
  calibrated against a maker's published flatwound tensions, not a guessed constant.
- [ ] **Optimizer profiles with different *objectives*, not just weights** (scottvr, 2026-09-30;
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
- [ ] **Survey: how do tabs in the wild state their tuning?** (scottvr, 2026-10-07; a mental
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
- [ ] **Key changes: how many keys vs how many changes** (scottvr's question, 2026-10-04: do the
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
- [ ] **Keys: what v0.6.18 left out** (from C04/C05/F02, 2026-10-04).
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
- [ ] **Replace the fallback MIDI reader** (from the v0.6.19 bug sweep, 2026-10-05; scottvr: "I
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
- [ ] **What a tab states that still isn't kept** (from v0.7.0). Its `// Title:` (the converter
  names every output after the input file); bends, slides, vibrato and other marks.
- [ ] **`--omit-comments`: leave header lines out of a tab** (scottvr, 2026-10-07; maybe with a
  list, `--omit-comments tuning,title`, or a separate `--omit-header`). scottvr used "header"
  and "comment" interchangeably and flagged that as worth a discussion. They aren't the same
  thing to a reader:
  - Lines gtrsnipe reads back, so leaving them out changes what the tab *means*: `// Tuning:`
    (the tuning, and the mark that the tab is in gtrsnipe's layout), `// Capo:`, `// Time:`,
    `// Tempo:`, and since v0.8.0 `// Rhythm:` and `// Lengths:` (without them the tab's
    rhythm is read approximately).
  - Lines that only inform: `// Title:`, `// Transcribed with:`, `// Fingering:`, the chord
    and shape-name banners, the homograph keys.
  - Related: `--homograph-neutral` already numbers the strings and omits the default tuning.
    A tab with no tuning line is the bare text the homograph argument is about, and any
    "de facto standard" would have to say which lines are part of the notation.
  - scottvr, later the same day: the conflation wasn't only a slip. Sometimes the wish is
    to leave out *everything* written as a `//` comment, whatever it says, so the plain
    form (`--omit-comments` with no list) should mean exactly that.
- [ ] **Triplets in the note-length letters** (from F08, 2026-10-07). `--tab-letters` writes
  `W H q e s t` with dots and `+` ties, which can't state a triplet's note, so a bar holding
  one gets no letters (its layout still carries the rhythm: such a bar is written in
  columns). A mark for it (`e3` for a triplet eighth, or a bracket over the group) would
  close the gap. Worth checking what tabs with rhythm lines already do before choosing;
  Guitar Pro's text export has a "Duration Legend" with similar letters (from memory, not
  checked).
- [ ] **Is the command-line stamp still needed? Ship style profiles instead** (scottvr,
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
- [ ] **Write a file the tab editors open: gtrsnipe as the generator they lack** (scottvr,
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
- [ ] **Standard notation, in and out** (scottvr, 2026-10-07). Engrave proper scores (staff, clef,
  time signature) with an existing tool, and, more interesting and probably more feasible,
  *read* scores so they can be written to the formats gtrsnipe already has. Notes (Claude):
  - MusicXML is the interchange format the notation programs share (MuseScore, LilyPond via
    its converter, Finale, Sibelius). Reading it would give exact rhythm, key and time
    signature, which MIDI and tabs don't state; it can also carry string and fret. It is
    XML, so a reader needs no new dependency.
  - For engraving, writing LilyPond or MusicXML and letting those tools draw is far less work
    than drawing. LilyPond can set a tab staff under a notation staff.
  - gtrsnipe already reads one notation format, Humdrum kern, for the research corpora.
- [ ] **Learned weights and a profile finder** (from the scoring-weights notes, 2026-09-27; kept
  parked at the 2026-10-05 triage). A structured perceptron trained on human-fingered tabs, or
  sampling settings and letting a player rank the distinct tabs. Both wait for the weights
  audit (M01) and for human fingerings to learn from. Notes: [`NOTES-playability.md`](NOTES-playability.md).
