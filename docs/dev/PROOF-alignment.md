# Offset distances under optimized alignment (backlog R07)

This settles the "candidate result" in §7 of
[`coupled_transposition_structure.md`](coupled_transposition_structure.md). That section
guessed that log-richness might stay a metric when the alignment is optimized, and that
Shannon entropy, switch count S and total variation TV might not. **Half of the guess was
wrong:**

> Under warping-path alignment, log-richness, S and TV all remain pseudometrics. Shannon
> entropy and TI-Hamming (1 − C₁) do not.

The dividing line is not "set versus distribution". It is whether the statistic changes when
an alignment repeats a note:
- richness depends only on the *set* of offsets;
- S and TV depend on the *sequence* of offsets but ignore consecutive repeats;
- entropy and modal share count *multiplicities*, and repeating a note changes those.

Numeric check: [`alignment_check.py`](alignment_check.py) enumerates every path for short
melodies. It found 0 violations for richness, S and TV in 5,000 random triples, and many for
entropy and 1 − C₁.

## Setup

Melodies are A = (a₁…aₙ), B = (b₁…bₘ), C = (c₁…c_p), with integer pitches.

A **warping path** P from A to B is a sequence of index pairs from (1, 1) to (n, m), each step
(1,0), (0,1) or (1,1). It is the alignment dynamic time warping uses: every note takes part,
nothing crosses, and one note may pair with several consecutive notes of the other melody
(the "ta ≈ ti ti" of re-rhythming, without a cap).

The offsets along P are the sequence δ_P = (b_j − a_i) for (i, j) in path order. For a
statistic f of that sequence, define

    d_f(A, B) = min over warping paths P of f(δ_P).

The statistics in question:

| f | definition | depends on |
|---|---|---|
| log₂ richness | log₂ \|set(δ_P)\| | the set of offsets |
| switches S | #{t : δ_{t+1} ≠ δ_t} | the sequence, up to consecutive repeats |
| variation TV | Σ \|δ_{t+1} − δ_t\| | the sequence, up to consecutive repeats |
| entropy H | Shannon entropy of the offset counts | multiplicities |
| 1 − C₁ | 1 − (count of the modal offset)/length | multiplicities |

## Lemma (composing paths)

Given warping paths P₁ from A to B and P₂ from B to C, there is a warping path Q from A to C,
and a sequence of index triples (iₜ, jₜ, kₜ), such that:

1. the pairs (iₜ, kₜ) run through Q in order, possibly repeating a pair on consecutive
   steps;
2. the pairs (iₜ, jₜ) run through P₁ in order, and the pairs (jₜ, kₜ) through P₂, each
   possibly with consecutive repeats;
3. for every t, (iₜ, jₜ) ∈ P₁ and (jₜ, kₜ) ∈ P₂. So jₜ is a *witness*, and

       c_{kₜ} − a_{iₜ} = (b_{jₜ} − a_{iₜ}) + (c_{kₜ} − b_{jₜ}) = xₜ + yₜ,

   where x is P₁'s offset sequence and y is P₂'s, each with consecutive repeats.

*Proof.* For each note j of B, the pairs of P₁ that use j have consecutive i values
I(j) = [lo₁(j), hi₁(j)], and P₁ visits them in increasing order. Likewise the pairs of P₂
that use j cover K(j) = [lo₂(j), hi₂(j)]. Because P₁ is a warping path,
lo₁(j+1) − hi₁(j) ∈ {0, 1}, and the same holds for P₂.

Build the triples one block at a time, for j = 1…m:
- **Inside block j**, walk from (lo₁(j), j, lo₂(j)) to (hi₁(j), j, hi₂(j)) by unit steps:
  first raise i to hi₁(j), then raise k to hi₂(j). Every triple here has i ∈ I(j) and
  k ∈ K(j), so j is its witness.
- **From block j to block j+1**, i and k each rise by 0 or 1, which is a legal warping step
  in (i, k). If neither moves, (i, k) repeats; that duplicate is dropped from Q.

