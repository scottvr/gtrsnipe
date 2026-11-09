# Offset distances under optimized alignment (backlog R07)

This settles the "candidate result" in §7 of
[`coupled_transposition_structure.md`](coupled_transposition_structure.md). That section
guessed that log-richness might stay a metric when the alignment is optimized, and that
Shannon entropy, switch count S and total variation TV might not. **Half of the guess was
wrong.** The general statement:

> **A statistic of the offset sequence that ignores consecutive repeats and is subadditive
> stays a pseudometric when minimized over warping paths.** Log-richness, S and TV are
> instances; so are the largest jump and the offset range (twice a transposition-invariant
> discrete Fréchet distance when the transposition may be any real number; with whole
> semitones, up to rounding: see "Relation to known work" below). Shannon entropy and TI-Hamming (1 − C₁) count how long each
> offset lasts, and they fail.

A warping path may hold a note against several notes of the other melody, which *stretches*
the offset sequence. Statistics of the offsets that occur (richness), of the changes between
them (S), or of the size of those changes (TV, the largest jump, the range) do not see
stretching. Statistics of how long each offset lasts (entropy, the modal share) do. Warping
reweights notes, as §7 feared, but reweighting only matters to statistics that count
weights.

Numeric check: [`alignment_check.py`](alignment_check.py) enumerates every path for short
melodies. Run with 5,000 random triples (`python alignment_check.py 5000`; the default is
3,000), it finds no violation for the stutter-invariant statistics, 92 for entropy and 130 for
1 − C₁. The smallest violation it finds is the counterexample below.

## Setup

Melodies are A = (a₁…aₙ), B = (b₁…bₘ), C = (c₁…c_p), with integer pitches.

A **warping path** P from A to B is a sequence of index pairs from (1, 1) to (n, m), each step
(1,0), (0,1) or (1,1). It is the alignment dynamic time warping uses, also called a coupling:
- every note takes part;
- nothing crosses;
- one note may pair with several consecutive notes of the other melody. That is the
  "ta ≈ ti ti" of re-rhythming, without a cap.

The **offset sequence** along P is δ_P = (b_j − a_i) for (i, j) in path order. For a statistic
f of finite integer sequences, define

    d_f(A, B) = min over warping paths P of f(δ_P).

**Stuttering.** A *stuttering* of a sequence repeats some of its elements in place:
(5, 7) → (5, 5, 5, 7, 7). Its *run collapse* merges consecutive repeats: (5, 5, 5, 7, 7) →
(5, 7). A statistic is **stutter-invariant** if it depends only on the run collapse.

| f | definition | stutter-invariant? |
|---|---|---|
| log₂ richness | log₂ \|set(δ)\| | yes: the set of values |
| switches S | #{t : δ_{t+1} ≠ δ_t} | yes: repeats add no changes |
| variation TV | Σ \|δ_{t+1} − δ_t\| | yes: repeats add zero |
| largest jump J | max \|δ_{t+1} − δ_t\| (0 for one note) | yes |
| range R | max δ − min δ | yes |
| entropy H | Shannon entropy of the offset counts | **no**: counts multiplicities |
| 1 − C₁ | 1 − (count of the modal offset)/length | **no** |

## Lemma (composing paths through B)

Let P₁ be a warping path from A to B and P₂ one from B to C. There is a **lifted walk** Q̃, a
sequence of index triples (iₜ, jₜ, kₜ) for t = 1…L, such that:

1. **Witness.** Every triple has (iₜ, jₜ) ∈ P₁ and (jₜ, kₜ) ∈ P₂, so

       c_{kₜ} − a_{iₜ} = (b_{jₜ} − a_{iₜ}) + (c_{kₜ} − b_{jₜ}) = xₜ + yₜ.

2. **Stuttered inputs.** Read along Q̃, the pairs (iₜ, jₜ) visit P₁'s pairs in path order,
   each at least once and consecutively. So x = (x₁…x_L) is a stuttering of δ_P₁. Likewise
   y is a stuttering of δ_P₂.
3. **A legal A–C path after deduplication.** Projected onto (i, k), each step of Q̃ is (1,0),
   (0,1), (1,1), or occasionally (0,0). Deleting the (0,0) steps (consecutive duplicate (i, k)
   pairs) leaves a warping path Q from A to C.

