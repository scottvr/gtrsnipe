# R03b: phrases and motifs (the R03 follow-ups)

Run on 2026-09-30 with `gtrsnipe-research segments` (gtrsnipe 0.6.14), on the expert
annotations of MTC-ANN 2.0.1. Reproduce with:

```bash
R="gtrsnipe-research --data DIR"
$R segments mtc-ann --level phrase --scope family --json phrase-family.json
$R segments mtc-ann --level motif  --scope family --json motif-family.json
$R segments mtc-ann --level phrase --scope song   --json phrase-song.json
```

## The questions

[R03](RESULTS-R03-families.md) compared whole melodies on one time grid and found the offset
measures no better than transposition-invariant Hamming distance at finding tune-family
members. It left four things untested, and scottvr asked for them before anything is published:

1. **Phrase-level retrieval** (R03 used whole melodies).
2. **Alignment-based baselines** (R03 compared on a fixed grid only).
3. **The offset measures under their own optimal warping** (R12): the pseudometrics of
   [PROOF-alignment](../theory/PROOF-alignment.md), minimized over warping paths.
4. **The structure note's §6 hypothesis**: does low richness with high reuse (few offsets,
   revisited) mark related passages such as sequences or echoes?

## Bottom line

- **The best single measures still look at the dominant transposition.** For phrases:
  TI-Hamming on the grid (MAP 0.78–0.79 across the three annotators), and DTW on pitch after
  that transposition (0.78–0.81). For motifs, pitch DTW leads (0.88; TI-Hamming 0.85).
  DTW on intervals trails both (0.70–0.73 for phrases).
- **Warping helps the offset measures a lot.** Switches and total variation rise from about
  0.60 on the grid to 0.71–0.75; richness from 0.70 to 0.71–0.75. That brings them close to
  the best single measures, but not above them.
- **A small positive result, at the phrase level only.** Added to all five baselines (grid
  TI-Hamming, switches and TV, interval DTW, pitch DTW), the warped switches, TV and richness
  raise MAP by **+0.009 to +0.010 for every annotator** (95% intervals +0.005 to +0.013).
  Against weaker baselines without pitch DTW the gain was +0.014 to +0.019, so about half of it
  was warping itself; the rest comes from the offset statistics. For motifs, and for phrases
  within a song (near the ceiling), there's no measurable gain.
- **The §6 hypothesis isn't supported by these tests.** Low richness marks related segments
  with or without a revisit: among related phrase pairs across the family, 15–18% have low
  richness and no revisit, and 9–12% have both, both far above the ~0.2% of unrelated pairs.
  Adding grid richness, entropy and reuse to the baselines changes MAP by −0.005 to +0.000.
  MTC-ANN annotates phrase and motif identity, not sequences or echoes, so the direct test of
  the hypothesis still needs annotations of those.

## Setup

- **Data.** MTC-ANN 2.0.1: 360 melodies in 26 tune families.
  - 1,890 phrases, each labelled by three annotators; their letters are their own, so each
    annotator is scored separately.
  - 1,657 motif occurrences, each with a motif class.
  - Every annotation lines up with gtrsnipe's kern reader: all 360 songs have the annotated
    number of phrases, and every motif's note indices and start time match.
- **The task.** Each labelled segment is a query. Its candidates are the segments of the other
  songs of its tune family, or, in the within-song setting, the other phrases of its own song.
  Relevant candidates carry the same label. This is a phrase-to-phrase variant of the task
  in Janssen, van Kranenburg & Volk (2017), not a replication of their benchmark or numbers.
- **Measures.**
  - The R03 measures on a time-normalized grid (16 points per phrase, 8 per motif).
  - DTW on the interval sequences, and DTW on pitch after the grid's modal transposition.
  - The offset measures minimized over warping paths: switches, total variation, largest jump,
    range, and richness, exact up to 6 distinct offsets (the guitar range).
  - A brute-force enumeration of every warping path confirms all five on 400 random pairs.
- **Scores.** Mean average precision (tie-aware) and AUC per query, with bootstrap intervals.
  Pair models: class-balanced logistic regression on the five baselines, then with each set of
  candidates added, cross-validated by leaving each tune family out.

