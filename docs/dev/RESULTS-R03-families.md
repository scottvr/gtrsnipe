# R03: does the offset profile find tune families?

The experiment in §11 of [`coupled_transposition_structure.md`](coupled_transposition_structure.md),
run 2026-09-26 with `gtrsnipe-research families` (gtrsnipe 0.6.3). Reproduce with:

```bash
gtrsnipe-research --data DIR families mtc-ann --grid 64 --json r03-ann-64.json   # also --grid 32, 128
gtrsnipe-research --data DIR families mtc-fs --queries 1000 --bootstrap 1000     # the scale check
```

## Verdict

**No gain.** Richness is a weak tune-family similarity measure. Adding richness, entropy and
reuse to the baselines does not measurably improve retrieval. Per the note's own decision rule,
richness is a guitar statistic, not a similarity measure. The homograph work is unaffected: it
needs exact richness as a string budget, not as a similarity.

What the data do say is **the more a measure concentrates on the single dominant offset, the
better it finds variants**:

1 − C₁ (TI-Hamming) ≥ 1 − C₂ ≈ entropy > 1 − C₃ > trimmed vocabulary (75%) > 1 − C₆ ≈ vocabulary (90%) > richness.

Variants of a tune mostly keep one transposition and depart from it here and there, so a
measure that counts *every* departing offset (Hill order 0) is dominated by noise. That is the
ecologists' warning about order-0 diversity (rare species count as much as common ones), met in
melodies.

## Setup

- **Data.** MTC-ANN 2.0.1: 360 Dutch folk-song melodies in 26 expert-labelled tune families (8–27
  members). Chance MAP is 0.039. The scale check uses MTC-FS-INST 2.0: 18,109 melodies. The
  12,344 with a tune-family id are candidates and queries (1,000 sampled queries); the unlabelled
  ones are distractors.
- **Alignment (the same for every measure).** Each melody is sampled at N points spread evenly
  over its own duration (the pitch sounding at each point), so any two melodies pair point for
  point and long notes weigh more. N = 64 is the headline; 32 and 128 are the sensitivity check.
  The pairing is measure-neutral, but crude: it ignores pickups, inserted bars and ornaments. The
  absolute MAPs are therefore well below published alignment-based systems on this corpus. The
  question here is the *relative* ranking of measures on one shared pairing.
- **Scores.** Every melody queries all the others (relevant = same tune family).
  - MAP and mean AUC are tie-aware: exact expected values over random orderings of tied
    distances. Richness is integer-valued and ties constantly.
  - 95% intervals come from a paired bootstrap over queries.
  - The pair models are class-balanced logistic regressions, cross-validated so that a query's
    tune family is never in training (leave-one-family-out on MTC-ANN; 10 family groups on
    MTC-FS).

## MTC-ANN, whole melodies

MAP (95% CI) at N = 64, with MAP at N = 32 and N = 128 for sensitivity:

| measure | kind | MAP N=64 (95% CI) | AUC N=64 | MAP N=32 | MAP N=128 |
|---|---|---|---|---|---|
| Hamming, no transposition | floor | 0.411 (0.387–0.438) | 0.712 | 0.376 | 0.416 |
| **TI-Hamming, 1 − C₁** | baseline | **0.513 (0.488–0.539)** | **0.803** | **0.462** | **0.521** |
| switches S (interval Hamming) | baseline | 0.307 (0.285–0.329) | 0.674 | 0.327 | 0.252 |
| variation TV (interval L1) | baseline | 0.297 (0.274–0.320) | 0.667 | 0.337 | 0.255 |
| log₂ richness | candidate | 0.338 (0.316–0.361) | 0.741 | 0.337 | 0.338 |
| entropy H | candidate | 0.493 (0.466–0.521) | 0.773 | 0.452 | 0.497 |
| vocabulary covering 90% | candidate | 0.384 (0.359–0.409) | 0.742 | 0.360 | 0.384 |
| vocabulary covering 75% | candidate | 0.432 (0.408–0.459) | 0.749 | 0.402 | 0.436 |
| 1 − C₂ | candidate | 0.503 (0.476–0.529) | 0.789 | 0.452 | 0.507 |
| 1 − C₃ | candidate | 0.485 (0.458–0.511) | 0.776 | 0.440 | 0.491 |
| 1 − C₆ | candidate | 0.412 (0.386–0.437) | 0.750 | 0.369 | 0.418 |

