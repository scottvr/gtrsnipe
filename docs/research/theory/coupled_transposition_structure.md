# Coupled Transposition Structure in Aligned Melodies

## Working technical note, revision 3 (2026-09-29)

**What this note is.** A dictionary and a synthesis, written for the guitar-tab homograph
(one tab, a different melody in each tuning; [`../../app/DESIGN-homograph.md`](../../app/DESIGN-homograph.md)).
It collects what is known about the pointwise pitch differences between two aligned
melodies: which statistics of them are distances, what they are called in other fields, and
what the homograph needs from them.

**What it is not.** It claims no new result. Every fact below is either elementary or already
named elsewhere, as far as the literature survey
([`../literature/LITERATURE-offsets.md`](../literature/LITERATURE-offsets.md)) and later reading
could tell. The one statement that may not be written down anywhere in general form, the
condition for surviving optimized alignment (§7), is almost certainly folklore to anyone who
knows the Fréchet distance. How the note got here is in §14.

---

## 0. Summary

- **One sequence carries everything.** For two melodies aligned note for note, the offsets
  `delta_i = b_i - a_i` describe the whole relationship up to transposition (§1).
- **Two families of statistics, all with established names** (§4, §5, §10):
  - the *values* of delta: log richness (the number of distinct offsets), Shannon entropy,
    one minus the modal share;
  - the *changes* in delta: the switch count and total variation, which are the Hamming and
    L1 distances between the melodies' interval sequences.
  All five are pseudometrics, and metrics once transposed melodies count as equal, by one
  elementary lemma (§3). No other Rényi/Hill order gives a metric (§4.4).
- **Vocabulary vs. switches is a known distinction** (§6). How many distinct offsets a pair
  needs, as against how often it changes offset, is the split between *label costs* (paid
  once per label used) and *Potts* smoothness costs (paid at every change) in computer-vision
  energy minimization. The guitar gives it a physical reading: richness is a lower bound on
  the number of strings a shared tab needs.
- **Under optimized (warping) alignment** (§7), a statistic that ignores consecutive repeats
  and is subadditive stays a pseudometric: log richness, the switch count, total variation,
  the largest jump and the range survive. Entropy and one minus the modal share, which count
  how *long* each offset lasts, do not. The proof is the Fréchet distance's.
- **As a melodic similarity, richness is not useful** (§11). On tune-family retrieval,
  transposition-invariant Hamming distance beats it. Its role is the string budget.

---

## 1. Setup

Two monophonic melodies of equal length, aligned position by position:

```text
A = (a_1, ..., a_n)        B = (b_1, ..., b_n)        integer pitches (e.g. MIDI)
delta_i = b_i - a_i        Delta(A,B) = (delta_1, ..., delta_n)
```

`Delta` is constant exactly when B is A transposed. Transposing either melody shifts
every `delta_i` by the same constant, so every statistic below that ignores constant shifts
is transposition-invariant.

---

## 2. One string, one offset

A tab event is (string `s_i`, fret `f_i`). Under tunings `T_A` and `T_B`:

```text
a_i = T_A[s_i] + f_i
b_i = T_B[s_i] + f_i
=>  delta_i = T_B[s_i] - T_A[s_i]
```

The offset belongs to the *string*, not the note. So a tab that plays A under one tuning and
B under another must put notes with different offsets on different strings:

```text
exact free-tuning homograph on an s-string instrument  requires  richness(A,B) <= s
```

It is necessary but not sufficient: fret span, simultaneous notes and string physics also
constrain. The exact criterion (a partition of the aligned notes into at most s classes of
constant offset, with no two simultaneous notes in a class and each class within the fret
range) is DESIGN-homograph §1. In the language of §10, finding a homograph is
**multi-model fitting with a label budget**: each note pair is a correspondence, each string's
retune is a model (a constant offset), and at most s models are allowed.

---

## 3. One lemma makes all of these distances

> **Lemma.** Let `f` map offset sequences to `[0, inf)` with
> (i) `f(-x) = f(x)`, (ii) `f(x + y) <= f(x) + f(y)`, and
> (iii) `f(x) = 0` exactly when `x` is constant.
> Then `d(A,B) = f(B - A)` is a pseudometric on melodies, and a metric on melodies
> modulo transposition.

