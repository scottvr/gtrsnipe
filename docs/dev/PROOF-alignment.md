# Offset distances under optimized alignment (backlog R07)

This settles the "candidate result" in §7 of
[`coupled_transposition_structure.md`](coupled_transposition_structure.md). That section
guessed that log-richness might stay a metric when the alignment is optimized, and that
Shannon entropy, switch count S and total variation TV might not. **Half of the guess was
wrong.** The general statement:

> **A statistic of the offset sequence that ignores consecutive repeats and is subadditive
> stays a pseudometric when minimized over warping paths.** Log-richness, S and TV are
> instances; so are the largest jump and the offset range (twice a transposition-invariant
> discrete Fréchet distance). Shannon entropy and TI-Hamming (1 − C₁) count how long each
> offset lasts, and they fail.

A warping path may hold a note against several notes of the other melody, which *stretches*
the offset sequence. Statistics of the offsets that occur (richness), of the changes between
them (S), or of the size of those changes (TV, the largest jump, the range) do not see
stretching. Statistics of how long each offset lasts (entropy, the modal share) do. Warping
reweights notes, as §7 feared, but reweighting only matters to statistics that count
weights.

Numeric check: [`alignment_check.py`](alignment_check.py) enumerates every path for short
melodies. In 5,000 random triples it finds no violation for the stutter-invariant statistics,
and many for entropy and 1 − C₁.

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

## Corollary: which distances qualify

Each statistic below satisfies (a)–(d). Since richness ≥ 1, the first uses log₂ r.

| f | (b) subadditivity, because | notes |
|---|---|---|
| log₂ richness | \|set(x + y)\| ≤ \|set(x)\|·\|set(y)\| (sumset bound) | the offset vocabulary; the guitar's string lower bound |
| switches S | x + y changes only where x or y changes | the fewest changes of relative transposition, with free note-stretching |
| variation TV | \|Δx + Δy\| ≤ \|Δx\| + \|Δy\|, summed | |
| largest jump J | the same, as a maximum | |
| range R | max(x + y) ≤ max x + max y, and min(x + y) ≥ min x + min y | R/2 = the least possible max\|δ − c\| over real transpositions c: **a transposition-invariant discrete Fréchet distance** (below). With whole-semitone c it is ⌈R/2⌉, still a pseudometric since ⌈(a+b)/2⌉ ≤ ⌈a/2⌉ + ⌈b/2⌉ |

The class is closed under non-negative sums and under maxima of its members, so S + TV or
max(R, J) qualify too. Stutter-invariance is *sufficient*, not claimed necessary. Entropy and
1 − C₁ fail it, and the counterexample shows they fail the conclusion as well.

## Counterexample for entropy and modal share

Take A = (G4), B = (F4, F4) and C = (E4, F4), writing 7, 5 5 and 4 5 for pitches.
- d(A, B) = 0: the only path pairs G4 with both F4s, so the offsets are −2, −2.
- d(B, C): the best path (1,1), (1,2), (2,2) has offsets −1, 0, 0. That gives H = 0.918 and
  1 − C₁ = 1/3.
- d(A, C): the only path pairs G4 with E4 and with F4, so the offsets are −3, −2. That gives
  H = 1 and 1 − C₁ = 1/2.

So d(A, C) > d(A, B) + d(B, C) for both measures. From B, a path may *repeat* the matching note
to outvote the mismatch. A has only one note, so no path from A can reweight that way. In the
lemma's terms, the lifted walk here is (1,1,1), (1,1,2), (1,2,2):
- its sum sequence (−3, −2, −2) would satisfy the entropy bound (0.918 ≤ 0 + 0.918);
- but the last triple repeats the A–C cell (1, 2);
- a legal path cannot keep that repeat, and dropping it is exactly the reweighting that
  breaks entropy.

## Relation to known work: the discrete Fréchet (Frechet) distance

The discrete Fréchet distance between two point sequences is the minimum, over couplings
(exactly our warping paths), of the largest pointwise distance. It is known to be a
pseudometric, zero exactly when the sequences agree after merging consecutive repeats. Its
triangle inequality is proved, I believe, by composing couplings through the middle sequence,
which is this lemma. The maximum is stutter-invariant, so the discrete Fréchet distance is the
prototype of the class above. Applied to pitch with transposition factored out, it is R/2 in
the corollary table: exactly R/2 when the transposition may be any real number, ⌈R/2⌉ when
it must be whole semitones.

So **the composition argument is not new**. What this note adds:
- the explicit condition, stutter-invariance plus subadditivity;
- applying it to the *offset* sequence, which makes every member transposition-invariant for
  free;
- the members richness, S and TV, with richness's physical reading as a lower bound on
  strings.

Whether the general condition is written down anywhere needs a literature search before any
novelty claim. Starting points: Eiter & Mannila's discrete Fréchet report (1994), Alt &
Godau's Fréchet paper (1995), and the elastic distances built to be metrics (ERP, TWED,
Move-Split-Merge). *These citations were not verified in this session.*

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
    minimum-label path problem, which is NP-hard on general graphs; its complexity on this
    grid is open here, so don't claim anything about it. Fixed k is easy: try each set of at
    most k offsets, then check whether a path exists through cells labelled with them. k ≤ 6
    is the guitar case.
- **What this does not say.** The R03 experiment found that richness is a weak tune-family
  similarity measure under a fixed grid alignment. This result is about the *geometry* of the
  measures, not their usefulness.

## Review

Reviewed 2026-09-26 by scottvr with ChatGPT. Incorporated from that review:
- the separation of the lifted walk Q̃ from the path Q, and the explicit argument that
  deduplication is harmless;
- the canonical zero-set wording and the quotient;
- extracting the general principle.

The Fréchet connection and the extra members (J, R) were added in the revision. The
whole-semitone ⌈R/2⌉ refinement also came from the review.