*Proof.* In a warping path the second index never decreases and moves by at most 1. So for
each note j of B, the pairs of P₁ that use j:
- form one consecutive stretch of the path (j is never revisited);
- have A indices filling an interval I(j) = [lo₁(j), hi₁(j)], visited in increasing order,
  because within the stretch every step is (1, 0);
- are followed by a stretch for j+1 with lo₁(j+1) − hi₁(j) ∈ {0, 1}.

The same holds for P₂ with C intervals K(j) = [lo₂(j), hi₂(j)].

Build Q̃ one block at a time, for j = 1…m:
- **Inside block j**, walk from (lo₁(j), j, lo₂(j)) to (hi₁(j), j, hi₂(j)) by unit steps:
  first raise i to hi₁(j), then raise k to hi₂(j). Every triple here has i ∈ I(j) and
  k ∈ K(j), so j is its witness (property 1).
- **From block j to j+1**, i rises by lo₁(j+1) − hi₁(j) ∈ {0, 1} and k by
  lo₂(j+1) − hi₂(j) ∈ {0, 1}, so the projected step is (1,0), (0,1), (1,1) or (0,0).
- **The ends.** The walk starts at (1, 1, 1) and ends at (n, m, p), because both paths start
  and end at their corners.

Property 2: projected onto (i, j), the walk runs through P₁'s block-j pairs in order,
pausing while k moves, then steps to P₁'s next pair. Property 3: the projected steps are unit
steps or (0, 0), both coordinates are monotone and cover 1…n and 1…p, and deleting the
(0, 0) steps leaves a warping path. ∎

**Why deduplication is harmless.** A (0, 0) step in (i, k) happens only between blocks, when
B advances but A and C don't: (i, j, k) → (i, j+1, k). The witnessed parts xₜ and yₜ may both
change there, but their sum c_k − a_i cannot, because it depends only on (i, k). So the
offset sequence õ = x + y along Q̃ is a **stuttering of δ_Q**: deleting duplicate cells
deletes only consecutive repeats of equal offsets.

## Theorem (the stutter-invariance principle)

Let f be a statistic of finite integer sequences with:
- (a) **stutter-invariance**: f depends only on the run collapse;
- (b) **subadditivity**: f(x + y) ≤ f(x) + f(y) for sequences of equal length (pointwise sum);
- (c) **evenness**: f(−x) = f(x);
- (d) **normalization**: f(x) ≥ 0, with f(x) = 0 exactly when x is constant.

Then d_f is a pseudometric on melodies:

    d_f(A, A) = 0,   d_f(A, B) = d_f(B, A),   d_f(A, C) ≤ d_f(A, B) + d_f(B, C),

and d_f(A, B) = 0 **iff the run-collapsed pitch sequences of A and B are transpositions of
each other.** So d_f is a metric on the quotient

    melodies / (global transposition + splitting or merging repeated consecutive notes).

*Proof.*
- **Zero and symmetry.** The diagonal path of A with itself has offsets all 0, so
  d_f(A, A) = 0 by (d). Swapping A and B mirrors every path and negates every offset, so by
  (c) the minimum is the same.
- **Triangle.** Take P₁ and P₂ optimal for d_f(A, B) and d_f(B, C), and build Q̃, Q, x, y
  from the lemma. Then

      d_f(A, C) ≤ f(δ_Q) = f(x + y) ≤ f(x) + f(y) = f(δ_P₁) + f(δ_P₂) = d_f(A, B) + d_f(B, C).

  The first step holds because Q is a warping path. The equality f(δ_Q) = f(x + y) is (a),
  since x + y is a stuttering of δ_Q. The next inequality is (b), for the equal-length x
  and y. The last equality is (a) again, since x and y are stutterings of δ_P₁ and δ_P₂.
- **Zero set.** By (d), d_f(A, B) = 0 iff some path has a constant offset c.
  - *Only if:* a (1, 0) step keeps the offset only if a repeats its pitch, a (0, 1) step
    only if b does, and a (1, 1) step only if both move by the same interval. So A's pitch
    changes and B's occur together, and the collapsed sequences satisfy
    collapse(B) = collapse(A) + c.
  - *If:* pair the r-th run of A with the r-th run of B (any staircase through the block),
    and step (1, 1) between runs. Every pair then has offset c. ∎