*Proof.* Symmetry comes from (i). The triangle inequality comes from (ii), because
`C - A = (B - A) + (C - B)`. Zero distance means a constant offset, which is (iii). ∎

This is the standard construction of a translation-invariant metric from a subadditive
length function. Taking the quotient by constant offsets is the **T** of Callender, Quinn &
Tymoczko's OPTIC equivalences (2008). Each statistic below only needs (ii) checked.

---

## 4. Family I: the values of delta

Let `p_k` be the fraction of positions with offset `k`.

### 4.1 Richness (Hill order 0)

```text
r(A,B)  = number of distinct offsets
d_0     = log2 r
```

Subadditive because the offsets of `x + y` are sums of an offset of `x` and an offset of
`y`, so there are at most `r(x) * r(y)` of them (the elementary sumset bound). Taking logs
gives (ii). *Readings:* the number of transposition classes; the bits needed to name a note's
class with a fixed-length label; on a guitar, a lower bound on the strings a shared tab needs
(§2). It is exact only in an idealized model (one note at a time, unlimited frets), and
"richness ≤ s" is a budget, not an equivalence relation: it isn't transitive.

### 4.2 Shannon entropy (Hill order 1)

```text
d_1 = H(Delta) = -sum_k p_k log2 p_k        effective number of classes R_eff = 2^H
```

Subadditive because `H(X + Y) <= H(X, Y) <= H(X) + H(Y)`: a function of a pair carries no
more information than the pair. This is the elementary argument, not the entropy sumset
theory of Ruzsa and Tao, which concerns *independent* summands; here the offsets are coupled
by the alignment. *Reading:* the average bits per note to say which class a note is in.

### 4.3 One minus the modal share (transposition-invariant Hamming)

```text
C_1 = max_k p_k                  (share explained by the best single transposition)
d_H = 1 - C_1
```

Subadditive because at least `m_x + m_y - n` positions carry both modal values, so
`m_(x+y) >= m_x + m_y - n`. `n * d_H` is the **transposition-invariant Hamming distance**
of Mäkinen, Navarro & Ukkonen (2005), computed from exactly this histogram.

### 4.4 No other order

Richness, `R_eff` and `1/C_1` are Hill numbers of orders 0, 1 and ∞ (Hill 1973; Jost 2006),
and their logs are Rényi entropies. **Only orders 0 and 1 give metrics.** Rényi entropy is
subadditive only at those orders (the classical characterization: Aczél, Forte & Ng 1974), and
choosing offsets whose pairwise sums are all distinct turns any non-subadditive joint
distribution into a triangle violation (LITERATURE §5). Two explicit examples, from
[`triangle_check.py`](triangle_check.py):

**Example 1 (16 notes).** `B - A` is 0 on the first 8 notes, then eight distinct nonzero
singleton values (9 distinct offsets in all); `C - B` is the mirror image; `C - A` has 16
distinct values.

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

At order ∞ the metric is `1 − C_1`, not `−log C_1`: min-entropy is not subadditive.

### 4.5 Top-k coverage: a prefilter, not a distance

```text
C_k = p_(1) + ... + p_(k)        (sorted shares; share explained by the best k offsets)
```

`C_6 = 1` is necessary for a 6-string homograph at this alignment, and `C_6 < 1` rules one
out. No metric claim is made for `k > 1`.

---

## 5. Family II: the changes in delta

### 5.1 The identity

With interval sequences `I_A(i) = a_(i+1) - a_i` and `I_B(i) = b_(i+1) - b_i`:

```text
I_B(i) - I_A(i) = delta_(i+1) - delta_i
```

Wherever the offset stays constant, the two melodies take identical steps; they diverge
exactly where the offset changes. This connects the two classic transposition-invariant
approaches: absolute pitch with a best transposition (Family I) and interval encoding
(Family II).

### 5.2 Switch count and total variation

```text
S(A,B)  = #{ i : delta_(i+1) != delta_i }    = Hamming distance between I_A and I_B
TV(A,B) = sum_i |delta_(i+1) - delta_i|      = L1 distance between I_A and I_B
```