The walk starts at (1, 1, 1), because both paths start at their corners, and ends at
(n, m, p). Projected onto (i, k) with repeats removed, it is a warping path Q. Projected onto
(i, j), it visits P₁'s pairs in order, pausing while k moves; symmetrically for (j, k). This
gives properties 1–3. ∎

## Theorem

For f ∈ {log₂ richness, S, TV}, d_f is a pseudometric:

    d_f(A, A) = 0,   d_f(A, B) = d_f(B, A),   d_f(A, C) ≤ d_f(A, B) + d_f(B, C).

Distance 0 means B is A transposed after **merging repeated consecutive notes**. For example,
(C C D) and (G A) are at distance 0: tie the two C's and they are a transposition.

*Proof.*
- **Zero and symmetry.** The diagonal path gives offsets {0}. Swapping the roles of A and B
  mirrors each path and negates every offset, which changes none of these statistics.
- **Triangle.** Take optimal P₁ and P₂, and let Q come from the lemma, so Q's offsets are
  o_t = xₜ + yₜ (removing duplicate (i, k) pairs removes repeats of the same offset).
  - *Richness:* set(o) ⊆ set(x) + set(y), so |set(δ_Q)| ≤ |set(δ_P₁)| · |set(δ_P₂)| by the
    sumset bound. Take logs.
  - *S:* if o_{t+1} ≠ o_t, then x_{t+1} ≠ x_t or y_{t+1} ≠ y_t. Consecutive repeats add no
    changes, so x changes exactly S(P₁) times and y exactly S(P₂) times. Hence
    S(Q) ≤ S(P₁) + S(P₂).
  - *TV:* |o_{t+1} − o_t| ≤ |x_{t+1} − x_t| + |y_{t+1} − y_t|, and repeats add zeros. Summing
    gives TV(Q) ≤ TV(P₁) + TV(P₂).
  - Finally, d_f(A, C) ≤ f(δ_Q).
- **Distance 0.** It means there is a path with a constant offset. Along it, a (1,0) or (0,1)
  step keeps the offset only if the melody that moved repeats its pitch, so the two melodies
  agree after merging consecutive repeats. ∎

## Counterexample for entropy and modal share

Take A = (G4), B = (F4, F4) and C = (E4, F4), writing 7, 5 5 and 4 5 for pitches.
- d(A, B) = 0: the only path pairs G4 with both F4s, so the offsets are −2, −2.
- d(B, C): the best path (1,1), (1,2), (2,2) has offsets −1, 0, 0. That gives H = 0.918 and
  1 − C₁ = 1/3.
- d(A, C): the only path pairs G4 with E4 and with F4, so the offsets are −3, −2. That gives
  H = 1 and 1 − C₁ = 1/2.

So d(A, C) > d(A, B) + d(B, C) for both measures. From B, a path may *repeat* the matching note
to outvote the mismatch. A has only one note, so no path from A can reweight that way. This is
exactly the "composing re-weights notes" failure §7 feared, but it bites the
multiplicity-based statistics only.

## Caveats

- **A capped re-rhythm is not covered.** gtrsnipe's `--homograph-subdivide K` lets one note
  stand for at most K. Block j of Q pairs up to |I(j)| + |K(j)| − 1 notes, so the class of
  paths with a cap is not closed under composition, and the theorem says nothing about it.
- **The zero set is coarser than in the aligned case.** With a fixed note-for-note alignment,
  d = 0 means an exact transposition. Here it means a transposition up to repeated notes.
- **Computing it.** d_S and d_TV are shortest paths through the n × m grid. A cell's offset is
  fixed by the cell, so each step's cost ([offset changed] or |change|) depends only on the
  two cells: O(nm) time.
  - d_richness asks for the grid path using the fewest distinct offsets. That is a
    minimum-label path problem, which is NP-hard on general graphs; its complexity on this
    grid is open here, so don't claim anything about it.
  - Fixed k is easy: try each set of at most k offsets, then check whether a path exists
    through cells labelled with them. k ≤ 6 is the guitar case.
- **What this does not say.** The R03 experiment found that richness is a weak tune-family
  similarity measure under a fixed grid alignment. This result is about the *geometry* of the
  measures, not their usefulness.