## Proposition: transposition invariance is not an extra axiom

Let **c** be a constant sequence. Then f(x + **c**) = f(x) for every x, using only (b) and
(d): f(x + **c**) ≤ f(x) + f(**c**) = f(x), and f(x) = f((x + **c**) − **c**) ≤ f(x + **c**) +
f(−**c**) = f(x + **c**). So any statistic meeting the hypotheses is automatically unchanged by
a global transposition of either melody; the theorem concerns transposition-invariant
distances because of (b) and (d), not by a separate assumption.

The quotient metric is well defined for the usual reason: if d_f(A, A′) = 0 and
d_f(B, B′) = 0, two applications of the triangle inequality give d_f(A, B) = d_f(A′, B′).

## Corollary: which distances qualify

Each statistic below satisfies (a)–(d). Since richness ≥ 1, the first uses log₂ r.

| f | (b) subadditivity, because | notes |
|---|---|---|
| log₂ richness | \|set(x + y)\| ≤ \|set(x)\|·\|set(y)\| (sumset bound) | the offset vocabulary; the guitar's string lower bound |
| switches S | x + y changes only where x or y changes | the fewest changes of relative transposition, with free note-stretching |
| variation TV | \|Δx + Δy\| ≤ \|Δx\| + \|Δy\|, summed | |
| largest jump J | the same, as a maximum | |
| range R | max(x + y) ≤ max x + max y, and min(x + y) ≥ min x + min y | R/2 = the least possible max\|δ − c\| over real transpositions c: **a transposition-invariant discrete Fréchet distance** (below). With whole-semitone c it is ⌈R/2⌉, still a pseudometric since ⌈(a+b)/2⌉ ≤ ⌈a/2⌉ + ⌈b/2⌉ |

The class is closed under non-negative linear combinations with at least one positive
coefficient (all-zero coefficients give the zero functional, which fails (d)) and under maxima
of its members, so S + TV or max(S, R) qualify too. max(R, J) does not add anything, because
J ≤ R. Stutter-invariance is *sufficient*, not claimed necessary. Entropy and 1 − C₁ fail it,
and the counterexample shows they fail the conclusion as well.

**Order among the members.** For integer offsets, pointwise in δ:

    J ≤ R ≤ TV,     S ≤ TV,     richness − 1 ≤ S,     richness − 1 ≤ R.

(The largest step is at most the range; walking from the minimum to the maximum costs at least
R; each change costs at least 1; a sequence with r distinct values has at least r runs; r
distinct integers span at least r − 1.) A pointwise inequality f ≤ g survives minimization
over the same set of paths, so d_J ≤ d_R ≤ d_TV, d_S ≤ d_TV, and
d_{log₂ richness} ≤ log₂(d_S + 1), ≤ log₂(d_R + 1). Of the Hill numbers, only order 0
(richness) is stutter-invariant; every positive order counts how long each offset lasts.

## Counterexample for entropy and modal share

Take A = (G4), B = (F4, F4) and C = (E4, F4), writing 7, 5 5 and 4 5 for pitches.
- d(A, B) = 0: the only path pairs G4 with both F4s, so the offsets are −2, −2.
- d(B, C): the best path (1,1), (1,2), (2,2) has offsets −1, 0, 0. That gives H = 0.918 and
  1 − C₁ = 1/3.
- d(A, C): the only path pairs G4 with E4 and with F4, so the offsets are −3, −2. That gives
  H = 1 and 1 − C₁ = 1/2.

