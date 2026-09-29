# Tab homographs: the research

gtrsnipe's `--homograph` finds one ordinary, playable tab that plays one song in one tuning
and a different song in another. It began as the executable form of an argument about
copyright: a tab records *where to put your fingers*, not *what music sounds*, and the tuning
decides the rest. This folder holds the mathematics, the literature, and the experiments that
tested how far that argument goes. How the feature itself works is in
[`../app/DESIGN-homograph.md`](../app/DESIGN-homograph.md).

## Reading order

1. **The one fact everything rests on:** [`../app/DESIGN-homograph.md`](../app/DESIGN-homograph.md)
   §1. On a single string, fret f sounds `open + f`. So two aligned songs share a tab exactly
   when their note-for-note intervals split into at most N constant classes, one per string.
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
   - [R05](results/RESULTS-R05-aswritten.md): what about real tabs, fingered as published?
6. **How it happened:** [`story/`](story/README.md).

## Where the claims stand (v0.6.9)

| claim | status | evidence |
|---|---|---|
| Two aligned melodies share a tab iff their note-for-note intervals split into ≤ N classes of constant interval (with no two simultaneous notes in a class, and each class within the fret range). | **Holds.** A theorem; the solver checks every solution by decoding it. | DESIGN-homograph §1 |
| Short passages of unrelated songs often share a tab. | **Holds.** Folk: about a third of same-rhythm 8-note phrase pairs from different tunes fit six strings and sound unrelated; 8% at 12 notes, 3% at 16. | R04 |
| String tension rarely rules a shared tab out. | **Holds.** 93–100% of sampled pairs place on a real guitar, many without a gauge change. | R04 |
| Shared tabs are comfortable to play. | **Mostly false.** 49 of 50 sampled pairs have a tab; 19 within 50 mapper points per note of A's own tab, 4 within 20, none within 5. (These counts are lower bounds.) | R04 "Playability"; F06 |
| A published tab, as written, is ambiguous. | **Tempered.** Yes for short passages: hundreds of 8-note partners. Past 16 notes, nothing unrelated-sounding fits. The fingering, not the melody, decides the partners. | R05 |
| "Any tab could be any song." | **Only** for short passages, or for a tab stripped of its tuning. | R04 + R05 |
| Log-richness and offset entropy are pseudometrics modulo transposition (fixed alignment). | **Holds, but elementary.** Present them as applications of known bounds. | theory note §3–4; literature |
| Other Rényi/Hill orders are not. | **Holds.** Explicit counterexamples; Aczél–Forte–Ng (1974). | `theory/triangle_check.py` |
| Richness is a useful melodic similarity. | **False.** Transposition-invariant Hamming wins; adding richness gains ≤ 0.006 MAP. | R03 |
| With warping-path alignment, stutter-invariant subadditive statistics of δ stay pseudometrics; entropy and 1 − C₁ don't. | **Holds** (proof and numeric check). The composition step is the discrete Fréchet distance's. Whether the general condition is published is open. | PROOF-alignment; R13 |
| Counting distinct offsets as a measure is unused in prior work. | **Holds as far as searched.** Mäkinen–Navarro–Ukkonen (2005) define the set but use only its mode. | literature §1; R13 |
| The tab homograph (one tab, two given unrelated melodies, and a solver) is new in the scholarship. | **Holds as far as searched.** Its ingredients are old (scordatura, Allen & Goudeseune 2011). StegTab (2012) is a cipher, not prior art. | literature §4 |

## Reproducing

- **Code:** [`gtrsnipe/guitar/homograph.py`](../../gtrsnipe/guitar/homograph.py) and
  [`strings.py`](../../gtrsnipe/guitar/strings.py) (the solver and the string physics), and
  [`gtrsnipe/research/`](../../gtrsnipe/research/) (the `gtrsnipe-research` CLI: `corpus`,
  `profile`, `families`, `scan`, `aswritten`). Each results doc gives its exact commands.
- **Scripts:** [`theory/triangle_check.py`](theory/triangle_check.py),
  [`theory/alignment_check.py`](theory/alignment_check.py), and
  [`results/r04_plot.py`](results/r04_plot.py).
- **Data:** the corpora (Essen, the Meertens Tune Collections, Nottingham, POP909, Lakh) are
  not in the repo, because of their licences. Each results doc names the corpora and versions
  it used.

## Open questions

- **R13:** the citation pass for the stutter-invariance principle and the Fréchet
  connection (scottvr, in progress). See PROOF-alignment, "Citations to verify".
- The complexity of the fewest-distinct-offsets warping path (d_richness) on the alignment
  grid.
- **R10–R12:** re-rhythm in the scan, the full Lakh corpus, and richness under its own
  optimal warping. See [`../dev/BACKLOG.md`](../dev/BACKLOG.md).
