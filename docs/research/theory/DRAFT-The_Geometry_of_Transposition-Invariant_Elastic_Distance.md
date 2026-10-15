## Outline: The Geometry of Transposition-Invariant Elastic Distance## I. Introduction

* The Problem Space: Introduce time-series matching under temporal deformation (warping) and translation (transposition).
* The MIR Application (The Narrative Hook): Explain the mechanics of a fretted stringed instrument interface. Define guitar tablature as a time-series matrix of mechanical coordinates, and the string tuning as a transformation vector.
* The Collision Phenomenon: Briefly state the empirical discovery that motivated this paper: a single mechanical coordinate matrix can map onto two completely distinct, unrelated musical expressions (melodies) under two different tuning vectors.
* The Core Mathematical Objective: To prove why the similarity metrics that can detect this specific relationship form a true pseudometric space, and to establish the general sufficient condition (The Stutter-Invariance Principle) for preserving the triangle inequality under dynamic time warping.

## II. Related Work & Boundaries

* Occupancy vs. Structure: Review existing alignment distances. Contrast Dynamic Time Warping (DTW), which sums pointwise costs and is sensitive to note-stretching (violating the triangle inequality), with the Discrete Fréchet Distance, which takes a maximum cost and preserves metricity.
* Neighboring MIR Metrics: Cite Mäkinen, Navarro & Ukkonen (2005). Acknowledge that while they isolated the set of aligned transpositions, they only utilized its mode. Explain how your approach instead leverages the vocabulary (richness) and structural variation of these offsets.

## III. Formal Notation & Setup

* The Sequences: Define melodies $A, B, C$ as sequences of integer pitches.
* The Warping Path: Formally define the coupling path $P$ from $(1,1)$ to $(n,m)$ with permitted unit steps $(1,0), (0,1), (1,1)$.
* The Offset Sequence: Define $\delta_P = (b_j - a_i)$ along the path $P$.
* The Distance Functional: Define the minimized metric $d_f(A, B) = \min_{P} f(\delta_P)$.
* Stutter-Invariance Defined: Introduce the formal definition of run collapse (invariance under run-length expansion).

## IV. The Core Proofs

* Lemma: Composition of Warping Paths Through a Middle Sequence
* Construct the lifted walk $\tilde{Q}$ of index triples $(i_t, j_t, k_t)$ witnessing paths $P_1$ and $P_2$.
   * Prove that deleting duplicate $(0,0)$ steps yields a legally valid warping path $Q$ from $A$ to $C$.
   * Show that the offset sequence $\tilde{o} = x + y$ is a deterministic stuttering of $\delta_Q$, rendering deduplication completely harmless to the final functional.
* Theorem: The Stutter-Invariance Principle
* Prove that if a statistic $f$ satisfies stutter-invariance, subadditivity, evenness, and normalization, then $d_f$ is a guaranteed pseudometric on the quotient space of melodies modulo global transposition and consecutive note splitting/merging.

## V. Characterization of Admissible Information-Theoretic Orders

* The Rényi Order Constraints: Group your statistics into Hill numbers / Rényi entropy orders.
* Why Order 0 (Richness) and Order 1 (Shannon Entropy) Behave Differently:
* Show how log-richness, switch counts ($S$), and Total Variation ($TV$) naturally satisfy the subadditivity bounds.
   * Walk through the explicit counterexample ($G4 \rightarrow F4, F4 \rightarrow E4, F4$) to demonstrate how Shannon entropy and modal share fail the triangle inequality under warping due to path-reweighting.
* General Impossibility Proof for Other Orders: Leverage the classical characterization of Aczél, Forte & Ng (1974) and Linden et al. (2013) to prove that no other Rényi orders ($\alpha \notin \{0, 1\}$) can universally satisfy the triangle inequality in this environment.

## VI. Computational Complexity and Bounded Constraints

* Algorithmic Landscapes: Classify the computing times for the various admissible distances.
* Show that $d_S, d_{TV},$ and $d_J$ are standard shortest/bottleneck paths solvable in $O(nm)$ polynomial time.
   * Address the NP-hardness of $d_{richness}$ as a minimum-label path problem on general graphs.
* The Guitar Bounded Case: Prove that for a physical interface where the vocabulary of transpositions is bounded by a fixed number of strings ($k \le 6$), the search space becomes fixed-parameter tractable (FPT), resolving to a trivial polynomial check.

## VII. Conclusion & Musical Implications

* Summarize the geometric properties established.
* Conclude by returning to the narrative frame: the math proves that instrument tablature functions structurally as an elastic, multi-interpretable coordinate instruction system rather than a fixed representation of a singular expressive work.