So d(A, C) > d(A, B) + d(B, C) for both measures. **It is the smallest counterexample by total
length.** With four notes or fewer the shapes are (1, 1, 1), (1, 2, 1), (1, 1, 2) and (2, 1, 1).
When A and C are single notes, d(A, C) = 0. When A and B are single notes, d(A, B) = 0 and
d(B, C) = d(A, C), because each has one path and the two offset sequences differ by a
constant, which neither measure sees. (2, 1, 1) is the mirror image. So no triple of total
length ≤ 4 violates, for any pitches; [`minimal_counterexample_check.py`](minimal_counterexample_check.py)
confirms this exhaustively over an 8-pitch alphabet (0 violations at total length ≤ 4, 896 at
total length 5). From B, a path may *repeat* the matching note to outvote the mismatch. A has only one note, so no path from A can reweight that way. In the
lemma's terms, the lifted walk here is (1,1,1), (1,1,2), (1,2,2):
- its sum sequence (−3, −2, −2) would satisfy the entropy bound (0.918 ≤ 0 + 0.918);
- but the last triple repeats the A–C cell (1, 2);
- a legal path cannot keep that repeat, and dropping it is exactly the reweighting that
  breaks entropy.

## Relation to known work: Fréchet, elastic distances and stutter-invariant costs (Frechet)

There are two classic families of alignment distances. Each sits on one side of this note's
dividing line (occupancy-sensitive vs stutter-invariant), and a third family escapes the
problem another way.

### 1. Summed costs (DTW): occupancy-sensitive, not metrics

Dynamic time warping sums a per-cell cost over the path (e.g. Σ \|a_i − b_j\|). A note held
against three notes of the other melody is charged three times, so the path's multiplicities
enter the total. That is the entropy/TI-Hamming situation above, and DTW is well known *not* to
satisfy the triangle inequality. Composing two optimal paths reweights the cells, which is the
§7 intuition.

### 2. Maximum cost (Fréchet): stutter-invariant, a pseudometric

The **discrete Fréchet distance** is the minimum over couplings (our warping paths) of the
*largest* pointwise distance. A maximum does not care how often a value is repeated, so it is
stutter-invariant and subadditive: exactly the theorem's hypotheses. The discrete Fréchet
distance is the class's prototype. Its triangle inequality composes two couplings through the
middle sequence, which is our lemma. The continuous Fréchet distance is the same idea for
curves: stutter-invariance becomes invariance under monotone reparametrization.

On pitch with transposition factored out, the Fréchet distance of the offset sequence is
R/2 (⌈R/2⌉ for whole semitones), the range row of the corollary.

### 3. Paying for stretching (ERP, TWED, Move-Split-Merge): metrics by a different route

Several time-series distances were *built* to be metrics while staying elastic:
- ERP (edit distance with real penalty);
- TWED (time warp edit distance);
- MSM (move–split–merge).

They are edit distances: stretching a sequence (a gap, a split or a merge) has a cost, and the
costs are chosen so that the edit operations compose metrically. That is the opposite of this
note's route. Here stretching is **free**, and metricity comes from restricting the statistic
to be **stutter-invariant**.

### Where this note's distances sit

| family | stretching | the cost is a function of | metric? |
|---|---|---|---|
| DTW | free | the multiset of cells visited (occupancy) | no |
| discrete Fréchet | free | the max over cells visited | yes (pseudometric) |
| ERP, TWED, MSM | charged | edit operations | yes, by design |
| **this note** | free | a stutter-invariant, subadditive functional of the **offset sequence** δ = b − a | yes (pseudometric): the theorem |
| entropy, 1 − C₁ under warping | free | occupancy of offset values | no (counterexample above) |

The two distinguishing choices:
- **The functional acts on the signed offset sequence,** not on pointwise distances \|a − b\|.
  That makes every member transposition-invariant (each is unchanged by δ → δ + c).
- **The members are functionals of the sequence as a whole,** not only a maximum: the number of
  distinct values, the number of changes, the total and largest change, the range.

**What is known, and what we did not find.**
- The composition mechanism is known: it is the one in the standard proof that the discrete
  Fréchet distance is a metric, and its discrete form for warping paths is worked out by Jain
  (2019): expansions by replication, the condensed form (our run collapse), warping functions
  as monotone surjections, the remark that warping paths are not closed under composition,
  and a common refinement of two warping functions onto the same middle sequence (his Lemma
  28), which is our lifted walk. Jain stops at a warping-invariant *semi-metric* for his
  summed DTW cost; a summed cost is occupancy-sensitive, so the triangle inequality is not
  claimed there.