- Every candidate is below TI-Hamming at every grid. The paired 95% intervals of the difference
  exclude zero in all cases; entropy at N = 32 is the closest call, at −0.009 (−0.018 to −0.000).
- Richness's AUC (0.74) is much closer to TI-Hamming's than its MAP is. It separates
  same-family from other pairs reasonably often, but it cannot rank the *top* of the list: too
  few distinct values, and any stray offset costs a whole class.
- S and TV degrade as the grid gets finer. Finer sampling adds more points where one melody has
  moved on and the other hasn't.

**Pair models** (logistic regression, cross-validated by family):

| grid | baselines (TI-Hamming, S, TV) | + richness, entropy, reuse | gain (95% CI) |
|---|---|---|---|
| 32 | 0.461 | 0.467 | +0.006 (+0.002 to +0.010) |
| 64 | 0.512 | 0.513 | +0.002 (−0.002 to +0.005) |
| 128 | 0.524 | 0.526 | +0.002 (−0.002 to +0.006) |

The gain is below 0.01 MAP everywhere, and indistinguishable from zero at 64 and 128. The fitted
weights shift between the collinear S, richness and reuse (u = S + 1 − r) from grid to grid,
which is what a model does when a feature carries no stable extra signal.

## MTC-FS-INST, scale check

There are 18,109 melodies, 1,000 random labelled queries among 12,344 labelled melodies in 5,102
families, and 5,765 unlabelled distractors. Chance MAP is 0.001; the grid is N = 64.

| measure | MAP (95% CI) | AUC | MAP − TI-Hamming (95% CI) |
|---|---|---|---|
| Hamming, no transposition | 0.351 (0.329–0.372) | 0.727 | −0.122 (−0.139 to −0.106) |
| **TI-Hamming, 1 − C₁** | **0.473 (0.450–0.495)** | **0.876** | — |
| switches S | 0.316 (0.294–0.338) | 0.789 | −0.157 |
| variation TV | 0.299 (0.278–0.322) | 0.772 | −0.174 |
| log₂ richness | 0.267 (0.246–0.288) | 0.833 | −0.206 (−0.221 to −0.190) |
| entropy H | 0.433 (0.409–0.458) | 0.865 | −0.040 (−0.048 to −0.033) |
| vocabulary covering 90% | 0.325 | 0.838 | −0.148 |
| vocabulary covering 75% | 0.377 | 0.843 | −0.095 |
| 1 − C₂ | 0.449 | 0.872 | −0.024 |
| 1 − C₃ | 0.420 | 0.865 | −0.053 |
| 1 − C₆ | 0.322 | 0.850 | −0.151 |

The pair models give 0.470 for the baselines and 0.473 with the candidates added: a gain of
**+0.003 (95% CI +0.000 to +0.006)**. The order of the measures is the same as on MTC-ANN.
Richness falls further behind at scale, because a large corpus is full of unrelated melodies
that happen to share a small offset vocabulary.

## Limits

- **One alignment.** A crude time-grid pairing is used for everything.
  - A good note-level alignment would raise every measure, and could favor richness more than
    the others, since stray offsets from misalignment hurt richness most.
  - The fair test of that is richness under its *own* optimal warping. That distance is a proven
    pseudometric ([`PROOF-alignment.md`](PROOF-alignment.md)), but it is a minimum-label path
    problem, costly to compute at this scale. Not run.
- **Whole melodies only.** Phrase-level retrieval (MTC-ANN has phrase annotations) is not run.
- **Folk song only.** Other repertoires could behave differently.
