# Coupled Transposition Structure in Aligned Melodies

## Working technical note, revision 1 (2026-09-26)

**What changed from the original draft.** A triangle-inequality check
(`docs/dev/triangle_check.py`) and a prior-art pass. The metric facts all
survived, but they are elementary, and most of the statistics already have
established names (§10). Three more of our statistics turned out to be metrics
too (§4.3, §5.2). The metric property is proved here for Hill orders 0 and 1;
explicit counterexamples rule out q = 1/2, 2 and infinity (§4.4), so there is no
general Hill/Renyi family of metrics. Optimizing the alignment can break the triangle
inequality (§7). "Rank" is renamed **richness** (§13). The one
possibly-new idea narrowed to **vocabulary vs. switches** (§6), with a concrete
test against existing baselines (§11).

---

## 0. Summary

For two melodies aligned note for note, the pointwise pitch differences
`delta_i = b_i - a_i` carry the whole relationship between them, up to transposition.
Two families of statistics fall out of that one sequence:

- **Family I, the values of delta** (how the notes are shared among transpositions):
  log richness, Shannon entropy, and one minus the modal share. All three are
  metrics once transposed melodies are treated as identical.
- **Family II, the changes in delta** (where the melodies' steps differ): the
  switch count and total variation. These are the Hamming and L1 distances
  between the two melodies' interval sequences, also metrics modulo transposition.

The metric property follows from one standard lemma (§3). It is proved here for
Hill/Renyi orders 0 and 1; explicit counterexamples show that it does not extend to
q = 1/2, 2 or infinity. Nearly every quantity here
has an established name in string matching, music retrieval, or ecology (§10).

The part we could not find named is the contrast between how *many* distinct
transposition offsets a pair needs and how *often* it switches between them (§6).
The guitar gives that contrast a physical meaning: every new offset value requires
at least one independently retuned string class, while returning to an offset already
in the vocabulary adds no new offset value. Fret range and simultaneity may still
require duplicate strings. Whether the distinction has musical value is an empirical
question (§11).

---

## 1. Setup

Two monophonic melodies of equal length, aligned position by position:

```text
A = (a_1, ..., a_n)        B = (b_1, ..., b_n)        integer pitches (e.g. MIDI)
delta_i = b_i - a_i        Delta(A,B) = (delta_1, ..., delta_n)
```

`Delta` is constant exactly when B is A transposed. Transposing either melody shifts
every `delta_i` by the same constant (with opposite sign depending on which melody
moves), so every statistic below that ignores constant shifts is automatically
transposition-invariant.

---

## 2. Where this came from: one string, one offset

A tab event is (string `s_i`, fret `f_i`). Under tunings `T_A` and `T_B`:

```text
a_i = T_A[s_i] + f_i
b_i = T_B[s_i] + f_i
=>  delta_i = T_B[s_i] - T_A[s_i]
```

The offset belongs to the *string*, not the note. So a tab that plays A under one
tuning and B under another must put notes with different offsets on different
strings:

```text
exact free-tuning homograph on an s-string instrument  requires  richness(A,B) <= s
```

It is necessary but not sufficient: fret span, simultaneous notes, reach and
physics also constrain (see `DESIGN-homograph.md`).

---

## 3. One lemma makes all of these distances

> **Lemma.** Let `f` map offset sequences to `[0, inf)` with
> (i) `f(-x) = f(x)`, (ii) `f(x + y) <= f(x) + f(y)`, and
> (iii) `f(x) = 0` exactly when `x` is constant.
> Then `d(A,B) = f(B - A)` is a pseudometric on melodies, and a metric on melodies
> modulo transposition.

*Proof.* Symmetry comes from (i). The triangle inequality comes from (ii), because
`C - A = (B - A) + (C - B)`. Zero distance means a constant offset, which is (iii). ∎

This is the standard "group norm" construction (a translation-invariant metric
from a subadditive length function). Taking the quotient by constant offsets is the
**T** of Callender, Quinn & Tymoczko's OPTIC equivalences (2008). Each statistic
below only needs its subadditivity (ii) checked.

---

## 4. Family I: the values of delta

Let `p_k` be the fraction of positions with offset `k`.

### 4.1 Richness (Hill order 0)

```text
r(A,B)  = number of distinct offsets            (called "rank" in the original draft)
d_0     = log2 r
```

Subadditive because the offsets of `x + y` are sums of an offset of `x` and an offset
of `y`, so there are at most `r(x) * r(y)` of them (the elementary sumset bound).
Taking logs gives (ii). *Reading:* how many transposition classes exist, or the bits
needed to name a note's class with a fixed-length label.

### 4.2 Shannon entropy (Hill order 1)

```text
d_1 = H(Delta) = -sum_k p_k log2 p_k        effective number of classes R_eff = 2^H
```

Subadditive because `H(X + Y) <= H(X, Y) <= H(X) + H(Y)`: a function of a pair
carries no more information than the pair. *Reading:* average bits per note to say
which class a note is in. This grows with both the number of classes and the
evenness of their use. It is not a pure "diffuseness" measure; evenness alone is
Pielou's `H / log r`, for which no metric claim is made.

### 4.3 One minus the modal share (transposition-invariant Hamming)

```text
C_1 = max_k p_k                  (share explained by the best single transposition)
d_H = 1 - C_1
```

Subadditive because at least `m_x + m_y - n` positions carry both modal values, so
`m_(x+y) >= m_x + m_y - n`. *Reading:* the fraction of notes that fail the best global
transposition. `n * d_H` is the **transposition-invariant Hamming distance**
(Mäkinen, Navarro & Ukkonen 2005), and it is computed from exactly this histogram.

### 4.4 The boundary: counterexamples at other orders

Richness, `R_eff` and `1/C_1` are Hill numbers of orders 0, 1 and ∞ (Hill 1973;
Jost 2006). Their logs are the Rényi entropies `H_q`. It is tempting to treat all
orders as a family of metrics. They are not. From `triangle_check.py`:

**Example 1 (16 notes).** `B - A` is 0 on the first 8 notes, then eight distinct
nonzero singleton values (9 distinct offsets total); `C - B` is the mirror image;
`C - A` has 16 distinct values.

| measure | d(A,B) | d(B,C) | d(A,B)+d(B,C) | d(A,C) | triangle |
|---|---|---|---|---|---|
| log2 richness (q=0) | 3.170 | 3.170 | 6.340 | 4.000 | holds |
| Rényi q=1/2 | 2.874 | 2.874 | 5.747 | 4.000 | holds |
| Shannon (q=1) | 2.500 | 2.500 | 5.000 | 4.000 | holds |
| Rényi-2 (log inverse Simpson) | 1.830 | 1.830 | 3.660 | 4.000 | **fails** |
| min-entropy (−log2 C1) | 1.000 | 1.000 | 2.000 | 4.000 | **fails** |
| 1 − C1 | 0.500 | 0.500 | 1.000 | 0.938 | holds |

**Example 2 (10 notes).** Offset splits 7:3 and 7:3 combine to 5:2:2:1.

| measure | d(A,B) | d(B,C) | d(A,B)+d(B,C) | d(A,C) | triangle |
|---|---|---|---|---|---|
| log2 richness (q=0) | 1.0000 | 1.0000 | 2.0000 | 2.0000 | holds (equality) |
| Rényi q=1/2 | 0.9385 | 0.9385 | 1.8770 | 1.8788 | **fails** |
| Shannon (q=1) | 0.8813 | 0.8813 | 1.7626 | 1.7610 | holds (by 0.002) |
| 1 − C1 | 0.300 | 0.300 | 0.600 | 0.500 | holds |

So the property holds at orders 0 and 1 and fails at 1/2, 2 and infinity on these
explicit constructions. A random search found violations at additional q values as
well. We therefore make no metric claim for the rest of the Renyi/Hill family without
an order-specific proof. In particular, **log inverse Simpson is not a metric here**,
and neither is -log C1, even though 1 - C1 is.

### 4.5 Top-k coverage: a prefilter, not a distance

```text
C_k = p_(1) + ... + p_(k)        (sorted shares; share explained by the best k offsets)
```

`C_6` is the natural cheap prefilter for guitar homographs: the share of notes that
six string-classes could account for. No metric claim is made for `k > 1`. `C_6 = 1`
is necessary but not sufficient for a 6-string homograph (§2).

---

## 5. Family II: the changes in delta

### 5.1 The identity

With interval sequences `I_A(i) = a_(i+1) - a_i` and `I_B(i) = b_(i+1) - b_i`:

```text
I_B(i) - I_A(i) = delta_(i+1) - delta_i
```

Wherever the offset stays constant, the two melodies take identical steps. They
diverge exactly where the offset changes. This identity connects the two classic
transposition-invariant approaches: **absolute pitch with a best transposition**
(Family I) and **interval encoding** (Family II).

### 5.2 Switch count and total variation

```text
S(A,B)  = #{ i : delta_(i+1) != delta_i }    = Hamming distance between I_A and I_B
TV(A,B) = sum_i |delta_(i+1) - delta_i|      = L1 distance between I_A and I_B
```

Both satisfy the lemma. For S, a position switches in `x + y` only if it switches in
`x` or in `y`. For TV, it is the triangle inequality of `|.|`. Both are zero exactly
for transpositions. Interval-sequence comparison is the standard transposition-invariant
representation in music retrieval (e.g. Lemström & Ukkonen 2000).

### 5.3 How the families connect

The offset sequence breaks into `S + 1` constant runs, and every class occupies at
least one run:

```text
r <= S + 1
reuse  u = (S + 1) - r >= 0        (how many runs return to an already-used class)
```

---

## 6. The possibly-new piece: vocabulary vs. switches

Existing local-transposition alignment (Allali, Ferraro, Hanna & Iliopoulos 2007)
lets a match change transposition partway through and **charges each change**. It
measures `S`, in spirit. The guitar exposes a different resource: introducing a new
offset value requires at least one string with that tuning difference, while returning
to an offset already in the vocabulary does not introduce another offset class. Thus
`r` is the **offset-vocabulary lower bound** on string demand; in the unconstrained
monophonic/infinite-fret model it is exact, while real fret range and simultaneity can
force multiple strings to carry the same class. Reuse `u` is free only with respect to
this offset-vocabulary resource.

| Delta | r | S | u | reading |
|---|---|---|---|---|
| 5 5 5 5 5 5 5 5 | 1 | 0 | 0 | a transposition |
| 5 5 5 5 7 7 7 7 | 2 | 1 | 0 | two classes, one handover |
| 5 7 5 7 5 7 5 7 | 2 | 7 | 6 | two classes, constantly alternating |
| 0 6 0 6 0 6 0 6 | 2 | 7 | 6 | same class pattern, but every other note moves a tritone |

Rows 3 and 4 are cheap in the offset-vocabulary model (two classes, hence a two-string
lower bound) and expensive for switch-penalized alignment. They are also a warning, because richness ignores the size of the offsets
(§8). The hypothesis worth testing is whether low richness with high reuse marks a
real musical relationship: a melody and a variant that keeps returning to the same
few transposition levels, such as sequences, echoes, or call-and-response at a fixed
interval. We found no name for this in a quick search, which is weak evidence of
novelty (§10).

---

## 7. Alignment

Everything above assumes the alignment `a_i <-> b_i` is given. Once the alignment is
*optimized* per pair, the triangle inequality is no longer automatic. Dynamic time
warping is the well-known example: it sums costs along the path and is not a metric.

A sketch, which needs a careful proof before it is cited:

- **Candidate result: log-richness may survive some unbounded monotone alignment
  models.** If the admissible alignment relation is closed under composition, an A->B
  alignment and a B->C alignment can induce an A->C alignment whose offsets are sums
  of offsets on the two component alignments. The sumset bound would then survive the
  minimization over alignments. This needs a precise alignment definition and proof
  before it is cited; do not assume it for arbitrary DP/DTW-style alignments.
- **Shannon, S and TV may not survive.** Composing alignments re-weights the paired
  notes (a note matched twice counts twice), which is exactly how DTW breaks.
- **A capped re-rhythm breaks the argument even for richness.** gtrsnipe's
  `--homograph-subdivide K` limits splits; two K=2 splits can compose into a K=4
  split, which the cap forbids.

Keep alignment out of the core mathematics. When it is added, say which of these
properties still hold.

---

## 8. What these measures ignore

- **Offset size.** `0 6 0 6` (tritones) and `0 1 0 1` (semitones) have the same
  richness, entropy, modal share and switch count. Only TV sees the size. Pair
  these with a size-aware measure before claiming anything perceptual.
- **Order, in Family I.** Richness, entropy and modal share cannot tell `5 5 7 7`
  from `5 7 5 7`. Family II can.
- **Rhythm.** Durations enter only through the alignment.
- **Perception.** Every claim here is structural, not perceptual. The note's claim is:

> The pointwise offset sequence represents the aligned relationship completely (up to
> transposition). Its value distribution and its changes give two families of
> transposition-invariant metrics. The guitar reads the value family's order-0 member
> physically as a lower bound on independently retuned string classes, and exactly as
> the minimum channel count in the unconstrained monophonic/infinite-fret model.

---

## 9. Decoder-relative sameness

The homograph is an exact, non-statistical example of decoder-relative meaning: one
fixed tab, `D(H, T_A) = A`, `D(H, T_B) = B`. The offset sequence says exactly what
the decoder has to supply.

- Given A, the tab's **string choices** must identify each note's class. In the
  source-coding sense that costs about `n * H(Delta)` bits in total (Shannon, §4.2),
  or `log2 r` bits per note with a fixed-length label (§4.1).
- The **tuning key** supplies the `r` offset values.

Different decoder capabilities induce different equivalences or resource-bounded
reachability relations. The distinction matters: `richness <= s` is a budget, not an
equivalence relation, because it need not be transitive.

| decoder/key model | parameters | relation | distance or resource test |
|---|---|---|---|
| identity | none | identical pitches | Hamming |
| global transposition | 1 offset | `B = A + c` | any Family I or II metric is 0 |
| s independent tuning offsets | at most s offset values | reachable within the abstract offset budget | `d_0 <= log2 s` (necessary guitar lower bound) |
| arbitrary substitution (one-to-one relabeling of pitches) | a codebook | `B = sigma(A)` | variation of information (Meila) |

Variation of information, `VI = H(A|B) + H(B|A)`, is zero exactly when each melody
is a relabeling of the other: a free substitution cipher. The tuning is a
*structured* key between transposition and substitution. What counts as "the same
melody" depends on which keys the decoder is allowed.

---

## 10. Prior art and names

| this note | established name | where |
|---|---|---|
| offset histogram | difference histogram used for transposition-invariant matching | Mäkinen, Navarro & Ukkonen 2005 |
| 1 − C1 | transposition-invariant Hamming distance (normalized) | same; also "P2" in Ukkonen, Lemström & Mäkinen 2003 |
| S | Hamming distance between interval sequences | interval encoding, e.g. Lemström & Ukkonen 2000 |
| TV | L1 distance between interval sequences | same family |
| richness, R_eff, 1/C1 | Hill numbers of order 0, 1, infinity (richness, exp-Shannon, reciprocal Berger-Parker) | Hill 1973; Jost 2006 |
| unaligned all-pairs version of the histogram | Lewin's interval function IFUNC | Lewin 1987 |
| transposition as quotient by constant offsets | the T in OPTIC | Callender, Quinn & Tymoczko 2008 |
| subadditivity of log-support and entropy of sums | sumset bounds; entropy sumset theory | additive combinatorics; Tao 2010 |
| switch-penalized local transposition | local transpositions in alignment | Allali, Ferraro, Hanna & Iliopoulos 2007 |
| substitution-cipher sameness | variation of information | Meilă 2003/2007 |

Also worth reading before any claim of novelty: δ- and γ-approximate matching
(Cambouropoulos, Crochemore, Iliopoulos et al.); translation-vector pattern discovery
(SIA/SIATEC, Meredith, Lemström & Wiggins 2002); voice-leading geometry (Tymoczko;
Straus); the melodic-similarity measure comparisons of Müllensiefen & Frieler and of
Janssen, van Kranenburg & Volk (2017).

---

## 11. The experiment that decides usefulness

Question: **does the offset profile separate same-tune variants from unrelated
melodies better than the established baselines?**

- **Data.** The Meertens Tune Collections. The annotated subset MTC-ANN (tune-family
  labels plus phrase annotations; verify its size) suits a first pass; MTC-FS-INST
  (~18k melodies) suits scale.
- **Baselines.** 1 − C1 (TI-Hamming), S (interval Hamming), and a standard
  alignment-based measure. Janssen, van Kranenburg & Volk (2017) is the benchmark
  to compare against on this corpus.
- **Candidates.** Richness, entropy, reuse `u`, and the profile as a feature vector.
- **Alignment.** Use the same alignment for every measure (for example phrase-level
  equal-length units, or one shared DP), so measures differ only in how they score
  the coupling.
- **Scores.** Mean average precision for tune-family retrieval; AUC for classifying
  same-family vs. different-family pairs; the gain from adding richness and reuse to
  the baselines, with bootstrap confidence intervals.
- **Decision.**
  - No gain over the baselines: richness is a guitar statistic, not a similarity
    measure. Stop there; the homograph work is unaffected.
  - A gain: a small, honest contribution with a physical reading.

The homograph search in the wild (do playable low-richness pairs occur between
*unrelated* songs?) is a separate question with its own interest either way.

---

## 12. Homograph corollaries (from the original §16–17, condensed)

- **Prefilter.** `C_6 < 1` means no exact 6-string homograph at this alignment.
  `C_6 = 1` sends the pair on to the full fretboard/physics solver.
- **Construction residue.** In a constructed homograph, A's fingering is constrained
  by B's hidden offsets: the same audible note may sit on different strings for no
  playing reason (Old MacDonald's three opening C4s land on D10, D10, G5). A detector
  scoring fingering improbability given the audible melody alone could flag
  constructed homographs; a generator could then optimize against it. Natural
  homographs need not carry this residue.

---

## 13. Terminology (revised)

```text
pointwise offset sequence       Delta(A,B) = B - A
offset richness                 r = number of distinct offsets    (was "rank"; avoids clashes
                                                                   with matrix rank and
                                                                   rank-based metric terminology)
log-richness distance           d_0 = log2 r
offset entropy                  d_1 = H(Delta);   effective number R_eff = 2^H
modal share / TI-Hamming        C_1;   d_H = 1 - C_1
top-k coverage                  C_k   (prefilter; no metric claim for k > 1)
switch count                    S = interval Hamming distance
total variation                 TV = interval L1 distance
reuse                           u = S + 1 - r
```

gtrsnipe's `--homograph` report now prints "Richness"; keep that label synchronized
with this note.

---

## References

Verified 2026-09-26:

- V. Mäkinen, G. Navarro, E. Ukkonen. *Transposition invariant string matching.*
  Journal of Algorithms 56(2):124–153, 2005 (STACS 2003).
  <https://www.sciencedirect.com/science/article/abs/pii/S0196677404001427>
- J. Allali, P. Ferraro, P. Hanna, C. Iliopoulos. *Local transpositions in alignment
  of polyphonic musical sequences.* SPIRE 2007, LNCS 4726.
  <https://link.springer.com/chapter/10.1007/978-3-540-75530-2_3>
- B. Janssen, P. van Kranenburg, A. Volk. *Finding occurrences of melodic segments in
  folk songs employing symbolic similarity measures.* Journal of New Music Research
  46(2):118–134, 2017.
  <https://www.tandfonline.com/doi/full/10.1080/09298215.2017.1316292>

From memory (check venue and details before citing):

- M. O. Hill. *Diversity and evenness: a unifying notation and its consequences.*
  Ecology, 1973.
- L. Jost. *Entropy and diversity.* Oikos, 2006.
- C. Callender, I. Quinn, D. Tymoczko. *Generalized voice-leading spaces.* Science, 2008.
- T. Tao. *Sumset and inverse sumset theory for Shannon entropy.* Combinatorics,
  Probability and Computing, 2010.
- M. Meilă. *Comparing clusterings: an information based distance.* J. Multivariate
  Analysis, 2007 (COLT 2003).
- D. Lewin. *Generalized Musical Intervals and Transformations.* 1987.
- K. Lemström, E. Ukkonen. *Including interval encoding into edit distance based
  music comparison and retrieval.* AISB 2000.
- E. Ukkonen, K. Lemström, V. Mäkinen. *Geometric algorithms for transposition
  invariant content-based music retrieval.* ISMIR 2003.
- D. Meredith, K. Lemström, G. Wiggins. *Algorithms for discovering repeated
  patterns in multidimensional representations of polyphonic music.* JNMR, 2002.