- The property (a) has a name in the time-series literature: Diehl, Ebrahimi-Fard & Tapia
  (2020) call a functional *time-warping invariant* when it is unchanged by duplicating any
  element in place, and describe the series as allowed to "stand still" or "stutter". The
  formal-methods *stutter equivalence* (equality after collapsing repeats) is the same
  relation. "Stutter-invariant" is therefore not a false friend; the paper can keep it and
  name the two other vocabularies once.
- We did not find the general sufficient condition (any stutter-invariant, subadditive
  functional of the coupled differences) stated elsewhere; it may be known informally. It is
  presented with its proof, without a claim of priority.
- Likewise unknown: whether d_S (the fewest changes of relative transposition, with free
  stretching) or d_richness (the fewest distinct transpositions, with free stretching) appear
  under other names. The closest known relatives are local-transposition alignment (Allali et
  al.) and Lemström & Mäkinen's minimum number of pieces, both from
  [`LITERATURE-offsets.md`](../literature/LITERATURE-offsets.md) §1. Both charge a switch or piece every
  time the transposition changes. For Lemström & Mäkinen that includes a return to an earlier
  one; for Allali et al. it is inferred, not confirmed (see the table below).

### Citations to verify (R13; none checked when this note was written)

- [ ] T. Eiter, H. Mannila, *Computing discrete Fréchet distance*, Tech. Report CD-TR 94/64, Christian Doppler Laboratory for Expert Systems, TU Vienna, 1994 — relied on for: the definition of the discrete Fréchet distance via couplings; that it is a (pseudo)metric
- [ ] H. Alt, M. Godau, "Computing the Fréchet distance between two polygonal curves," *Int. J. Computational Geometry & Applications* 5(1–2):75–91, 1995 — relied on for: the continuous Fréchet distance; reparametrization invariance
- [ ] H. Sakoe, S. Chiba, "Dynamic programming algorithm optimization for spoken word recognition," *IEEE Trans. ASSP* 26(1):43–49, 1978 — relied on for: DTW's definition
- [ ] any standard source that DTW violates the triangle inequality — relied on for: DTW is not a metric
- [ ] L. Chen, R. Ng, "On the marriage of Lp-norms and edit distance," VLDB 2004, pp. 792–803 — relied on for: ERP is a metric
- [ ] P.-F. Marteau, "Time warp edit distance with stiffness adjustment for time series matching," *IEEE TPAMI* 31(2):306–318, 2009 — relied on for: TWED is a metric
- [x] M. R. Fellows, J. Guo, I. Kanj, "The parameterized complexity of some minimum label problems," *J. Computer and System Sciences* 76(8):727–740, 2010 (WG 2009) — relied on for: Minimum Label Path is NP-hard and W[2]-hard by number of labels even at bounded pathwidth (verified 2026-11-07 from the abstract and the WG slides; the bounded-pathwidth constant differs between sources, check the paper before quoting it)
- [x] B. J. Jain, "Making the dynamic time warping distance warping-invariant," *Pattern Recognition* 94:35–52, 2019 (arXiv:1903.01454) — relied on for: expansions/condensed form, warping functions as monotone surjections, common refinement (Lemma 28), twi distance a semi-metric (Theorem 5) (verified 2026-11-07 against the ar5iv text)
- [x] J. Diehl, K. Ebrahimi-Fard, N. Tapia, "Time-warping invariants of multidimensional time series," *Acta Applicandae Mathematicae* 170:265–290, 2020 (arXiv:1906.05823) — relied on for: the term "time-warping invariant" for a functional unchanged by duplicating an element, and the "stutter" wording (verified 2026-11-07 from the abstract and keywords; theorems not read)
- [ ] J. Allali, P. Ferraro, P. Hanna, C. Iliopoulos, "Local transpositions in alignment of polyphonic musical sequences," SPIRE 2007 — relied on for: that a return to an earlier transposition is charged again (inferred in the survey, not confirmed)
- [ ] A. Stefan, V. Athitsos, G. Das, "The Move-Split-Merge metric for time series," *IEEE TKDE* 25(6):1425–1438, 2013 — relied on for: MSM is a metric

What to look for while verifying:
1. Does any Fréchet or time-series source state the triangle inequality for a *general* class
   of coupling costs, beyond the maximum? Look for "Fréchet-like", "coupling distance",
   "bottleneck" and "reparametrization-invariant functional".
