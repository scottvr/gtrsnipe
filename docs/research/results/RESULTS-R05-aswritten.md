# R05: real fingerings, as written

Run on 2026-09-26/27 with `gtrsnipe-research aswritten` (gtrsnipe 0.6.5), against every cached
corpus: Essen, MTC-FS-INST, Nottingham, POP909 and Lakh Clean. For Lakh that includes skyline
melodies. The tabs are gtrsnipe's own, from its wiki (none is a third-party tab); they're in
[`examples/aswritten/`](../../../examples/aswritten/). Reproduce with:

```bash
R="--corpora essen mtc-fs nottingham pop909 lakh-clean"
gtrsnipe-research --data DIR aswritten examples/aswritten/asturias-v*.tab \
    examples/aswritten/bach-prelude-measure-*.tab $R --json small.json
gtrsnipe-research --data DIR aswritten examples/aswritten/bach-prelude-full.tab $R --solve 15 --json bach-full.json
# the 32-note tallies for the whole Prelude (every hit kept):
gtrsnipe-research --data DIR aswritten examples/aswritten/bach-prelude-full.tab $R \
    --lengths 32 --keep 1000 --solve 0 --json bach-full-32.json
```

## The question

R04 let the solver choose which notes share a string. A real tab has already chosen.
**Can a tab's own fingering, exactly as written, be retuned into a different song?** It can
only if every note the tab puts on one string moves by the same interval (per-string constancy),
which is far stricter than R04's "richness ≤ 6".

## Method