## Results

### Phrases: candidates from the other songs of the tune family

MAP, and in brackets the difference from TI-Hamming:

| measure | annotator 1 | annotator 2 | annotator 3 |
|---|---|---|---|
| TI-Hamming (1 − C₁), grid | 0.788 (+0.000) | 0.781 (+0.000) | 0.789 (+0.000) |
| entropy, grid | 0.779 (-0.009) | 0.768 (-0.013) | 0.776 (-0.013) |
| log richness, grid | 0.702 (-0.086) | 0.693 (-0.088) | 0.699 (-0.091) |
| switches S, grid | 0.605 (-0.183) | 0.601 (-0.180) | 0.601 (-0.188) |
| total variation TV, grid | 0.617 (-0.171) | 0.619 (-0.162) | 0.616 (-0.173) |
| DTW on intervals | 0.697 (-0.091) | 0.716 (-0.065) | 0.729 (-0.060) |
| DTW on pitch, transposed | 0.776 (-0.012) | 0.793 (+0.012) | 0.805 (+0.015) |
| richness, warped | 0.714 (-0.074) | 0.732 (-0.049) | 0.751 (-0.038) |
| switches, warped | 0.714 (-0.074) | 0.738 (-0.043) | 0.745 (-0.044) |
| TV, warped | 0.712 (-0.076) | 0.739 (-0.042) | 0.745 (-0.044) |
| range R, warped | 0.680 (-0.108) | 0.696 (-0.085) | 0.713 (-0.076) |
| largest jump J, warped | 0.532 (-0.256) | 0.551 (-0.230) | 0.570 (-0.219) |
| reuse u, grid | 0.273 (-0.515) | 0.280 (-0.501) | 0.258 (-0.531) |
| *chance* | 0.146 | 0.150 | 0.126 |
| *queries* | 1682 | 1717 | 1637 |

Pair models (all five baselines, then with the candidates added), MAP gain and 95% CI:

| | annotator 1 | annotator 2 | annotator 3 |
|---|---|---|---|
| baselines alone | 0.822 | 0.830 | 0.838 |
| + richness, entropy, reuse (grid) | -0.005 (-0.007 to -0.002) | -0.003 (-0.005 to -0.001) | -0.000 (-0.002 to +0.001) |
| + switches, TV, richness (warped) | +0.009 (+0.006 to +0.012) | +0.009 (+0.005 to +0.012) | +0.010 (+0.006 to +0.013) |

Low-richness pairs (grid richness ≤ 2), with and without a revisit (reuse ≥ 1), as a share of related / unrelated pairs:

| | annotator 1 | annotator 2 | annotator 3 |
|---|---|---|---|
| r ≤ 2, u ≥ 1 | 9.5% / 0.23% | 9.2% / 0.21% | 11.5% / 0.16% |
| r ≤ 2, u = 0 | 15.5% / 0.21% | 15.0% / 0.22% | 17.8% / 0.24% |

### Motifs: candidates from the other songs of the tune family

MAP, and in brackets the difference from TI-Hamming:

| measure | motif class |
|---|---|
| TI-Hamming (1 − C₁), grid | 0.848 (+0.000) |
| entropy, grid | 0.853 (+0.004) |
| log richness, grid | 0.801 (-0.047) |
| switches S, grid | 0.707 (-0.141) |
| total variation TV, grid | 0.751 (-0.097) |
| DTW on intervals | 0.831 (-0.017) |
| DTW on pitch, transposed | 0.880 (+0.031) |
| richness, warped | 0.844 (-0.004) |
| switches, warped | 0.830 (-0.018) |
| TV, warped | 0.851 (+0.003) |
| range R, warped | 0.857 (+0.008) |
| largest jump J, warped | 0.806 (-0.043) |
| reuse u, grid | 0.278 (-0.570) |
| *chance* | 0.260 |
| *queries* | 1607 |

Pair models (all five baselines, then with the candidates added), MAP gain and 95% CI:

| | motif class |
|---|---|
| baselines alone | 0.900 |
| + richness, entropy, reuse (grid) | +0.000 (-0.001 to +0.001) |
| + switches, TV, richness (warped) | -0.000 (-0.002 to +0.002) |