2. Is there a known name for "minimum over couplings of the number of changes" (or the number
   of distinct values) of a difference sequence? Search the run-length-encoded string matching
   literature too: stutter-invariance is invariance under run-length expansion.
3. Does the music-retrieval literature use Fréchet distances on pitch sequences with
   transposition factored out? That is R/2 here.

## Caveats

- **A capped re-rhythm is not covered.** gtrsnipe's `--homograph-subdivide K` lets one note
  stand for at most K. Block j of Q̃ pairs up to |I(j)| + |K(j)| − 1 notes, so paths with a
  cap are not closed under composition, and the theorem says nothing about them.
- **The zero set is coarser than in the aligned case.** With a fixed note-for-note alignment,
  d = 0 means an exact transposition. Here it means a transposition of the run-collapsed
  sequences.
- **Computing it.**
  - d_S, d_TV and d_J are shortest paths (for J, bottleneck paths) through the n × m grid. A
    cell's offset is fixed by the cell, so each step's cost depends only on the two cells:
    O(nm) time.
  - d_R needs the best path *and* the best transposition. For each candidate window of
    offsets, check whether a path stays inside it: polynomial.
  - d_richness asks for the grid path using the fewest distinct offsets. That is a
    minimum-label path problem. On general graphs it is NP-hard, and W[2]-hard when
    parameterized by the number of labels even at bounded pathwidth (Fellows, Guo & Kanj
    2010, by reduction from Hitting Set). Its complexity on this grid, with the special
    labels δ_ij = b_j − a_i, is open here, so don't claim anything about it. Three separate
    true statements, not to be merged:
    1. **Fixed offset budget k** (the guitar's k ≤ 6): try each set of at most k of the L
       distinct offsets in the grid and test reachability: O(L^k · nm). Polynomial for each
       fixed k, with k in the exponent: XP, not FPT in k.
    2. **Bounded pitch alphabet** (MIDI, or an instrument's sounding range): L is a constant,
       so even the full subset register is polynomial in nm, with a constant that may be
       astronomical.
    3. **Variable k, unbounded alphabet:** the parameterized status is not established by
       either argument.
    In practice the exact value is computed by a dynamic programme whose state is the grid
    cell plus the set of offsets used so far (a bitmask), dropping sets larger than k and
    keeping only inclusion-minimal sets per cell (`gtrsnipe/research/segments.py`,
    `warped_richness`, R03b). The cap and the dominance rule are both lossless; the running
    time is explained by dominance and by the small number of distinct offsets a real pair
    of phrases produces, which no bound here accounts for.
- **What this does not say.** The R03 experiment found that richness is a weak tune-family
  similarity measure under a fixed grid alignment. This result is about the *geometry* of the
  measures, not their usefulness.

## Review

Drafted by Claude on 2026-09-26 (R07), answering the §7 guess of revision 1 of the structure
note, which was also Claude's.

Reviewed 2026-09-26 by scottvr with ChatGPT. Incorporated from that review:
- the separation of the lifted walk Q̃ from the path Q, and the explicit argument that
  deduplication is harmless;
- the canonical zero-set wording and the quotient;
- extracting the general principle (stated as the theorem above);
- the whole-semitone ⌈R/2⌉ refinement.

In Claude's revision after that review: the Fréchet connection (the composition step uses the
same mechanism as the discrete Fréchet distance's triangle proof), and the extra members J and
R.

scottvr then took the revised proof to Gemini, which approved it and contributed a figure
template ([`../results/collision_plot_template.py`](../results/collision_plot_template.py)).

Revised 2026-11-07 by Claude from the compiled adversarial feedback
([`20261107-latest-feedback-compilation.md`](20261107-latest-feedback-compilation.md)):
the transposition-invariance proposition and the quotient remark; the closure statement
qualified and max(R, J) replaced by max(S, R); the order among the members; the counterexample
shown minimal by total length (with a check script); the computing-richness caveat split into
three claims with the register DP named; Jain 2019, Diehl et al. 2020 and Fellows–Guo–Kanj
2010 added and verified. Still open from that feedback: whether the general theorem is a
stated special case of a known coupling/quotient construction (the "crossing of mapped roads"
assessment), and whether stutter-invariance can be weakened to a monotonicity under
refinement.