- **The tabs.**
  - Bach's Cello Suite No. 1 Prelude: the wiki's full 654-note transcription, plus one
    measure in two fingerings.
  - The six successive Asturias transcriptions from the wiki, v1 (the "unplayable
    abomination") to v6, the option set whose output matches how you play it by ear.
  - All are public domain.
- **Timing.** ASCII tab carries only rough timing (the column spacing wobbles at barlines and
  two-digit frets). Both pieces are steady sixteenths, so each tab is read as steady notes and
  compared with corpus passages of evenly spaced notes: 1.76 million 8-note windows, 1.0 million
  16-note, 0.67 million 32-note. Chord onsets are skipped.
- **The test.** For every tab window and corpus window of the same length: is b − a constant on
  each of the tab's strings?
- **Categories.**
  - *Trivial*: the pair has no more distinct (a, b) pitch pairs than strings used. Then each
    string maps one pitch to one pitch, and the tab says only *which string to pluck*.
  - *Itself*: a plain transposition of the tab's own passage.
  - *Unrelated-sounding*: the R04 criteria. C₁ ≤ ½, contour agreement ≤ 0.6, and neither
    passage mechanical.
- **Physics.** The best hits go through the homograph solver's as-written check, with string
  physics.

## Results

### As written is about 10,000× stricter than a free fit

At 8 notes, 52–76% of same-length candidates fit *some* tab (R04's criterion), but only
0.004–0.02% fit an actual Asturias fingering.

### Fingering decides the partners: Asturias, one melody, six tabs

Non-trivial as-written hits (per million candidates in brackets):

| version | strings | 8 notes | 12 | 16 | 24 |
|---|---|---|---|---|---|
| v1 (first autotranscription) | 5 | — (doubled unisons break every window) | — | — | — |
| v2 | 3 | 1,448 (37) | 1 (0.04) | 0 | 0 |
| v3 | 2 | 2,714 (70) | 0 | 0 | 0 |
| v4 | 4 | 5,526 (142) | 40 (1.75) | 2 (0.14) | 0 |
| v5 | 4 | 2,772 (71) | 69 (3.0) | 0 | 0 |
| **v6 (the by-ear fingering)** | 3 | 6,194 (92) | 279 (6.5) | 23 (0.75) | 0 |

- The same melody's tabs differ several-fold in how many other passages they can become, and
  in which ones.
- Unrelated-sounding hits exist only at 8 notes (v4: 1,919; v5: 591; v6: 1,512).
- No version has any as-written partner at 24 notes.

### The fingering decides: one Bach measure, three fingerings

The same 16 notes, fingered three ways, all from the wiki's Bach page:

| fingering | strings | as-written hits at 8 notes (per million) | trivial | non-trivial |
|---|---|---|---|---|
| v0.2's default (the wiki's first step: all on the A string) | 1 | **0**, beyond transpositions of the passage itself | — | 0 |
| string-switch penalty removed (`--string-switch-penalty 0`, the wiki's second step) | 3 | 1,292,404 (81,373: 8% of all candidates) | **all** | 0 |
| final options (`--sweet-spot-low 0 --sweet-spot-high 4 --string-switch-penalty 0`: "exactly how I would have transcribed it manually") | 2 | 15,261 (961) | 0 | 15,261 |

- **One string pins the music down completely.** Every note shares one offset, so only a
  transposition of the passage fits: the tab says as much as the notes themselves.
- **One pitch per string pins down almost nothing.** Any passage that repeats three pitches
  in the same pattern fits, so the tab constrains nothing but the pattern.
- **The final fingering sits in between.** Two pitches share a string, and the hit rate
  drops 85× from the second fingering. Even then every hit is another repetitive figure;
  none sounds unrelated.

(An earlier version of this section called the second fingering "default mapper scoring".
It is the wiki's second step, with the string-switch penalty removed. The first-step
fingering was added on 2026-09-28; rerunning the other two reproduced their counts exactly.)

### The whole Prelude, as written

| notes | compared | as written | trivial | non-trivial (per million) | unrelated-sounding |
|---|---|---|---|---|---|
| 8 | 1.14 billion | 8.87 M | 8.56 M | 308,946 (271) | 13,562 |
| 12 | 817 M | 3.19 M | 3.11 M | 80,050 (98) | 191 |
| 16 | 654 M | 1.38 M | 1.36 M | 29,031 (44) | 29 |
| 24 | 506 M | 323,578 | 319,053 | 4,525 (8.9) | 0 |
| 32 | 419 M | 40,278 | 39,799 | 479 (1.1) | 0 |

- Arpeggiated figuration makes most matches trivial (97% at 8 notes).
- Non-trivial alternatives persist to 32 notes: 479 hits, from 26 works, including *Una
  Paloma Blanca*, the Toccata and Fugue in D minor, the Brandenburg Concerto No. 2 finale and
  *Liberian Girl*. Counted once per tab window and corpus melody, they are 53 distinct matches.
- **At 32 notes, all 53 are themselves mechanical figuration, and 51 of the 53 also follow
  Bach's contour** (agreement > 0.6). The only passages this fingering can become at that length
  are other broken-chord figures, nearly all moving the same way. (An earlier version said "475
  of the 479"; the per-hit contour values behind that count weren't saved, and the rerun keeps
  one hit per window and melody.)
- **Physics isn't the limit here either.** The solver confirmed every hit it checked: 15 for
  the Prelude, each needing one or two strings re-gauged, and 10 per Asturias version and Bach
  measure.

## What this says for the argument

- **Short passages: a fingering as written really is ambiguous.** Hundreds of passages from
  other songs fit a real 8-note fingering exactly, including ones that sound unrelated.
- **Long passages: a real fingering, with its tuning stated, nearly pins the music down.**
  Beyond 16 notes, nothing unrelated-sounding fits either piece's actual fingering. What still
  fits past 24 notes is look-alike figuration.
- **Arrangement choices matter.** Which other music a tab can become depends on the fingering
  (Asturias v2–v6; the two Bach measures), not on the melody alone. A fingering that gives
  each string one pitch (common in arpeggio writing) carries almost no melodic information.
- **Combined with R04:** a *melody* shares some tab with many others; a *published tab, as
  written*, shares its exact fingering with few, and for long passages only with passages that
  sound alike. The strong form of the claim ("any tab could be anything") holds for short
  passages and for a tab stripped of its tuning, not for a long, fully specified tab.

## Caveats

- These tabs were all made by gtrsnipe, including v6 and the tuned Bach measure: they are the
  output of option sets scottvr tuned until the result matched how he plays it. None was
  collected from a third-party tab site. Third-party tabs are the natural next input.
- Timing is taken as steady notes. That is true of these two pieces, not of tabs in general.
- **Checked after v0.6.19's tab-reading fix (2026-10-05).** That release changed how a tab's
  onset times are read where it has two-digit frets, which moved the decoded onsets of
  Asturias v1, v2 and v5 (not the Bach tabs or v3, v4, v6). Re-running this test on those
  three gave the same output line for line: the test uses the notes' order, strings and
  pitches, and only asks that the *corpus* passage be evenly spaced. The numbers above stand.
- Single notes only. Chord onsets break windows, which is why v1 has none.
- "Unrelated-sounding" is the R04 proxies (C₁, contour, mechanical), not a listening test.
- The corpora contain neither piece (Lakh has other Bach, not this suite), so no hit is
  "the piece itself". The "itself" transpositions found are stock figures shared with other
  pieces.