Low-richness pairs (grid richness ≤ 2), with and without a revisit (reuse ≥ 1), as a share of related / unrelated pairs:

| | motif class |
|---|---|
| r ≤ 2, u ≥ 1 | 24.1% / 3.27% |
| r ≤ 2, u = 0 | 40.4% / 7.56% |

### Phrases: candidates from the same song

MAP, and in brackets the difference from TI-Hamming:

| measure | annotator 1 | annotator 2 | annotator 3 |
|---|---|---|---|
| TI-Hamming (1 − C₁), grid | 0.975 (+0.000) | 0.955 (+0.000) | 0.978 (+0.000) |
| entropy, grid | 0.974 (-0.001) | 0.955 (+0.000) | 0.972 (-0.006) |
| log richness, grid | 0.957 (-0.018) | 0.943 (-0.012) | 0.961 (-0.017) |
| switches S, grid | 0.918 (-0.057) | 0.903 (-0.052) | 0.924 (-0.055) |
| total variation TV, grid | 0.922 (-0.053) | 0.909 (-0.047) | 0.934 (-0.045) |
| DTW on intervals | 0.954 (-0.021) | 0.944 (-0.011) | 0.970 (-0.009) |
| DTW on pitch, transposed | 0.970 (-0.005) | 0.953 (-0.002) | 0.984 (+0.005) |
| richness, warped | 0.961 (-0.014) | 0.947 (-0.008) | 0.968 (-0.010) |
| switches, warped | 0.962 (-0.013) | 0.947 (-0.008) | 0.967 (-0.011) |
| TV, warped | 0.955 (-0.020) | 0.935 (-0.020) | 0.965 (-0.014) |
| range R, warped | 0.924 (-0.051) | 0.904 (-0.051) | 0.939 (-0.039) |
| largest jump J, warped | 0.888 (-0.087) | 0.868 (-0.087) | 0.905 (-0.073) |
| reuse u, grid | 0.704 (-0.271) | 0.697 (-0.258) | 0.705 (-0.273) |
| *chance* | 0.191 | 0.195 | 0.189 |
| *queries* | 723 | 760 | 712 |

Pair models (all five baselines, then with the candidates added), MAP gain and 95% CI:

| | annotator 1 | annotator 2 | annotator 3 |
|---|---|---|---|
| baselines alone | 0.984 | 0.971 | 0.989 |
| + richness, entropy, reuse (grid) | +0.001 (-0.000 to +0.003) | -0.002 (-0.007 to +0.002) | +0.000 (-0.002 to +0.002) |
| + switches, TV, richness (warped) | +0.002 (-0.003 to +0.007) | -0.003 (-0.009 to +0.003) | -0.001 (-0.004 to +0.002) |

Low-richness pairs (grid richness ≤ 2), with and without a revisit (reuse ≥ 1), as a share of related / unrelated pairs:

| | annotator 1 | annotator 2 | annotator 3 |
|---|---|---|---|
| r ≤ 2, u ≥ 1 | 6.8% / 0.03% | 6.3% / 0.05% | 6.8% / 0.05% |
| r ≤ 2, u = 0 | 66.7% / 0.05% | 64.4% / 0.20% | 68.1% / 0.10% |

## Caveats

- **Small effect.** The phrase-level gain is about 1% of MAP. It is consistent across
  annotators and its intervals exclude zero, but it is one corpus, one task, and one model.
- **Collinear features.** Warped switches, TV and richness are correlated, so which of them
  carries the gain is not separated here.
- **The pitch-DTW baseline uses the grid's modal transposition,** not the best transposition per
  path; a fully optimized transposition could be stronger still.
- **Within-family candidates.** Candidates come from the query's tune family only, as in
  occurrence finding, so the task is "which phrase", not "which tune"; R03 covered the latter.
- **Not the Janssen et al. benchmark.** Their task finds occurrences inside whole melodies and
  compares other measures (among them SIAM and local alignment). Nothing here is comparable to
  their numbers.
- **The §6 hypothesis** was tested only indirectly, through phrase and motif identity.
