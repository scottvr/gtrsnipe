# State of the docs (H06), 2026-09-28

Every doc was checked against the code at v0.6.9 and against the other docs, by three
read-only review agents: the wiki, the README and app docs, and the research docs. Claude
spot-checked the serious claims (failing flags, rejected tunings, the Gemini credit, trial
counts, scope of the percentages), and they held. All R03–R05 numbers match the raw outputs;
the problems are framing, currency and provenance.

**Severity:** WRONG (misleads a reader today) · STALE (outdated but harmless) · OVERCLAIM
(stronger than the evidence) · INCONSISTENT (disagrees with another doc) · MISSING (should
say something it doesn't).

**How to approve:** by ID, e.g. "all except SN-*, LI-9". Items marked *(Claude's own)* are in
text Claude wrote on 2026-09-28 and will be fixed unless you object.

## Decisions that are yours

1. **The structure note needs a revision 2** (SN-*). It's your document. Should Claude write
   rev 2 (a new header listing the outcomes, "Answered by" boxes in §0, §6, §11, and §10
   brought in line with the survey) for you to edit, or do you want to write it?
2. **The literature survey's "Suggested wording (for the paper)"** predates R03 and R07
   (LI-3). Claude rewrites it, or you do, since it's your paper?
3. **The README's pasted `--help` block and options list** are about 45 options behind (RM-1,
   RM-8). Regenerate them from `gtrsnipe --help`, or cut them and point to `--help`?
   *Recommendation: cut the pasted block, keep a short curated options list.*
4. **Six tunings are listed but rejected by `--tuning`** (DADGAD, DROP_B, D_STANDARD, OPEN_D,
   OPEN_E, SEVEN_STRING_DROP_A; RM-13). Fix the code (add them to `TUNING_CHOICES`, a
   one-line bug fix and a patch release) or the docs? *Recommendation: the code.*
5. **Gemini.** `collision_plot_template.py` says "Contributed by Gemini via scottvr": a
   third LLM that no provenance note or story chapter mentions (CP-1). How much of a role
   did it play? (✎ for chapter 10.)
6. **The wiki** (WK-*). Its example pages were made with v0.2's greedy mapper, and the
   default (Viterbi) output now differs: Asturias steps 2–5 no longer reproduce, though the
   final tab does. *Recommendation:* rewrite page 1 (the reference page: six factual errors
   and no mention of the optimizer); give the example pages and the v0.2.0 log a "written for
   v0.2; add `--optimizer greedy` to replay" banner plus targeted fixes; expand page 0 with
   the features since v0.3. These are fixes to `docs/wiki/`; the live GitHub wiki is a
   separate repo, updated only when you say.
7. **The local HTML exports** (`LITERATURE-offsets.html`, `coupled_transposition_structure.html`)
   still have the old StegTab row and `docs/dev/` paths. Regenerate them, or delete them?

## Code issues found in passing (→ parking lot, not this pass)

- The help text of `--no-constrain-frequency` and `--no-pre-quantize` describes the opposite
  of what they do; `--min-note-override`'s help cites a flag that doesn't exist.
- `--bass` overrides any `--tuning`, including `BASS_DROP_D`.
- `gtrsnipe/player/clock.py` is dead code; `sink.py`'s docstring still calls CursesSink "later
  phase"; `config.py` says greedy is kept "for one release"; `research/cli.py`'s docstring
  puts `--data` after the subcommand (which fails).
- `alignment_check.py` defaults to 3,000 trials; PROOF cites 5,000 (PA-1 fixes the doc).
- `--tapping-run-threshold`'s help has an off-by-one (runs *longer* than N count).
- All of these are now in the parking lot.

---

## README.md

| ID | where | issue | fix |
|---|---|---|---|
| RM-1 | L336–352 | STALE/WRONG: the pasted help block shows `-o` as required and lacks ~45 options added since v0.3.0 | decision 3 |
| RM-2 | L404–405 | STALE: `-o` is repeatable, optional with `--play`/`--analyze`/`--solve-tuning`/`--homograph`; `.chords.md` writes a chord sheet | current help text |
| RM-3 | L432–433 | WRONG: `--constrain-frequency` doesn't exist; constraining is the default, `--no-constrain-frequency` turns it off | document the real flag |
| RM-4 | L467 | WRONG: `--pre-quantize` doesn't exist; `--no-pre-quantize` skips the default pass | same |
| RM-5 | L469 | WRONG: `--quantization-resolution` choices miss 0.025; default 0.125 not stated | fix the list |
| RM-6 | L486 | WRONG: `C_SHARP` isn't a choice; it's `C_SHARP_STANDARD` | fix |
| RM-7 | L494–496 | WRONG: "requires --constrain-frequency" | "ignored with `--no-constrain-frequency`" |
| RM-8 | L398–496 | MISSING: `--first-note-is-downbeat`, `--velocity-cutoff`, `--dynamic-quantize`, custom-tuning and physics options, `--solve-tuning`, `--max-strings`, `--sustain`; `--sweet-spot-bonus` default | decision 3 |
| RM-9 | L505 | WRONG: `--stem --stem-name bass` fails; `--bass` also silently overrides `--tuning DROP_D` | `--stem-track bass --tuning BASS_DROP_D` |
| RM-10 | L511 | WRONG: `--stem` fails | `--stem-track guitar` |
| RM-11 | L529 | WRONG: broken wiki URL (`/wik/`) | use the L18 URL |
| RM-12 | L535–556 | WRONG: `--list-tunings` output in the old high→low order; DROP_B shows 5 notes; C_SHARP_STANDARD missing | paste the current output |
| RM-13 | L532 | WRONG: lists six tunings that `--tuning` rejects | decision 4 |
| RM-14 | L243 | WRONG: step mode "press any key to advance" | `.` steps, space plays, q quits |
| RM-15 | L325–327 | WRONG: chord diagrams are a generated compact voicing, not "as voiced in the input" | describe the generated voicing |
| RM-16 | L331–332 | WRONG: `--prefer-open` doesn't change chord diagrams (tested; see C02) | remove, or point to C02 |
| RM-17 | L365–367 | STALE: greedy "kept for one release" (still there at 0.6.9) and "matches pre-0.3.0 output" (no longer exact) | "kept for reproducing older fingerings" |
| RM-18 | L209 | WRONG: `gtrsnipe-research corpus build essen --data …` fails; `--data` goes before the subcommand | reorder |

## examples/

| ID | where | issue | fix |
|---|---|---|---|
| EX-1 | `examples/homograph/*.report.txt` | STALE: reports predate F06 (no "Playability" line); the tabs regenerate byte-identical | regenerate the reports |
| EX-2 | homograph README L15–20 | MISSING: no playability (mary-london ≈ 90 points/note, frets to 22; oldmac-twinkle ≈ 4) | add a column |
| EX-3 | homograph README L32–38 | MISSING: the regenerate commands don't save the reports | append `> NAME.report.txt` |

`examples/aswritten/README.md` is fully accurate.

## docs/app/DESIGN-viterbi-mapper.md

| ID | where | issue | fix |
|---|---|---|---|
| VM-1 | L3 | STALE: no status line; reads as a plan | "Status: implemented in v0.3.0" |
| VM-2 | §1 L22–29 | WRONG: "what the code does today… greedy" is false since v0.3.0 | retitle "Before v0.3.0" |
| VM-3 | throughout | STALE: `mapper.py:NNN` line numbers are pre-0.3.0 | cite function names |
| VM-4 | §3 | MISSING: the `_positions_for` hook (used by the homograph solver) and `last_path_score` (used by `--analyze` and discomfort) | add a "Since v0.3.0" section |
| VM-5 | L244–247 | WRONG: `candidate_cap` was never added | drop it |
| VM-6 | L252–255 | STALE: golden files "once Viterbi lands" | point to H01 |
| VM-7 | §2.3, §5, §7 | STALE: the checklist reads as done; the landmine guard and the exact-tie tests don't exist | mark done / not done |
| VM-8 | L48, L229 | MISSING: "K ≤ 720" assumes 6 strings | n!/(n−k)! |
| VM-9 | L22, L244, L255 | MISSING: "the whitepaper", "(D3)", "Risk R1" refer to the archived plan | link it |

## docs/app/DESIGN-unified-io.md

| ID | where | issue | fix |
|---|---|---|---|
| IO-1 | L3 | STALE: status says v0.5.0 only | add v0.6.8 note-offs, v0.6.9 instrument default |
| IO-2 | L29 | MISSING: note-off at each note's own end; program and channel from the MIDI file | update the row |
| IO-3 | L37–38 | STALE: the loop also wakes at the next release (a heap with per-pitch generations) | describe it |
| IO-4 | L43–45 | MISSING: the Driver's `release` callback; `fire` uses `strike` when frames carry ends | add |
| IO-5 | L49 | WRONG: "space pause/resume (paused: step)"; space always resumes, `.`/`,` step | fix |
| IO-6 | L51 | WRONG: a space-key page-down collision that doesn't exist (no paging yet) | delete, or mark as P04 |
| IO-7 | L55–56 | MISSING: `add_tab_input_args`, the profile helpers, the custom-tuning helpers | complete the list |
| IO-8 | L65 | STALE: `gtrsnipe-play` calls `run_player` directly | reword |
| IO-9 | L69–70 | WRONG: "audio still sustains to the next onset" (fixed in v0.6.8) | "done in v0.6.8", with `--legato`, `--sustain` |
| IO-10 | L71–72 | STALE: deferred items shipped (F03) or moved to the backlog | BACKLOG IDs |

## docs/app/DESIGN-homograph.md

| ID | where | issue | fix |
|---|---|---|---|
| HG-1 | §5 L221–227 | STALE: "Phase 3, in the wild" reads as future; it shipped as R04 (phrase and window buckets) and R05 (gtrsnipe's own tabs) | "Done: R04, R05; open: third-party tabs, R10" |
| HG-2 | §5 | MISSING: limits the backlog cites §5 for (middle-mode split classes, greedy chord-voice pairing, EXTRA_STRINGS, no re-rhythm in the scan) | list with IDs |
| HG-3 | L219 | STALE: ENUM_CAP applies to anchored *and* middle | fix |
| HG-4 | §1 L52–56 | MISSING: links to the theory note, PROOF-alignment, and R03's verdict | one-line cross-reference |
| HG-5 | L10–12 | MISSING: `gtrsnipe/research/`, its tests, and `docs/research/README.md` | add |
| HG-6 | §3 L119–121 | STALE: "extended range (7-string) 27″" is ambiguous; SEVEN_STRING_STANDARD stays 25.5″ | clarify |
| HG-7 | L5–6 | OVERCLAIM: "an ordinary, fretted, playable tab"; since F06, most are fingerable but not comfortable | "fingerable" plus a pointer |

## docs/README.md *(Claude's own)*

| ID | where | issue | fix |
|---|---|---|---|
| DM-1 | L18 | STALE: the greedy mapper chose per chord, and is still available | reword |
| DM-2 | L19 | WRONG: no separate pager ships | "files and the interactive player" |
| DM-3 | L34 | WRONG: the README embeds none of the logos | "logo assets" |

## docs/research/README.md *(Claude's own)*

| ID | where | issue | fix |
|---|---|---|---|
| RR-1 | L3 | OVERCLAIM: "ordinary, playable tab" | "fingerable" (comfort: R04) |
| RR-2 | L13–14 | OVERCLAIM: the theorem without its simultaneity and fret-range conditions | add them |
| RR-3 | L25, L36 | OVERCLAIM: "published tabs"; R05 used gtrsnipe's own wiki tabs of two pieces | say so (also BACKLOG L47, story) |
| RR-4 | L34 | INCONSISTENT: 93–100% is folk, anchored, 7–20 notes; pop anchored is 23–90% | scope it |
| RR-5 | L36 | OVERCLAIM: "past 16 notes" was measured at 24 and 32; "not the melody" drops "alone" | fix |
| RR-6 | L40 | OVERCLAIM: "False" is stronger than one grid alignment on folk; R12 open | "Not supported" |
| RR-7 | L42 | INCONSISTENT: cites R13 (the wrong item) | "literature §1; R03" |
| RR-8 | L43 | OVERCLAIM: StegTab without "for melodic homographs" and the unchecked variants | restore the qualifiers |
| RR-9 | L39 | MISSING: literature §5 for the Rényi argument | add |
| RR-10 | L50–56 | WRONG: "each results doc gives its commands and versions"; R04/R05 lack some | fix R04/R05 (R4-5, R5-3) and soften |
| RR-11 | L58–65 | MISSING: third-party tabs, phrase-level retrieval, the §6 sequence/echo hypothesis, StegTab variants | add |

## docs/research/theory/coupled_transposition_structure.md (decision 1)

| ID | where | issue | fix |
|---|---|---|---|
| SN-1 | L3–14 | STALE: the header reads as current; R06, R07 and R03 have settled its open points | rev 2 header listing the outcomes |
| SN-2 | §0 L36–42 | STALE: "the part we could not find named… an empirical question (§11)" has no answer note | "Answered by R03/R06" box |
| SN-3 | §6 | STALE: "the possibly-new piece" with no update; only tune families were tested (sequences, echoes untested) | update box; retitle |
| SN-4 | §6 L235–237 | OVERCLAIM: that Allali et al. charge a *return* is inferred, not confirmed | mark unconfirmed; add to R13 |
| SN-5 | §7 box | INCONSISTENT: the offset range is *twice* a Fréchet distance; "3-note counterexample" (it's 1, 2 and 2 notes; the CHANGELOG repeats it) | fix both |
| SN-6 | §8 | STALE: "only TV sees the size" (J and R do too) | fix |
| SN-7 | §10 | INCONSISTENT/MISSING: P2 is the unaligned analogue; SIMILE `diff` is TV's prior art; Tao is a contrast, not the source; Straus, Allen & Goudeseune absent | align with the survey |
| SN-8 | §10, refs | STALE: "worth reading before any claim" is done; references "from memory" now verified in the survey; Meilă verified nowhere | copy the verified details; flag Meilă |
| SN-9 | §11 | STALE: no "answered" box; MTC-ANN's size now known (360 melodies, 26 families); what R03 skipped | update box; pointer to R04 |
| SN-10 | L110, L392, L409 | MISSING: cites "the original draft" and its §16–17, which isn't in the repo | say so |
| SN-11 | whole | MISSING: provenance (who drafted, who reviewed) | a Review note like PROOF's |

## docs/research/theory/PROOF-alignment.md

| ID | where | issue | fix |
|---|---|---|---|
| PA-1 | L22–24 | INCONSISTENT: "5,000 random triples", but the script defaults to 3,000 (5,000 reproduces the numbers) | "run `alignment_check.py 5000`" |
| PA-2 | L229–234 | OVERCLAIM: Allali "charges a return", only inferred | hedge; add to Citations to verify |
| PA-3 | L272–274 | MISSING: the NP-hardness of minimum-label paths has no citation | add a verify row |
| PA-4 | L283–290 | MISSING: who proposed the general principle, the Fréchet link, J/R and ⌈R/2⌉ | name them (✎ scottvr for the ChatGPT side) |

## docs/research/literature/LITERATURE-offsets.md

| ID | where | issue | fix |
|---|---|---|---|
| LI-1 | L5 | MISSING: no revision note for the 2026-09-28 StegTab correction | add |
| LI-2 | L12–25 | STALE: "using it as a measure looks new… claim the use", written before R03 | add an R03 note |
| LI-3 | L143–156 | STALE: the suggested paper wording predates R03 and R07 | decision 2 |
| LI-4 | L94 | MISSING: StegTab has no URL, title or access date; the academic variants are unchecked | complete it (✎ URL) |
| LI-5 | several rows, §5 | MISSING: DOI only, no check level, including Rahmatian's quote and Aczél–Forte–Ng | mark each row's level |

## docs/research/results/

| ID | where | issue | fix |
|---|---|---|---|
| R3-1 | R03 L106 | INCONSISTENT: at scale, richness falls below S and TV | reword |
| R3-2 | R03 L21 | INCONSISTENT: the ≈ in the ordering chain is from MTC-FS, not ANN-64 | say so |
| R3-3 | R03 L89 | INCONSISTENT: chance MAP is 0.0006, not 0.001 | fix |
| R4-1 | R04 L68 | INCONSISTENT: no-restring share is 23–60%, not "a quarter to a half" | fix |
| R4-2 | R04 L72 | STALE: "rhythm and offsets bind, not the strings" is true for existence; comfort binds too | add |
| R4-3 | R04 L90, L103 | INCONSISTENT: "— means not sampled", but 24 notes had 2 pairs | "fewer than 10 pairs" |
| R4-4 | R04 L153 | INCONSISTENT: the median top fret 19 is over the 8 tabs from the shallower search | say so |
| R4-5 | R04 L142–159 | MISSING: Playability has no command, seed or saved output | add |
| R4-6 | R04 L178–179 | STALE: "ranking by playability is parked" (done in F06) | point to Playability |
| R4-7 | figures, `r04_plot.py` | OVERCLAIM: the legend says "playable"; it means string tension is OK | relabel "placeable", regenerate |
| R5-1 | R05 L9–10 | OVERCLAIM: "a published tab" up front; they're gtrsnipe's wiki tabs | say so |
| R5-2 | R05 L88–90 | OVERCLAIM: the "past 16 notes" breakdown is for 32 notes; 475 of 479 follow the contour | scope it |
| R5-3 | R05 | MISSING: no reproduce block; the 479/26 and 475 tallies aren't in the saved output | add the commands and the tally |
| R5-4 | R05 L46–67 | INCONSISTENT: bracket convention flips between tables | unify |
| R5-5 | R05 L114 | MISSING: "third-party tabs are next" is tracked nowhere | add to the backlog |
| R5-6 | R05 L66–69; `examples/aswritten/README.md` L9 | **WRONG:** the measure labelled "default mapper scoring" is the wiki's second step, made with `--string-switch-penalty 0` (wiki page 3, L28–37). The true default put the whole passage on the A string. The finding stands; the label doesn't | relabel; optionally run `aswritten` on the true default measure too |
| CP-1 | `collision_plot_template.py` | STALE/MISSING: "R04 is meant to produce the real numbers" (it did: `r04_plot.py`); Gemini's credit appears in no provenance note | update; decision 5 |

## docs/research/story/ *(Claude's own)*

| ID | where | issue | fix |
|---|---|---|---|
| ST-1 | README L32; ch. 7 L11 | OVERCLAIM: "published tabs" | "gtrsnipe's wiki tabs" |
| ST-2 | ch. 10 | MISSING: Gemini | ✎ after decision 5 |
| ST-3 | ch. 7 | WRONG: "One Bach measure with gtrsnipe's default settings gives every string a single pitch" (R5-6) | "with the string-switch penalty removed" |
| ST-4 | ch. 8 "The weights" | STALE: "Asturias needs a long command line" was true of v0.2's greedy mapper; under Viterbi the step-5 flags already give nearly the final tab | add that; it strengthens the "learn the weights" point less than it seemed |

## docs/wiki/ (decision 6)

The audit rebuilt each example's input from the wiki's own tab and re-mapped it with the
documented flags. With `--optimizer greedy` the rebuilt inputs reproduce the wiki's output
exactly (Mr Crowley 70/70, Asturias steps 2–6, the full Bach tab 654/654), so the method
works; the differences below are the Viterbi mapper's, not noise.

| ID | page | issue | fix |
|---|---|---|---|
| WK-1 | 1 L3–6 | STALE: source paths moved (`core/config.py`, `guitar/mapper.py`, `add_mapper_args()`) | update |
| WK-2 | 1 L14 | WRONG: `C_SHARP` (it's `C_SHARP_STANDARD`); PIANO missing | current list; point to `--list-tunings` |
| WK-3 | 1 §1 | MISSING: `--tuning-pitches`, `--drop-low-string`, `--num-strings`, `--bass`, `--capo` | add rows |
| WK-4 | 1 §2 | MISSING: `--optimizer`; since v0.3.0 the default optimizes the whole song | add a row and a paragraph |
| WK-5 | 1 L26 | WRONG: `--movement-penalty` is per fret the hand's average position moves, not per semitone | fix |
| WK-6 | 1 L47 | WRONG (minor): `--tapping-run-threshold` needs runs *longer* than N (default 2 → 3+), `--single-string` only | fix (the code's help has the same off-by-one) |
| WK-7 | 1 L58 | WRONG: 0.125 beats is a 32nd note, not an 8th; the allowed values are a fixed list | fix |
| WK-8 | 1 §2–5 | MISSING: `--mono-lowest-only`, the barre and let-ring weights, `--diagonal-span-penalty`, `--single-string`, `--no-pre-quantize`, `--dynamic-quantize` | add rows |
| WK-9 | 1 L75–83; 2 L5, L80; 3 L54 | WRONG: positional `input.mid output.tab` is rejected | `-i … -o …` |
| WK-10 | 1 L85–90 | MISSING: profiles (`--save-args`/`--profile`), `--analyze`, `--play --view tab` for iterating | add 2–3 lines |
| WK-11 | 1 L93; 2 L49 | WRONG: `--debug` scoring output appears only with `--optimizer greedy` | say so |
| WK-12 | 1 L97–118; 2 L20–46 | STALE: the Mr Crowley tabs are greedy output; under Viterbi 22 of 70 events differ (the `--ignore-open` point survives) | version note or regenerate |
| WK-13 | 2 L6–18, L81–91 | STALE: console transcript and tab header formats changed | trim or regenerate |
| WK-14 | 2 L77 | WRONG: notes below E2 are *dropped*, not transposed, unless `--normalize-pitch` | fix |
| WK-15 | 2 L77 | WRONG: `--tuning BASS_* --num-strings 5` fails; no 5-string bass tuning is named | `--tuning-pitches B0,E1,A1,D2,G2` |
| WK-16 | 3 L5–26, L57–349 | STALE: under Viterbi ~11 of 48 events of the default excerpt differ (still too much single-string playing, so the complaint holds); the full tuned tab differs by one note | version note |
| WK-17 | 4 L22–112 | STALE (historical): steps 2–5 no longer reproduce under Viterbi (the "awful 9-area" openings never appear; the D-to-G jump behind `--diagonal-span-penalty` doesn't occur); the final tab reproduces under both | banner with `--optimizer greedy` |
| WK-18 | 4 L89 | STALE: "considers the previous two notes" only with let-ring and diagonal span set; Viterbi weighs the whole passage | clarify |
| WK-19 | 4 L44; end | MISSING: presets now exist as profiles; hearing the ringing notes (`--play --sustain string`) | add |
| WK-20 | 5 L11 | WRONG: `--pre-quantize` is rejected (it's the default now) | drop the flag |
| WK-21 | 5 L1–3; v0.2.0 L8–15, L33, L48 | STALE (historical): Basic-Pitch and `--remove-fx` were removed in v0.3.0 | banner |
| WK-22 | 5 whole | MISSING: `pip install 'gtrsnipe[audio]'`, and `[separation]` for `--stem-track` | add |
| WK-23 | v0.2.0 L28, L40 | WRONG: the commands no longer do what the text says (`--stem`, `--stem-name`, `--constrain-frequency`) | fix or strike |
| WK-24 | FAQ L23, L39 | STALE: "the highest-scoring fingering wins" describes greedy | add a Viterbi paragraph |
| WK-25 | FAQ L43–48, L57 | WRONG: diagonal span and let-ring are opt-in; let-ring rewards any unstruck string, not only open ones; open-string preference needs `--prefer-open` | fix |
| WK-26 | README (snapshot) | MISSING: doesn't say the pages predate v0.3.0; the *live* wiki's Asturias page uses `--count-fret-span-across-neighbors`, now rejected | add the caveat; fix the live page |
| WK-27 | 0 | MISSING: nothing since v0.3 (player, charts, profiles, custom tunings, `--solve-tuning`, `--homograph`, `--analyze`) | "since v0.3" paragraph and a page index (H03) |

Home and _Footer are accurate. More code bugs found here: the `--tapping-run-threshold` help
has the same off-by-one; `examples/aswritten/README.md` mislabels the Bach measure (R5-6).