Both satisfy the lemma: a position switches in `x + y` only if it switches in `x` or in `y`,
and TV inherits the triangle inequality of `|.|`. Both are zero exactly for transpositions.
S is interval-encoding Hamming distance (e.g. Lemström & Ukkonen 2000); TV is SIMILE's `diff`
(Müllensiefen & Frieler 2004). As signal regularizers (§10), S is the "L0 norm" of the
gradient and TV is classic total variation.

### 5.3 How the families connect

The offset sequence breaks into `S + 1` constant runs, and every class occupies at least one
run:

```text
r <= S + 1
reuse  u = (S + 1) - r >= 0        (how many runs return to an already-used class)
```

---

## 6. Vocabulary vs. switches

Two different costs can be charged for a sequence of offsets:
- **per switch** (`S`): every change of offset costs, including a return to an offset used
  before;
- **per vocabulary item** (`r`): each distinct offset costs once, and returning to it is free.

| Delta | r | S | u | reading |
|---|---|---|---|---|
| 5 5 5 5 5 5 5 5 | 1 | 0 | 0 | a transposition |
| 5 5 5 5 7 7 7 7 | 2 | 1 | 0 | two classes, one handover |
| 5 7 5 7 5 7 5 7 | 2 | 7 | 6 | two classes, constantly alternating |
| 0 6 0 6 0 6 0 6 | 2 | 7 | 6 | same class pattern, but every other note moves a tritone |

**Where each appears.**
- *In music retrieval,* switches are charged: local-transposition alignment (Allali, Ferraro,
  Hanna & Iliopoulos 2007) and Lemström & Mäkinen's minimum number of pieces (2005). For
  Lemström & Mäkinen a return to an earlier transposition is explicitly charged again; for
  Allali et al. this is inferred from their description, not confirmed. No measure that counts
  the offset vocabulary was found (LITERATURE §1).
- *In computer vision,* both costs are standard. Segmentation and multi-model fitting minimize
  an energy with a **Potts** term (a cost at every label change: S) and a **label cost** (a
  cost for each label used at all: r), e.g. Delong, Osokin, Isack & Boykov (2012) and the PEARL
  multi-model fitting of Isack & Boykov (2012), which assigns point correspondences to a few
  geometric models, classically homographies. Layered motion (Wang & Adelson 1994) is the same
  idea for optical flow. *(Citations from memory; see References.)*
- *On a guitar,* the vocabulary cost is physical: each distinct offset needs a string retuned
  by that interval, and going back to it costs nothing. So `r` is the string-budget lower bound
  of §2, and `u` is free.

**What was tested.** Whether a small vocabulary marks melodic variants: it doesn't (§11).
**What wasn't:** whether low richness with high reuse marks sequences, echoes or
call-and-response at a fixed interval. That remains an open, low-priority question. Rows 3
and 4 of the table are also a warning: richness ignores how big the offsets are (§8).

---

## 7. Optimized alignment

Everything above assumes the alignment `a_i <-> b_i` is given. When it is optimized per pair
over **warping paths** (monotone alignments in which a note may be matched to several notes of
the other melody), the triangle inequality is no longer automatic: dynamic time warping, which
sums a cost along the path, is the standard example of a distance that fails it.

**The result** ([`PROOF-alignment.md`](PROOF-alignment.md), with a brute-force check in
[`alignment_check.py`](alignment_check.py)). Minimized over warping paths, a statistic of the
offset sequence stays a pseudometric if it is
- *stutter-invariant*: it ignores consecutive repeats (a note held against several notes
  repeats an offset);
