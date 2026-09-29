# Tab homographs: the research

gtrsnipe's `--homograph` finds one ordinary, fingerable tab that plays one song in one tuning
and a different song in another. (Fingerable, not necessarily comfortable: see R04,
"Playability".) It began as the executable form of an argument about
copyright: a tab records *where to put your fingers*, not *what music sounds*, and the tuning
decides the rest. This folder holds the mathematics, the literature, and the experiments that
tested how far that argument goes. How the feature itself works is in
[`../app/DESIGN-homograph.md`](../app/DESIGN-homograph.md).

## Reading order

1. **The one fact everything rests on:** [`../app/DESIGN-homograph.md`](../app/DESIGN-homograph.md)
   §1. On a single string, fret f sounds `open + f`. So two aligned songs share a tab exactly
   when their note-for-note intervals split into at most N constant classes, one per string,
   with no two simultaneous notes in a class and each class within the fret range.
2. **The structure of those intervals:**
   [`theory/coupled_transposition_structure.md`](theory/coupled_transposition_structure.md).
   It covers the offset sequence δ = B − A, *richness* (its number of distinct values), and
   which statistics of δ are distances.
3. **What was already known:** [`literature/LITERATURE-offsets.md`](literature/LITERATURE-offsets.md).
4. **Distances when the alignment is optimized:** [`theory/PROOF-alignment.md`](theory/PROOF-alignment.md),
   the stutter-invariance principle.
5. **The experiments** in [`results/`](results/):
   - [R03](results/RESULTS-R03-families.md): does richness find tune families? *No.*
   - [R04](results/RESULTS-R04-scan.md): how often do real songs share a tab?
   - [R05](results/RESULTS-R05-aswritten.md): what about a real fingering, as written? (gtrsnipe's
     own wiki tabs of two pieces)
6. **How it happened:** [`story/`](story/README.md).

## Where the claims stand (2026-09-29)

| claim | status | evidence |
|---|---|---|
| Two aligned melodies share a tab iff their note-for-note intervals split into ≤ N classes of constant interval (with no two simultaneous notes in a class, and each class within the fret range). | **Holds.** A theorem; the solver checks every solution by decoding it. | DESIGN-homograph §1 |
| Short passages of unrelated songs often share a tab. | **Holds.** Folk: about a third of same-rhythm 8-note phrase pairs from different tunes fit six strings and sound unrelated; 8% at 12 notes, 3% at 16. | R04 |
| String tension rarely rules a shared tab out. | **Holds.** Folk, 7–20 notes: 93–100% of sampled pairs place on a real guitar with A in standard tuning (23–60% with no gauge change). Pop: 23–90% anchored, 93–97% when both songs retune one guitar. | R04 |
| Shared tabs are comfortable to play. | **Mostly false.** 49 of 50 sampled pairs have a tab; 19 within 50 mapper points per note of A's own tab, 4 within 20, none within 5. (These counts are lower bounds.) | R04 "Playability"; F06 |
| A real tab's fingering, as written, is ambiguous. | **Tempered.** Yes for short passages: hundreds of 8-note partners. At 24 and 32 notes, nothing unrelated-sounding fits. The fingering, not the melody alone, decides the partners. (Tested on gtrsnipe's own wiki tabs of two pieces; third-party tabs are next.) | R05 |
| "Any tab could be any song." | **Only** for short passages, or for a tab stripped of its tuning. | R04 + R05 |
| Log-richness and offset entropy are pseudometrics modulo transposition (fixed alignment). | **Holds, but elementary.** Present them as applications of known bounds. | theory note §3–4; literature |
| Other Rényi/Hill orders are not. | **Holds.** Explicit counterexamples; Aczél–Forte–Ng (1974). | `theory/triangle_check.py`; literature §5 |
| Richness is a useful melodic similarity. | **Not supported.** On tune-family retrieval, transposition-invariant Hamming wins; adding richness, entropy and reuse to the baselines gains ≤ 0.006 MAP. (One grid alignment, whole folk melodies; R12 open.) | R03 |
| With warping-path alignment, stutter-invariant subadditive statistics of δ stay pseudometrics; entropy and 1 − C₁ don't. | **Holds** (proof and numeric check), **but not new**: the proof is the discrete Fréchet distance's, and the general condition is best treated as folklore. | PROOF-alignment; theory note §7 |
| Counting distinct offsets is unused as a *music* measure. | **Holds as far as searched, in music retrieval.** Mäkinen–Navarro–Ukkonen (2005) define the set but use only its mode; R03 suggests why (as a similarity it's weak). In computer vision the same count is the standard *label cost*. | literature §1, §6; R03 |
| "Vocabulary vs. switches" is a new distinction. | **No.** It's label costs vs. the Potts smoothness term in computer vision, and finding a homograph is multi-model fitting with a label budget. (Citations from memory; to verify.) | theory note §6, §10 |
| The tab homograph (one tab, two given unrelated melodies, and a solver) is new in the scholarship. | **Holds as far as searched.** Its ingredients are old (scordatura, Allen & Goudeseune 2011). StegTab (2012) is a letter cipher: not prior art for melodic homographs, though it shares the re-keying structure. Its later academic variants are unchecked. | literature §4 |

## Reproducing

- **Code:** [`gtrsnipe/guitar/homograph.py`](../../gtrsnipe/guitar/homograph.py) and
  [`strings.py`](../../gtrsnipe/guitar/strings.py) (the solver and the string physics), and
  [`gtrsnipe/research/`](../../gtrsnipe/research/) (the `gtrsnipe-research` CLI: `corpus`,
  `profile`, `families`, `scan`, `aswritten`). The results docs give their commands.
- **Scripts:** [`theory/triangle_check.py`](theory/triangle_check.py),
  [`theory/alignment_check.py`](theory/alignment_check.py), and
  [`results/r04_plot.py`](results/r04_plot.py).
- **Data:** the corpora (Essen, the Meertens Tune Collections, Nottingham, POP909, Lakh) are
  not in the repo, because of their licences. The results docs name the corpora they used.

## Open questions

- **R13:** the citation pass for the stutter-invariance principle and the Fréchet
  connection (scottvr, in progress). See PROOF-alignment, "Citations to verify".
- The complexity of the fewest-distinct-offsets warping path (d_richness) on the alignment
  grid.
- **R10–R12:** re-rhythm in the scan, the full Lakh corpus, and richness under its own
  optimal warping. See [`../dev/BACKLOG.md`](../dev/BACKLOG.md).
- **Third-party tabs as written** (R05's natural next input), kept local for copyright
  reasons.
- **Phrase-level tune-family retrieval** (R03 used whole melodies), and the structure note's
  untested §6 hypothesis: that low richness with high reuse marks sequences, echoes or
  call-and-response at a fixed interval.
- **StegTab's later academic variants**, not yet examined.
