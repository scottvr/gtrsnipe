# Changelog

All notable changes to gtrsnipe are documented here.
This project adheres to [Semantic Versioning](https://semver.org/).

**Versioning while in 0.x.** The minor version marks breaking changes (or a
deliberate milestone); the patch version marks everything else, including
backward-compatible features and fixes. This is the left-most-non-zero rule that npm
and Cargo apply to 0.x version ranges. Full SemVer applies from 1.0.0. The public API
is the CLI flags and the file formats gtrsnipe reads and writes; report wording is
not part of it.

## [0.6.19] — 2026-10-05

Step 4 begins with a bug sweep (backlog B08–B22, H08): the open code bugs from the docs audit
and later passes, and how tabs are read back.

### Fixed
- **A failed conversion now exits with status 1.** It used to log "An error occurred" and
  exit 0, so a script couldn't tell a failure from a success. Producing no output for a
  requested file is also an error now.
- **`--transpose` is applied first,** before the range filter, `--normalize-pitch` and
  `--analyze`. Notes that fit once transposed are no longer dropped beforehand.
- **`--bass` no longer overrides `--tuning`.** It selects the bass version of the tuning:
  BASS_STANDARD by default, BASS_DROP_D for `--tuning DROP_D`, and a `BASS_` tuning as it is.
  A tuning with no bass version is an error.
- **`--tuning PIANO` works again.** It failed on every run, even with MIDI output. It passes
  every note through to a `.mid` file; other outputs are refused, as intended.
- **A tab gtrsnipe wrote reads back with even timing.** A two-digit fret pushed the notes
  after it one column to the right, and the reader took that column for time: steady
  sixteenths came back as 0.25, 0.375, 0.25 beats. This applies to tabs with gtrsnipe's
  `// Tuning` header, old and new; tabs from elsewhere are read by their columns, as before.
  (Of the example tabs in `examples/aswritten/`, Asturias v1, v2 and v5 now decode with
  steadier onsets. Re-running the R05 as-written test on those three gave the published
  counts exactly: it compares the notes' order, strings and pitches, not their onset times.)
- **`--analyze` on a tab** no longer ranks the tab's own tuning as an extra "CUSTOM" row when
  it is a named tuning, and a long custom name no longer breaks the columns.
- **`gtrsnipe-chords`** no longer warns "Could not find a playable fingering" about voicings
  its own diagram search tried and rejected.
- **`gtrsnipe-play` and `gtrsnipe-chords`** report an unreadable file in one line instead of
  a traceback.
- **The fallback MIDI reader** (used when the main one can't read a file) no longer loses a
  track over a flat key signature, no longer scans its first track before parsing it, and
  never parses a track twice. It is still the weaker reader; replacing it is parked.
- One "Successfully saved" message per output, not two.
- `gtrsnipe-research profile` names its own flags (`--subdivide`, `--rhythm`) in its hints.
- `--mono-lowest-only`'s help says what it does: ASCII tab output only.
- The player's help overlay lists every key it answers to (`enter`, `p`, `home`).
- A reused mapper no longer reports the previous song's score after an empty run.

### Changed
- **Exit status:** scripts that relied on gtrsnipe exiting 0 after an error will now see 1.

### Removed
- `gtrsnipe/player/clock.py`, dead since the transport replaced it in v0.5.0.

### Tests
- The three Viterbi tests the design doc promised: an exact tie (the smallest fingering wins
  at every stage), a guard that fails if the scorer reads history it shouldn't, and the
  enumeration cap.

## [0.6.18] — 2026-10-04

Step 3 continues: C04, C05 and F02 from `docs/dev/BACKLOG.md`, done together because they share
one thing: a song's key.

### Added
- **Extended chords (C04):** 9, maj9, m9, 7b9, 7#9, 11, m11, 13, maj13, m13 and 7sus4, in chord
  charts, `--name-chords` and `--name-chord`.
  - Three rules keep a melody note from being named as an extension. The chord must be
    complete: its defining tones all sound (the fifth may be missing, and a 13th's 9th) and
    nothing outside the chord does. Its root must be the bass (the same notes over another
    bass keep the simpler name: C/D's notes over C are still C). And add9, madd9 and 6/9, which
    have no seventh to define them, are named only for a fret shape (`--name-chord x32033` is
    Cadd9); in a bar of music a C triad with a D over it stays C.
  - Diagrams voice an extended chord as guitarists do, the extension on top (C9 as C E Bb D).
- **A key on the song (C05, F02),** and `--key KEY` (`Eb`, `F#m`, `'D dorian'`, or `auto`).
  - The key is `--key`, else the file's own (ABC's `K:`, a MIDI key signature), else an
    estimate from the notes. Whatever spells a name says which: a chord chart's header, a
    `//` line in a tab with `--name-chords`, a comment in ABC output.
  - **Chord names are spelled for the key (C05):** Ab in Eb major, G# in E major; a slash
    chord's bass as the chord spells it (E/G#). With no key (`--name-chord`), each chord is
    spelled in its own simplest key (Bb, Eb, Ab, F#; C#m, G#m), and its notes to match.
  - **ABC output has a real key signature (F02)** and spells notes in it. Accidentals are
    written so the tune reads the same whether or not a reader carries them through the bar.
  - MIDI output carries the key signature when the song has its own (never an estimate).
  - **The estimate:** pitch-class profiles in all 24 keys, the signature by Temperley's
    profile and major-or-minor by Krumhansl and Kessler's. Measured on songs with known keys,
    it was right for 88% of 1,034 Nottingham folk tunes and 91% of 709 single-key POP909
    songs; the key signature, which is all that spelling depends on, for 93% and 99%. (The
    pairing was the best of a handful tried on those two sets.) One key per song.
  - **A MIDI file's "C major" is kept only if the notes agree.** Sequencers write it by
    default: all 112 POP909 files that declare a key say C major, and 10 are in it.

### Changed
- **Chord names that were always sharps may now be flats:** A# is Bb, D# is Eb, wherever the
  key (or, with none, the chord's own) says so.
- ABC output no longer always says `K:C`.

### Fixed
- **`--transpose` was ignored by chord charts and by `--play`.** It now applies once, to
  every output and the player, and moves the key with the notes.
- **ABC output could be misread.** A natural after a sharp in the same bar was written bare
  (`^C C`), which standard readers play as two C sharps. Naturals are now written.

## [0.6.17] — 2026-10-04

The first public release since 0.6.9. Versions 0.6.10 to 0.6.16 were development releases,
not published on their own. Their changes are listed under their own headings below, and all
of them are in this release. The research write-ups in `docs/research/` are as published in
0.6.9, apart from their new location; their revisions will be published together when the
research is done.

## [0.6.16] — 2026-10-03

C07 (new, scottvr): what a chord chart's diagrams show is now a stated choice, and
fidelity to the song is the default.

### Added
- **`--chart-voicing {source,compact,open}` (C07).**
  - **`source` (the new default)** draws each chord as the song's own tab fingers it. That
    means the bar's chord tones, if each string holds one fret and they make one hand shape:
    at most four fingers, an index barre counting as one, within four frets, and
    fingerable. Otherwise it's the bar's fullest simultaneous chord as fingered, and a chord
    with no such bar gets a compact voicing marked `*`.
  - **`compact`** is the previous default, a compact voicing of the chord's name.
  - **`open`** is C02's open shapes; `--prefer-open-chords` is the same as
    `--chart-voicing open`.
  - The chart's header states the mode.

### Changed
- **Chord charts name bars as `--name-chords` does:** the lowest note at the start of a bar
  always counts as a chord tone. An arpeggiated bar is named by its bass, so the Bach
  Prelude's opening reads G, C/G instead of Bm/D.
- **Chord charts now show the song's own voicings by default,** where one hand shape holds
  them. Use `--chart-voicing compact` for the previous diagrams.

## [0.6.15] — 2026-09-30

Step 3 continues: C02 from `docs/dev/BACKLOG.md`.

### Added
- **`--prefer-open-chords`: open-position shapes in chord charts (C02).**
  - Each chord is drawn in its familiar first-position shape where one exists: C `x32010`,
    G `320003`, D `xx0232`, F `xx3211`, B7 `x21202`, C/G `332010`, and so on.
  - The shapes are found by search, not a lookup table, so they work in any tuning and with
    a capo: with capo 2, a D is drawn as the C shape you finger.
  - The constraints: every chord tone present (4-note chords may drop the fifth); the
    chord's bass on the lowest string played; muted strings only at the low end; at most
    four fretted strings within four frets.
  - One fingerability rule: two notes on one fret may not straddle a higher fret unless a
    barre could cover them. That rules out 102210 as an Fmaj7, but keeps C7 `x32310`.
  - Chords with no open shape keep the compact voicing.
- **Every chord diagram is captioned with its shape** (e.g. **C** `x32010`), which shows
  muted strings.

### Changed
- An open-position diagram keeps the nut in view (G `320003` used to start at fret 2).

## [0.6.14] — 2026-09-30

The R03 follow-ups (backlog R12, R15): a research subcommand.

### Added
- **`gtrsnipe-research segments`: phrase- and motif-level retrieval on MTC-ANN's expert
  annotations.**
  - Phrases are labelled by three annotators and scored separately; there are 1,657 motif
    occurrences. All annotations line up with gtrsnipe's kern reader.
  - The measures: the R03 grid measures; DTW on intervals, and on pitch after the modal
    transposition; and the offset measures minimized over warping paths (switches, total
    variation, largest jump, range, and richness exact up to 6). All five warped measures
    are confirmed against brute-force path enumeration.

## [0.6.13] — 2026-09-30

Step 3 continues: C03 from `docs/dev/BACKLOG.md`.

### Added
- **`--shape-names`: chords named by the shape you finger (C03), a "generalized capo".**
  - In a tuning that is standard shifted evenly on every string (E_FLAT, D_STANDARD,
    C_SHARP_STANDARD, the baritones, the bass and 7-string equivalents, or an even custom
    tuning), plus any capo, a chord is named as its fingering would be in standard tuning
    with no capo: in BARITONE_B a C shape is named C though it sounds G.
  - Drop and open tunings have no standard shape names, so their chords stay in concert
    pitch.
  - A banner always states the convention: at the top of a chord chart, as a `//` line in a
    tab's header, and under `--name-chord` output.
  - It applies to chord charts (their diagrams still show the notes actually played),
    `--name-chords`, and `--name-chord SHAPE` (which adds a `shape:` column).

## [0.6.12] — 2026-09-30

Step 3 continues: F04 from `docs/dev/BACKLOG.md`, with two gauge fixes scottvr asked about.

### Added
- **`--show-tuning` shows string tension (F04).**
  - For each string: the note it's strung for and tuned to, its gauge, the tension, the
    change from normal, the stress (for plain strings), and a status.
  - Strings outside safe tension get a restring suggestion. When no steel string is safe at
    a pitch, it says so: a plain string's breaking pitch depends on the scale, not the gauge.
  - "Your guitar" is the usual set for `--tuning` (10-46 for STANDARD), or `--string-gauges`,
    strung for an explicit `--tuning` or else for the tuning shown.
  - With no name, `--show-tuning` shows the tuning set by `--tuning-pitches` or
    `--drop-low-string`.
- **Converting with a custom tuning warns** about any string it would overload or leave
  floppy. A tab's own header tuning is taken as given, with no warning.
- **`--solve-tuning` notes pitches past what a steel string can take** at the scale length
  (e.g. A4 at 25.5"), whatever the gauge.

### Fixed
- **Gauges for a re-entrant tuning** (e.g. Nashville) are read exactly as written, low string
  first. An ascending set used to be flipped as if written thin-to-thick, putting the thinnest
  string on the low one.
- **The `p` (plain) suffix of `--string-gauges` is now documented.** It worked, but only `w`
  was mentioned: a jazz set's plain .022 is `22p`, since unsuffixed gauges above .020 count as
  wound.
- A custom gauge set is described by its thinnest and thickest gauges ("8-16 set"), not
  "011-010".

## [0.6.11] — 2026-09-29

Step 3 continues: C01 with C06 from `docs/dev/BACKLOG.md`.

### Added
- **`--name-chords`: chord names above an ASCII tab (C01).**
  - A name sits over the first note of its bar. It's written where the chord changes and
    again at the start of each line, and wraps with `--max-line-width`.
  - Bars are named as in chord charts, with two refinements:
    - the lowest note at the start of a bar always counts, so an arpeggio's bass isn't
      lost among short notes (Bach's Prelude reads G, C/G);
    - each bar is also named by halves, so a bar that changes chord midway gets both names.
  - Only plainly spelled chords are named (`core.chords.is_clear`): every chord tone
    except perhaps the fifth, at most one extra note, and exact power chords. A melody bar
    or a doubtful chord gets no name rather than a wrong one.
  - Names are concert pitch. The name line is ignored when the tab is read back in.
- **`--name-chord SHAPE`: name a fret shape without an input file (C06, scottvr's idea).**
  - The frets are listed from the lowest string, `x` for muted:
    `gtrsnipe --name-chord x,x,3,2,1,0` prints Fmaj7 and its notes.
  - The shape is read in `--tuning` or `--tuning-pitches`, with `--capo` and
    `--num-strings`, so the same shape names the chord it plays on your guitar: the C
    shape is G on a baritone.
  - The option can be repeated, and the compact `x32010` form works when every fret is
    one digit.

### Changed
- `chords.segment.segment_by_measure` gains `keep_downbeat_bass` and `parts` (both off by
  default, so chord charts are unchanged).

## [0.6.10] — 2026-09-28

A docs interlude in step 3 (backlog H05 and H06), and the bugs it turned up.

### Fixed
- **`--stem-track` crashed on every run since v0.3.0.** A NameError in the Demucs wrapper
  (`importlib` was never imported) stopped it before separation began. It also never mapped
  "guitar" to the "other" stem for 4-stem models: the check was a substring test that the
  4-stem `htdemucs` itself passed. Tests added, with Demucs stubbed.
- **`--tuning` rejected six tunings that `--list-tunings` shows** (DADGAD, DROP_B,
  D_STANDARD, OPEN_D, OPEN_E, SEVEN_STRING_DROP_A). The choices are now derived from the tuning
  list, with a test.
- **Help texts that said the opposite of what the flag does:** `--no-pre-quantize`,
  `--no-constrain-frequency`, `--min/--max-note-override` (which cited a removed flag),
  `--tapping-run-threshold` (off by one), and `--demucs-model` (a misspelled model name).

### Documentation
- **`docs/` reorganized** into `app/` (how gtrsnipe works), `research/` (theory, literature,
  results) and `dev/` (process), with a map in `docs/README.md`.
- **A state-of-the-docs audit** checked every doc against the code and each other, and its
  fixes to the app docs are applied:
  - the README's options list, examples and tuning list are corrected (several documented
    flags and commands no longer existed);
  - the wiki snapshot's reference page is rewritten, and its example pages note that they
    show v0.2's greedy mapper;
  - the design docs are current;
  - the homograph examples' reports now include playability.

## [0.6.9] — 2026-09-27

Step 3 continues: P03 from `docs/dev/BACKLOG.md`.

### Changed
- **Playback sound defaults to the MIDI file's own instrument (P03).**
  - Without `--instrument`, `--audio midi|fluidsynth` uses the General MIDI program and
    channel of the first track with notes, and logs which it picked. An explicit
    `--instrument` still wins.
  - The MIDI reader now keeps each track's program and channel, the same way it keeps
    its name.
  - `gtrsnipe-play` parses the file before opening audio, so it can choose.

## [0.6.8] — 2026-09-27

Step 3 continues: P01 from `docs/dev/BACKLOG.md`.

### Changed
- **Playback honors note lengths and rests (P01).** Each note now stops at its own end,
  instead of every note sounding until the next onset.
  - A held note rings under later ones, and a rest is silent.
  - A re-struck pitch is never cut short by its earlier note's release.
  - Pausing in a rest stays silent; step mode still sounds each frame on its own; the
    metronome clock stays legato on its grid.
  - `--legato` restores the old playback.
- **The MIDI reader keeps short notes.** It used to stretch every note shorter than a
  sixteenth (0.25 beats) to a sixteenth, a leftover of early tab-spacing experiments. The
  tab generator spaces notes by onset, so that no longer matters. The floor is now 1/64 of a
  beat. *MIDI output from MIDI input can change: short notes stay short.*

### Added
- **`--sustain {legato,string}` for tab input**, in `gtrsnipe` and `gtrsnipe-play`. A tab
  says when to strike a string, not when to stop.
  - `legato` (default, as before) holds each note until the next onset.
  - `string` lets each note ring until its own string is struck again, at most one bar.
    Arpeggios and pedal notes then keep sounding: on the Asturias v6 tab, the average note
    lasts 1.03 beats instead of 0.37.
  - It applies to the parsed Song, so playback and MIDI output agree.

## [0.6.7] — 2026-09-27

Step 3 continues: F03 from `docs/dev/BACKLOG.md`.

### Changed
- **`--analyze` ranks tunings by how playable the song is in each (F03).** It used to list
  the tunings whose range fits.
  - It now fingers the song in each of them, with your own mapper settings, and ranks them
    by the mapper's score per note.
  - Each row shows how many points per note harder than the best tuning it is, the frets
    used, the average hand travel between fretted notes, and the share of open strings.
  - Ties (the default weights don't prefer open strings to a barre) go to less travel,
    then more open strings.
  - A guitar gets guitar tunings (7-string and baritone included) and `--bass` gets bass
    tunings; before, all were mixed. A custom `--tuning-pitches` tuning is ranked too.

### Fixed
- `--analyze` no longer demands `-o/--output`; it never writes one.

## [0.6.6] — 2026-09-27

Step 3 begins: B07 and F06 from `docs/dev/BACKLOG.md`.

### Added
- **Playability of homograph tabs (F06).**
  - Each anchored or middle solution now reports its *discomfort*: how many mapper points
    per note its fingering of song A scores below the tab gtrsnipe writes for A alone, in the
    same tuning and key. It also reports the fret range used.
  - `--homograph-max-discomfort POINTS` rejects placements over the limit. The solver then
    fingers up to 16× more placements looking for one within it.
  - `gtrsnipe-research scan` takes `--max-discomfort` and `--max-fret`, and lists each
    candidate's discomfort.
  - Finding (DESIGN-homograph, RESULTS-R04 "Playability"): string tension barely filters
    shared tabs, but comfort does. Of 50 sampled folk pairs, 49 have a tab, but only 19 have
    one within 50 points per note, 4 within 20, and none within 5. A's own tab scores −2 to
    −7 per note.

### Fixed
- **MIDI track and instrument names were dropped (B07).** The mido path never read
  `track_name`/`instrument_name` events, so every track was "Acoustic Grand Piano". *Tab
  titles for named tracks now read "Title (Melody)".*

## [0.6.5] — 2026-09-27

R05 finishes the research items planned for step 2 of `docs/dev/BACKLOG.md`.

### Added
- **`gtrsnipe-research aswritten TAB…`**: can a tab's *own* fingering be retuned into
  another song?
  - Every note the tab puts on one string must move by one interval.
  - Windows slide over the tab and are tested against evenly spaced corpus passages. The
    output counts trivial hits (each string maps one pitch to one pitch), transpositions of
    the passage itself, and unrelated-sounding hits.
  - The best hits go through the solver's as-written check.
- `docs/research/results/RESULTS-R05-aswritten.md`, from Bach's Cello Suite No. 1 Prelude and six
  successive Asturias fingerings (`examples/aswritten/`):
  - As written is about 10,000× stricter than a free fit.
  - Which passages a tab can become depends on the fingering.
  - Past 16 notes, nothing unrelated-sounding fits either piece's real fingering.
- `docs/wiki/`: a snapshot of the whole GitHub wiki, with Windows-safe file names.
- `docs/research/theory/PROOF-alignment.md`:
  - the stutter-invariance principle: stutter-invariant, subadditive offset statistics stay
    pseudometrics under warping;
  - a subsection relating it to the Fréchet distance, DTW and elastic metrics (ERP, TWED,
    MSM);
  - a checklist of citations to verify.

## [0.6.4] — 2026-09-26

Step 2 of `docs/dev/BACKLOG.md`, continued: R04, the corpus homograph scan.

### Added
- **`gtrsnipe-research scan CORPUS…`**: finds passages of different songs that one tab can
  play under two tunings.
  - It buckets marked phrases (or sliding windows) by rhythm and computes the richness of
    every same-rhythm pair from different works.
  - It counts, per length, what is eligible, what is trivial, and what sounds unrelated.
  - It runs the full homograph solver (anchored and middle, string physics) on the best
    pairs and on a random sample per length, and writes verified shared tabs on request.
  - Options: `--cross-corpus`, `--named-melodies`.
- `docs/research/results/RESULTS-R04-scan.md` with charts (`docs/research/results/r04_plot.py`, `docs/research/results/figures/`):
  - Folk song (Essen + Meertens): a third of same-rhythm 8-note phrase pairs from different
    tunes share a tab and sound unrelated; 8% at 12 notes, 3% at 16.
  - The solver places 93–100% of sampled pairs on a real guitar: A in STANDARD, B a retune
    of the same guitar.
  - Pop (Lakh): mostly trivial pairs (few distinct pitch pairs), but 4,467 unrelated-sounding
    32-note pairs remain.

### Changed
- MIDI melody extraction no longer takes "Voice Oohs"/"Aahs" or pad tracks for the
  melody.

## [0.6.3] — 2026-09-26

Step 2 of `docs/dev/BACKLOG.md`, continued: R03 and R07.

### Added
- **`gtrsnipe-research families CORPUS`**: tune-family retrieval with every offset
  measure (R03).
  - Each measure ranks every melody against the others on one shared pairing: pitch
    sampled at evenly spaced points.
  - Scores are tie-aware MAP and AUC, with bootstrap intervals.
  - Logistic pair models, cross-validated by tune family, test whether the
    candidates add anything to the baselines.
  - Result ([`docs/research/results/RESULTS-R03-families.md`](docs/research/results/RESULTS-R03-families.md)):
    on MTC-ANN and MTC-FS-INST, transposition-invariant Hamming wins, and richness
    adds nothing (+0.002 to +0.006 MAP). It is a guitar statistic, not a similarity
    measure.
- `docs/research/theory/PROOF-alignment.md` and `alignment_check.py` (R07): under optimized
  (warping-path) alignment, log-richness, switch count and total variation stay
  pseudometrics; entropy and modal share don't (a 3-note counterexample).
  - `coupled_transposition_structure.md` gets pointers in §4.4 and §7.

## [0.6.2] — 2026-09-26

The first research tools (step 2 of `docs/dev/BACKLOG.md`: R01, R02, R06).

### Added
- **`gtrsnipe-research`**, a new command for work across melody corpora. It isn't
  imported by `gtrsnipe` itself.
  - `corpus build/info/show/list` reads the Essen Folksong Collection, the Meertens
    Tune Collections (MTC-ANN, MTC-FS-INST, with tune-family labels), Nottingham,
    POP909 and Lakh into one monophonic format and caches each corpus as a single
    gzipped file.
    - Kern files go through a new reader that keeps phrase marks. It matches
      music21 note for note on 8,469 of the 8,473 Essen files; the other 4 have
      malformed tie chains, which it holds as one note.
    - For MIDI it takes a melody-named part, or else the skyline of the other parts.
  - `profile A B` prints the offset profile of two aligned melodies: richness,
    entropy, coverage C₁…C₆, transposition-invariant Hamming, switches, total
    variation and reuse. A and B can be corpus melodies or phrases
    (`essen:deut4659#p2`), files or inline melodies.
- `docs/research/literature/LITERATURE-offsets.md`: the prior-art survey for the offset measures
  and tab homographs.
- `docs/research/results/collision_plot_template.py`: a figure template for the corpus scan
  (placeholder curves).

### Fixed
- **Non-editable installs were missing most of gtrsnipe.** The package pattern
  matched only the top-level package, so a wheel (e.g. `pip install
  git+https://…`) held 3 of 56 modules. Editable installs (`pip install -e .`,
  the README's method) were unaffected.

## [0.6.1] — 2026-09-26

A correctness sweep (step 1 of `docs/dev/BACKLOG.md`).

### Fixed
- **ABC input was decoded wrong.** The parser ignored the key signature and read
  chord symbols (`"G7"`), lyrics lines and comments as notes; it got 0 of the 1,034
  Nottingham folk tunes right. It's rewritten and now handles:
  - key signatures, including modes (`Dmix`, `E minor`) and explicit accidentals;
  - accidentals carried through the bar as the ABC version says (as music21 does);
  - ties, including the detached `C2 -C2` form legacy files use, where a tied note
    keeps its accidental;
  - broken rhythm, tuplets, chords, rests and multi-bar rests;
  - mid-tune key, length and meter changes;
  - skipping grace notes, decorations and other non-note text;
  - only the first tune and the first voice.

  It now matches music21 note for note on 94% of those tunes; the rest are music21
  quirks.
- **RIFF-wrapped MIDI** (`RIFF…RMID`, 259 files in Lakh) came back as an empty
  song. It's now read. Files that aren't MIDI at all raise a clear error instead of
  returning nothing, and out-of-range MIDI data bytes are tolerated.
- **Tabs with hammer-ons/pull-offs read back wrong.** The `h`/`p` letter pushed the
  fret digits one column late, so a chord with a hammered note decoded as an
  arpeggio and hammered notes read late. The letter now goes before the digits.
  *Generated tabs with techniques change byte-for-byte (they now read back
  correctly).*
- **`--num-strings 7` dropped the 7-string's low B string.** The range filter used
  STANDARD instead of the resolved tuning, so every note below E2 was discarded.
- An explicit `--tuning STANDARD` now overrides a `.tab`'s own `// Tuning:`
  header. Only the default defers to the header.

### Removed
- The empty `PdfTabGenerator` stub. Pretty PDF output stays on the backlog (F05).

### Changed
- The v0.3.0-era planning docs moved to `docs/dev/archive/`.

## [0.6.0] — 2026-09-26

### Added
- **Tab homographs** (`--homograph A B [C …]`): one ordinary, fretted, playable
  tab that plays a different song in each tuning. Two aligned songs share a tab iff
  their note-for-note intervals split into ≤ N classes (one per string; see
  [`docs/app/DESIGN-homograph.md`](docs/app/DESIGN-homograph.md)). The report walks
  through each check in turn: alignment → **richness** (distinct intervals) → *free* /
  *anchored* (A keeps `--tuning`, an ordinary tab of A) / *middle* (both tunings
  retune one strung guitar) / *as written* (does A's own `.tab` fingering retune?).
  It names the first obstacle, verifies every solution by decoding, writes
  `-o shared.tab` with every song's key in the header, and `--play`s it in any
  song's tuning. Songs are files (`.mid[:TRACK]`, `.abc`, `.tab`, `.vex`, each
  with an optional `@START-END` onset window) or inline melodies
  (`"C4 C4 G4:2 r:1 C3+E3+G3"`). Knobs: `--homograph-mode`, `-rhythm` (strict /
  ratio slop / sequence), `-subdivide` ("ta" ≈ "ti ti": smear repeated notes or
  re-strike), `-transpose`, `-transpose-a`, `-max-retune`, `-octaves`, `-neutral`,
  `-play`.
- **String physics** (`gtrsnipe/guitar/strings.py`): tension from gauge / scale /
  pitch (matches D'Addario EXL110 within 1–2%), plain steel's gauge-independent
  breaking pitch (≈ A4 at 25.5″), wound-core headroom, slack limit, and
  restring suggestions. Homograph retunes are costed and flagged with it.
  `--scale-length`, `--string-gauges` configure the instrument.
- Worked public-domain examples in `examples/homograph/`.
- Dev note [`docs/research/theory/coupled_transposition_structure.md`](docs/research/theory/coupled_transposition_structure.md)
  (+ `triangle_check.py`): the offset-sequence analysis behind the homograph's
  *richness* (the Hill order-0 count of distinct note-for-note intervals). It covers
  which offset statistics are metrics modulo transposition, the explicit
  counterexamples at other Hill/Rényi orders, and prior-art names.
- An adversarial multi-agent review of the feature found and confirmed 22
  issues before release (middle mode not a superset of anchored, the wound-string
  model, re-rhythm edge cases, rendering). All are fixed, each with a regression test.

### Fixed
- **`-i x.tab` now honors the tab's own `// Tuning:` header** when no tuning is
  given, for the whole run (decode, range filter, mapping, and any tab output),
  as if `--tuning-pitches` had named it. Before, the CLI always passed STANDARD
  pitches to the parser, so the v0.5.0 tab round-trip only worked through the API
  (a DADGAD tab decoded as if standard). An explicit `--tuning`/`--tuning-pitches`
  still overrides; header-less tabs read as 6-string standard, as before.
- Note names `Cb` and `B#` were an octave off (`Cb4` gave B4, `B#3` gave C3), in
  `--tuning-pitches` and anywhere else note names are read.
- `--save-args` no longer writes per-run inputs `--solve-tuning` / `--homograph`
  into a profile (a saved `--solve-tuning` turned every later run into a solve).

## [0.5.0] — 2026-09-25

Unified-I/O refactor (design: [`docs/app/DESIGN-unified-io.md`](docs/app/DESIGN-unified-io.md)).
The player, chord charts, and converter are now one tool over a shared option
surface and an event-driven transport. **Existing `gtrsnipe -i x -o y.{tab,mid,abc,vex}`
invocations are unchanged (byte-identical output).**

### Added
- **Custom tunings.** `--tuning-pitches "A1,E2,A2,D3,F#3,B3"` (low string → high)
  defines any tuning, any string count; `--drop-low-string N` lowers the lowest
  string by N semitones (2 = drop-D style) on any tuning. Works across all modes.
- **Inverse tuning solver.** `--solve-tuning "C4,C4,G4,G4,A4,A4,G4"` finds a tuning
  under which an all-open-string tab plays that melody — the tab reveals none of
  the tune (it lives entirely in the tuning). Prints the tuning + tab; `--play` to
  hear it, `-o FILE.tab/.mid` to write it. No `-i` needed. (Also a handy
  alternate-tuning finder.)
- **Config profiles (`.gtrsnipe`).** Save long option sets and reuse them.
  `--profile NAME` (repeatable and/or comma-separated; applied in order) loads
  option files from `./.gtrsnipe`, `~/.gtrsnipe`, or `$GTRSNIPE_HOME`
  (`--config-dir` overrides); a `defaults` profile auto-loads (`--no-defaults` to
  skip). Explicit CLI args always override profile values. `--save-args NAME`
  writes the current non-default options back to a profile. Simple format:
  `name value`, `name = value`, or bare `name` for flags; `#` comments. Works
  across all three commands, since a profile is just prepended argv re-parsed.
- **One canonical tool.** `gtrsnipe` now also:
  - writes a **chord sheet** as an output format: `-o SONG.chords.md` (or `.chords`);
  - **plays/visualizes** with `--play [--view {fretboard,tab}]`, `-o` no longer
    required. Because `--play` runs after the full input preamble, it inherits
    audio-input transcription, `--normalize-pitch`, `--transpose`, and frequency
    range — you can now `gtrsnipe -i song.wav --play`.
- **Full mapper option surface everywhere.** The player and chord charts now
  accept all 33 mapper knobs (`--fret-span-penalty`, `--sweet-spot-*`, `--barre-*`,
  `--let-ring-bonus`, …), not the previous ~6.
- **Transport controls** in the player: `space` pause/resume (toggle), `.`/`,`
  step (while paused), `←`/`→` seek ±1 bar, `[`/`]` tempo, `g`/`end` jump, `h`
  help, `q` quit — with audio resynced on seek/pause.
- **Curses player** on a real terminal: alternate screen (scrollback preserved &
  restored), non-blocking input (live pause during playback), and terminal-resize
  re-layout. Piped/redirected output falls back to a plain stream.

### Changed
- Argument definitions and `MapperConfig` construction are defined once in
  `gtrsnipe/arguments.py` and composed by every CLI (was declared/duplicated 3×).
- The three player Clock classes were replaced by one event-driven `Transport`
  whose audio onsets fire at true times (independent of the display frame rate).
- `gtrsnipe-play` / `gtrsnipe-chords` remain as curated convenience stubs over the
  same engine.
- **Tuning tuples are now ordered low string → high** (the enum data,
  `--show-tuning`/`--list-tunings`, and `--tuning-pitches`), matching how tunings
  are conventionally named. The internal string *index* is unchanged (0 = highest;
  tab staves still put the fattest string on the bottom row) — verified: resolved
  open-string pitches and all tab/mid/abc/vex output are unchanged.

### Fixed
- **ASCII tab parser honors the tuning.** It previously assumed standard/bass
  tuning regardless of `--tuning`, so a tab read under any other tuning produced
  wrong pitches. It now decodes in the configured (named or custom) tuning.
- **Generated tabs round-trip.** The parser reads the `// Tuning:` header and
  accepts any string labels (not just `eBGDAE`), so a generated tab can be re-read
  as input in its own tuning — or in a different one (explicit `--tuning` wins).
- **6-string low-E no longer dropped.** String-count detection uppercased `e`/`E`
  to one key, mis-counting 6 strings as 5 and dropping low-E notes on single-block
  tabs; it now uses the tuning header's count (else the first contiguous run).

### Testing
- Opt-in, profile-driven golden-output regression gate (`tests/golden/`, skips
  when no local fixtures are present) — turn a tuned real piece into a pre-release
  check without committing copyrighted inputs.

## [0.4.0] — 2026-09-24

### Added
- **Player / fretboard visualizer** (`gtrsnipe-play`). Renders any supported
  input (MIDI/ABC/VexTab/ASCII-tab) as a time-driven ASCII fretboard: an
  auto-following 5-fret window that tracks the playing up and down the neck.
  Three timing modes via `--clock`: `tempo` (at the song's tempo), `metronome`
  (a fixed `--grid` beat step), and `step` (advance manually with a keypress,
  quit with `q`). Reuses the existing parser + Viterbi mapper unchanged; the
  timeline, clock, and renderer layers are decoupled so browser/Qt renderers
  can be added later without touching the core. Rhythm fidelity follows the
  input — precise from MIDI, approximate from ASCII tab.
  - `--track N` selects a single MIDI track (1-indexed), matching the converter.
  - `--orientation {horizontal,vertical}` rotates the board (frets as columns,
    or chord-diagram style top-to-bottom); `--hand {right,left}` mirrors the
    neck for left-handed players.
  - `--view tab` renders a horizontally-scrolling ASCII tab staff instead of the
    neck — notes flow right-to-left under a fixed playhead as the clock advances
    (a "7-bit terminal Guitar Hero"). `--width` sets the viewport columns.
  - `--audio {midi,fluidsynth}` makes the player emit sound. `midi` streams
    note-on/off to a MIDI port (route it to a DAW/VST host or system synth) via
    `mido` + `python-rtmidi` (the new `[play]` extra); `fluidsynth` renders a
    SoundFont directly with no external host (`pyfluidsynth`, the `[synth]`
    extra). Missing backends fail with an install hint, not a traceback.
  - `--instrument` selects the voice by General MIDI program number (0-127) or
    name substring (e.g. `nylon`, `distortion guitar`); `--list-instruments`
    prints the GM set.
  - Smooth scrolling: the display animates between onsets at `--fps` (default 12)
    and shows a continuous `bar N/total beat X.x` readout — the bar ratio doubles
    as a progress bar, and the moving readout means long rests in ensemble MIDI
    keep visibly playing instead of looking like the app hung.

### Fixed
- **Last note no longer cut off.** Auto-clock playback marked the final frame
  with no dwell, so its note was struck and immediately released; every frame
  now dwells for its duration.
- **FluidSynth error clarity.** When the native `libfluidsynth` C library is
  missing (but pyfluidsynth is installed), the error now points at the C library
  (port/brew/apt) and the MacPorts `DYLD_FALLBACK_LIBRARY_PATH` tip, instead of
  telling the user to reinstall pyfluidsynth.
- **librosa 1.0 compatibility.** The audio-transcription path crashed with
  `module 'librosa.beat' has no attribute 'tempo'` on modern librosa. Tempo
  estimation now resolves `librosa.feature.rhythm.tempo` / `librosa.feature.tempo`
  / `librosa.beat.tempo` across versions (tested end-to-end on librosa 1.0.0).

### Known limitations
- Player audio sustains each note until the next onset (legato); a note's own
  duration and rests are not yet honored in playback — visuals are unaffected.
  Honoring true note-offs needs an event-level audio scheduler (roadmap).
- **Chord charts** (`gtrsnipe-chords`). Segments a song into one chord per
  measure (pitch classes unioned across the bar, weighted by duration, with the
  bass note resolving inversions/slash chords) and emits a Markdown/ASCII chord
  sheet: a bar-by-bar progression grid plus an ASCII diagram for each unique
  chord. Diagrams use a compact, playable root-position voicing generated in the
  song's tuning (the lowest tight-span register the mapper can finger), not the
  literal bar contents. Chord naming lives
  in `gtrsnipe.core.chords` (pure pitch-class template matching: triads, power
  chords, 6/7/maj7/m7/m7b5, sus2/sus4, dim/aug/dim7). Extended chords (9/11/13)
  and enharmonic key-aware spelling (sharps only) are deferred.

## [0.3.0] — 2026-09-23

Release plan and design docs live in [`docs/dev/archive/`](docs/dev/archive/RELEASE-PLAN-v0.3.0.md).

### Added
- **Global fretboard optimization.** A dynamic-programming / Viterbi trellis
  mapper replaces the greedy per-chord search, producing globally optimal, more
  playable fingerings. New `--optimizer {viterbi,greedy}` (default `viterbi`);
  the previous greedy behavior remains available via `--optimizer greedy`.
- **Optional-dependency extras** so the base install is torch-free:
  `pip install 'gtrsnipe[audio]'` (librosa bass pipeline),
  `pip install 'gtrsnipe[separation]'` (demucs stem isolation).

### Changed
- **BREAKING (packaging):** audio dependencies are no longer installed by
  default. `pip install gtrsnipe` now installs only the CPU-only MIDI/tab/abc/vex
  core. **If you use audio input, install `pip install 'gtrsnipe[audio]'`**
  (and/or `gtrsnipe[separation]`).
- `requires-python` raised to `>=3.10`. Python **3.10–3.13** are fully supported;
  **3.14** is supported for the core (audio extras are best-effort on 3.14 until
  numba publishes 3.14 wheels — use 3.10–3.13 for the librosa path).
- Fretboard mapper tie-breaking is now deterministic (lexicographically smallest
  fingering); previously it depended on hash/iteration order. Outputs may differ
  from prior versions only on exact score ties. Use `--optimizer greedy` to
  reproduce pre-0.3.0 behavior for one release.

### Removed
- The experimental `basic-pitch` pitch engine, the ONNX distortion-remover
  (`--remove-fx`), and the HiFi-GAN vocoder — with their basic-pitch-only flags
  (`--onset-threshold`, `--frame-threshold`, `--min-note-len-ms`,
  `--melodia-trick`). The librosa engine is the supported audio path.

### Fixed
- Output-corrupting f-string bugs: VexTab title and ABC instrument name emitted
  the literal placeholder text (`{song.title}`, `(track.instrument_name)`)
  instead of the real values.
- Tab out-of-bounds string index: a negative index silently wrote a note onto
  the wrong string; both bounds are now guarded.
- MIDI time-signature denominator: non-power-of-2 signatures (e.g. 4/6) were
  silently truncated to a wrong denominator; they now warn and fall back to 4/4.
- Tab measure sizing now honors the time-signature denominator (correct bar
  lines for 6/8, 3/8, 2/2), matching the ABC generator.
- ABC header validity: the `T:` (title) line now precedes `K:` (which closes the
  header); the instrument name is emitted as a comment rather than an invalid
  body `T:`.
- Capo ordinal suffix (`3rd`/`21st`/`22nd`, not `3th`/`21th`/`22th`).
- Note-name↔pitch round-trip for negative octaves (e.g. `C-1`, MIDI 0).
- Double-quantization on the `--dynamic-quantize` audio path (a second pass
  re-quantized already-quantized events against a grid recomputed from the raw
  input).
- Crash on `--dedupe` (an undefined `_normalize_pitch` helper).
- Removed a stray `DEBUG PARSER` `print()` from the tab parser.

See [`docs/dev/archive/AUDIT-findings.md`](docs/dev/archive/AUDIT-findings.md).

### Known limitations
- **VexTab** does not yet emit hammer-on/pull-off/tap articulation symbols or
  rests for time gaps between notes (the ASCII tab generator does). Tracked for a
  future release.
- **ABC** key signature is always emitted as `K:C` (the `Song` model carries no
  key), and accidentals are spelled as sharps regardless of key.

## [0.2.2] — 2026-09-12

### Fixed
- **Critical:** a stray `exit(1)` (regression from the v0.2.1 refactor) inside the
  non-piano branch of `converter.main()` aborted every guitar/bass conversion
  before any output was written. Guitar/bass `.tab/.abc/.vex/.mid` output works
  again.
- Removed leftover `DEBUG` `print()` statements from `converter.py`.

### Changed
- Declared `mido` as a dependency — it is the primary MIDI parser
  (`formats/mid/reader.py`) and was previously undeclared, so a clean install
  could not import the package.

## [0.2.1]
- Performance fixes; `--constrain-pitch` renamed to `--normalize-pitch`;
  `--pitch-mode` removed (its old `drop` behavior is the default).

## [0.2.0]
- Audio-to-tab pipeline; convert audio/MIDI/text formats into ASCII tablature.

## [0.1.1]
- Convert to/from `.mid`, `.abc`, `.vex`, and `.tab`.