- *subadditive*, even, and zero exactly on constant sequences (the lemma's conditions).

The zero set becomes "the same melody up to transposition and to splitting or merging repeated
notes".

| survives | fails |
|---|---|
| log richness, switch count S, total variation TV, the largest jump J, the range R | Shannon entropy, 1 − C1 |

The survivors depend only on *which* offsets occur and *how* they change; the failures count
how *long* each offset lasts, which a warping path can inflate. The smallest counterexample has
melodies of 1, 2 and 2 notes.

**What is known.** The proof composes the two optimal paths through the middle melody. That is
the classical proof that the discrete Fréchet distance (the largest pointwise gap, minimized
over couplings) is a metric, and Fréchet's distance is the prototype of the class: with
transposition factored out, the range R is twice a transposition-invariant discrete Fréchet
distance. Whether the general condition (any stutter-invariant subadditive functional of the
coupled differences) is stated anywhere is not known here; it is the kind of generalization an
expert would call immediate. The measures `d_S` (fewest offset changes with free stretching)
and `d_richness` (fewest distinct offsets with free stretching) were not found under other
names. The capped re-rhythm of `--homograph-subdivide K` is not covered: capped paths are not
closed under composition.

---

## 8. What these measures ignore

- **Offset size.** `0 6 0 6` (tritones) and `0 1 0 1` (semitones) have the same richness,
  entropy, modal share and switch count. TV, and under optimized alignment J and R, see the
  size.
- **Order, in Family I.** Richness, entropy and modal share cannot tell `5 5 7 7` from
  `5 7 5 7`. Family II can.
- **Rhythm.** Durations enter only through the alignment.
- **Perception.** Everything here is structural. Nothing says two melodies *sound* alike or
  unlike.

---

## 9. Decoder-relative sameness

The homograph is an exact, non-statistical example of decoder-relative meaning: one fixed tab,
`D(H, T_A) = A`, `D(H, T_B) = B`. The offset sequence says exactly what the decoder has to
supply.

- Given A, the tab's **string choices** must identify each note's class: about `n * H(Delta)`
  bits in total (§4.2), or `log2 r` bits per note with a fixed-length label (§4.1).
- The **tuning key** supplies the `r` offset values.

| decoder/key model | parameters | relation | distance or resource test |
|---|---|---|---|
| identity | none | identical pitches | Hamming |
| global transposition | 1 offset | `B = A + c` | any Family I or II metric is 0 |
| s independent tuning offsets | at most s offset values | reachable within the offset budget | `r <= s` (a necessary guitar condition; not an equivalence) |
| arbitrary substitution (one-to-one relabeling of pitches) | a codebook | `B = sigma(A)` | variation of information (Meilă) |

Variation of information, `VI = H(A|B) + H(B|A)`, is zero exactly when each melody is a
relabeling of the other: a free substitution cipher. The tuning is a *structured* key between
transposition and substitution. What counts as "the same melody" depends on which keys the
decoder is allowed. A visual analogue is the *hybrid image* (Oliva, Torralba & Schyns 2006):
one picture that reads as two, depending on viewing distance.

---

## 10. Names across fields

| this note | established name | where |
|---|---|---|
| offset histogram | difference histogram for transposition-invariant matching | Mäkinen, Navarro & Ukkonen 2005 |
| 1 − C1 | transposition-invariant Hamming distance (normalized) | same; the unaligned analogue is "P2" (the mode over all note pairs) in Ukkonen, Lemström & Mäkinen 2003 |
| C1 | "consistency": the number of voices moving the same distance | Straus 2003, 2005 |
| S | Hamming distance between interval sequences | Lemström & Ukkonen 2000 |
| TV | L1 distance between interval sequences | SIMILE's `diff` (Müllensiefen & Frieler 2004) |
| richness, R_eff, 1/C1 | Hill numbers of order 0, 1, infinity | Hill 1973; Jost 2006; Berger & Parker 1970 |
| unaligned all-pairs histogram | Lewin's interval function IFUNC | Lewin 1959, 1987 |
| transposition as a quotient by constant offsets | the T in OPTIC | Callender, Quinn & Tymoczko 2008 |
| subadditivity of log-support and of entropy of sums | elementary (δ_AC is a function of the coupled pair) | not Ruzsa's or Tao's sumset theory (independent summands) |
| per-string retuning vector (a homograph's tuning key) | the "retuning cipher" | Allen & Goudeseune 2011 |
| switch-penalized local transposition | local transpositions in alignment | Allali, Ferraro, Hanna & Iliopoulos 2007 |
| substitution-cipher sameness | variation of information | Meilă 2003/2007 |
| S, as a regularizer | L0 gradient "norm" | Xu, Lu, Xu & Jia 2011 * |
| TV, as a regularizer | total variation | Rudin, Osher & Fatemi 1992 * |
| richness, as a regularizer | label cost (the number of labels used); palette size | Delong, Osokin, Isack & Boykov 2012 * |
| S, in labeling | Potts smoothness term | the same * |
| finding a homograph | multi-model fitting with a label budget | Isack & Boykov 2012 (PEARL) * |
| a piecewise-constant offset field | layered motion | Wang & Adelson 1994 * |
| range R and largest jump J under warping | discrete Fréchet distance (R is twice a transposition-invariant one) | Eiter & Mannila 1994 * |
| why entropy fails under warping | the reason DTW is not a metric (costs weighted by path multiplicity) | standard * |

\* From memory, not yet verified (see References).

---

## 11. Usefulness as a melodic similarity: no

The test this note specified in revision 1, with its decision rule written in advance: on the
Meertens Tune Collections, does the offset profile separate variants of a tune from unrelated
melodies better than established baselines? Run as R03
([`RESULTS-R03-families.md`](../results/RESULTS-R03-families.md)):

- On MTC-ANN (360 melodies in 26 tune families) and MTC-FS-INST (1,000 queries among 18,109
  melodies), with one shared grid alignment, transposition-invariant Hamming distance
  (1 − C1) is best. Richness trails it by 0.13–0.21 mean average precision.
- Adding richness, entropy and reuse to the baselines gains at most 0.006 MAP.
- The more a measure concentrates on the single dominant offset, the better it finds variants:
  variants keep one transposition and depart from it here and there, so counting every
  departing offset (order 0) is dominated by noise.

**Decision:** richness is a guitar statistic, not a similarity measure. Not tried: an
alignment-based baseline, the Janssen, van Kranenburg & Volk (2017) benchmark, and phrase-level
retrieval. Nothing suggests they would change the verdict.

---

## 12. Homograph corollaries

- **Prefilter.** `C_6 < 1` means no exact 6-string homograph at this alignment. `C_6 = 1`
  sends the pair on to the full fretboard and physics solver.
- **Construction residue.** In a constructed homograph, A's fingering is constrained by B's
  hidden offsets: the same audible note may sit on different strings for no playing reason (Old
  MacDonald's three opening C4s land on D10, D10, G5). A detector scoring fingering
  improbability given the audible melody alone could flag constructed homographs. Natural
  homographs need not carry this residue.
- **In real songs** (measured separately):
  - [R04](../results/RESULTS-R04-scan.md): short passages of unrelated folk songs often share
    a tab, and string tension rarely forbids it, but comfortable shared tabs are rare;
  - [R05](../results/RESULTS-R05-aswritten.md): a real, long fingering with its tuning stated
    nearly determines its music.

---

## 13. Terminology

```text
pointwise offset sequence       Delta(A,B) = B - A
offset richness                 r = number of distinct offsets    (was "rank"; avoids clashes
                                                                   with matrix rank)
log-richness distance           d_0 = log2 r
offset entropy                  d_1 = H(Delta);   effective number R_eff = 2^H
modal share / TI-Hamming        C_1;   d_H = 1 - C_1
top-k coverage                  C_k   (prefilter; no metric claim for k > 1)
switch count                    S = interval Hamming distance
total variation                 TV = interval L1 distance
reuse                           u = S + 1 - r
```

gtrsnipe's `--homograph` report prints "Richness"; keep that label synchronized with this note.

---

## 14. History of this note

Each revision narrowed what could be claimed.

- **The original draft** (2026-09-26, scottvr, developed with ChatGPT, from a remark of Claude's
  that log(richness) behaves like a distance). It presented the offset statistics as candidate
  new results, including a family of metrics across the Hill/Rényi orders. It isn't kept in
  the repo; its homograph corollaries survive, condensed, in §12.
- **Revision 1** (2026-09-26, Claude). A numeric triangle check found counterexamples at Rényi
  orders ½, 2 and ∞, so there is no family of metrics. A prior-art pass found established names
  for nearly every statistic: the metric facts are elementary. What was left as possibly new
  was "vocabulary vs. switches", with a usefulness test and a decision rule. scottvr then
  corrected it: richness is a lower bound on string demand, and "richness ≤ s" is a budget, not
  an equivalence relation.
- **The research track** (2026-09-26/27):
  - the literature survey (R06) found no other order works, and no music measure counts the
    offset vocabulary;
  - the alignment proof (R07) settled revision 1's guess about optimized alignment, which was
    half wrong (the switch count and total variation survive too). It was reviewed by scottvr
    with ChatGPT, and then by Gemini;
  - the tune-family test (R03) came back negative.
- **Revision 2** (2026-09-28, Claude). Update boxes for those outcomes.
- **Revision 3** (2026-09-29, Claude). A rewrite, so that every section states what is known
  now. The new finding: vocabulary vs. switches is the label-cost vs. Potts distinction of
  computer vision, and the homograph is multi-model fitting with a label budget (scottvr's
  question about image processing led there). The note no longer claims anything as new.

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

With details from the literature survey (R06; its "Verified" column says how each was checked):

- M. O. Hill. *Diversity and evenness: a unifying notation and its consequences.*
  Ecology 54(2):427–432, 1973. doi:10.2307/1934352
- L. Jost. *Entropy and diversity.* Oikos 113(2):363–375, 2006.
  doi:10.1111/j.2006.0030-1299.14714.x
- W. H. Berger, F. L. Parker. *Science* 168:1345–1347, 1970. doi:10.1126/science.168.3937.1345
- J. Aczél, B. Forte, C. T. Ng. *Why the Shannon and Hartley entropies are "natural".*
  Adv. Appl. Probab. 6(1):131–146, 1974. doi:10.2307/1426210
- C. Callender, I. Quinn, D. Tymoczko. *Generalized voice-leading spaces.* Science
  320:346–348, 2008. doi:10.1126/science.1153021
- T. Tao. *Sumset and inverse sumset theory for Shannon entropy.* Combinatorics,
  Probability and Computing 19(4):603–639, 2010. doi:10.1017/S0963548309990642 (a
  contrast only: it concerns independent summands)
- D. Lewin. *Re: Intervallic relations between two collections of notes.* JMT
  3(2):298–301, 1959 (doi:10.2307/842856); and *Generalized Musical Intervals and
  Transformations*, 1987.
- K. Lemström, E. Ukkonen. *Including interval encoding into edit distance based
  music comparison and retrieval.* AISB 2000, pp. 53–60.
- K. Lemström, V. Mäkinen. CPM 2003 (LNCS 2676:237–253); *J. Discrete Algorithms*
  3(2–4):248–266, 2005.
- E. Ukkonen, K. Lemström, V. Mäkinen. *Geometric algorithms for transposition
  invariant content-based music retrieval.* ISMIR 2003. doi:10.5281/zenodo.1417477
- D. Müllensiefen, K. Frieler. *Computing in Musicology* 13:147–176, 2004 (SIMILE).
- J. N. Straus. *Music Theory Spectrum* 25(2):305–352, 2003.
- A. Allen, C. Goudeseune. *Topological considerations for tuning and fingering stringed
  instruments.* arXiv:1105.1383, 2011.

Not yet verified (from memory; check before citing):

- M. Meilă. *Comparing clusterings: an information based distance.* J. Multivariate
  Analysis, 2007 (COLT 2003).
- T. Eiter, H. Mannila. *Computing discrete Fréchet distance.* Tech. Report CD-TR 94/64,
  TU Vienna, 1994.
- L. I. Rudin, S. Osher, E. Fatemi. *Nonlinear total variation based noise removal
  algorithms.* Physica D 60:259–268, 1992.
- L. Xu, C. Lu, Y. Xu, J. Jia. *Image smoothing via L0 gradient minimization.* ACM Trans.
  Graphics (SIGGRAPH Asia) 30(6), 2011.
- A. Delong, A. Osokin, H. N. Isack, Y. Boykov. *Fast approximate energy minimization with
  label costs.* Int. J. Computer Vision 96(1):1–27, 2012.
- H. Isack, Y. Boykov. *Energy-based geometric multi-model fitting.* Int. J. Computer Vision
  97(2):123–147, 2012.
- J. Y. A. Wang, E. H. Adelson. *Representing moving images with layers.* IEEE Trans. Image
  Processing 3(5):625–638, 1994.
- A. Oliva, A. Torralba, P. G. Schyns. *Hybrid images.* ACM Trans. Graphics (SIGGRAPH)
  25(3):527–532, 2006.
