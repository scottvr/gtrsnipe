# R05: real fingerings, as written

Run on 2026-09-26/27 with `gtrsnipe-research aswritten` (gtrsnipe 0.6.5), against every cached
corpus: Essen, MTC-FS-INST, Nottingham, POP909 and Lakh Clean. For Lakh that includes skyline
melodies. The tabs are in [`examples/aswritten/`](../../examples/aswritten/).

## The question

R04 let the solver choose which notes share a string. A published tab has already chosen.
**Can a tab's own fingering, exactly as written, be retuned into a different song?** It can
only if every note the tab puts on one string moves by the same interval (per-string constancy),
which is far stricter than R04's "richness ≤ 6".

## Method

- **The tabs.**
  - Bach's Cello Suite No. 1 Prelude: the wiki's full 654-note transcription, plus one
    measure in two fingerings.
  - The six successive Asturias transcriptions from the wiki, v1 (the "unplayable
    abomination") to v6, the fingering you play by ear.
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

Non-trivial as-written hits per million candidates (counts in brackets):

| version | strings | 8 notes | 12 | 16 | 24 |
|---|---|---|---|---|---|
| v1 (first autotranscription) | 5 | — (doubled unisons break every window) | — | — | — |
| v2 | 3 | 37 | 0.04 (1) | 0 | 0 |
| v3 | 2 | 70 | 0 | 0 | 0 |
| v4 | 4 | 142 | 1.75 (40) | 0.14 (2) | 0 |
| v5 | 4 | 71 | 3.0 (69) | 0 | 0 |
| **v6 (the by-ear fingering)** | 3 | 92 | 6.5 (279) | 0.75 (23) | 0 |

- The same melody's tabs differ several-fold in how many other passages they can become, and
  in which ones.
- Unrelated-sounding hits exist only at 8 notes (v4: 1,919; v5: 591; v6: 1,512).
- No version has any as-written partner at 24 notes.

### A fingering can make the frets meaningless: one Bach measure, two fingerings

| fingering | strings | as-written hits at 8 notes (per million) | trivial | non-trivial |
|---|---|---|---|---|
| default mapper scoring | 3 | 1,292,404 (81,373: 8% of all candidates) | **all** | 0 |
| by hand ("how I'd transcribe it") | 2 | 15,261 (961) | 0 | 15,261 |

In the default fingering each string carries one pitch. Any passage that repeats three pitches
in the same pattern fits, so the tab constrains nothing but the pattern. The hand fingering puts
two pitches on one string, and the hit rate drops 85×. Even then every hit is another
repetitive figure; none sounds unrelated.

### The whole Prelude, as written

| notes | compared | as written | trivial | non-trivial (per million) | unrelated-sounding |
|---|---|---|---|---|---|
| 8 | 1.14 billion | 8.87 M | 8.56 M | 308,946 (271) | 13,562 |
| 12 | 817 M | 3.19 M | 3.11 M | 80,050 (98) | 191 |
| 16 | 654 M | 1.38 M | 1.36 M | 29,031 (44) | 29 |
| 24 | 506 M | 323,578 | 319,053 | 4,525 (8.9) | 0 |
| 32 | 419 M | 40,278 | 39,799 | 479 (1.1) | 0 |

- Arpeggiated figuration makes most matches trivial (97% at 8 notes).
- Non-trivial alternatives persist to 32 notes: 479 hits in 26 works, including *Una Paloma
  Blanca*, the Toccata and Fugue in D minor, the Brandenburg Concerto No. 2 finale and *Liberian
  Girl*.
- **Every one of them is itself mechanical figuration, and 475 of the 479 also follow Bach's
  contour** (agreement > 0.6). Past 16 notes, the only passages this fingering can become are
  other broken-chord figures moving the same way.
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

- These tabs were made by gtrsnipe (v6 is a human fingering, made by hand-tuning the mapper),
  not collected from third-party tab sites. Third-party tabs are the natural next input.
- Timing is taken as steady notes. That is true of these two pieces, not of tabs in general.
- Single notes only. Chord onsets break windows, which is why v1 has none.
- "Unrelated-sounding" is the R04 proxies (C₁, contour, mechanical), not a listening test.
- The corpora contain neither piece (Lakh has other Bach, not this suite), so no hit is
  "the piece itself". The "itself" transpositions found are stock figures shared with other
  pieces.
