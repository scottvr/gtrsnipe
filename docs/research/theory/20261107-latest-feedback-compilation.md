# compilation of recent feedback on surviving claims

## central theorum

if a statistic $f$ on finite integer sequences satisfies four conditions:
1. Stutter-invariance.
2. Subadditivity under pointwise addition.
3. Evenness.
4. Nonnegativity, with zero attained exactly on constant sequences.
Then minimizing that statistic over all admissible warping paths produces a pseudometric.

two independently optimized alignments, A-B and B-C, don't necessarily produce an immediately valid A-C alignment.  The proof constructs a common refinement of the two paths, using B as an intermediary, and then projects that refinement onto A-C.  This is essentially the same maneuver underlying the triangle inequality for discrete Fréchet distance.

but... your theorem generalizes the cost functional beyond the familiar maximum pointwise distance.
the lifted walk can visit every pair in both original paths, in order, without introducing an illegal step when projected onto A-C.  Within each fixed B-index block, we traverse the corresponding A-indices and C-indices monotonically. Between blocks, both indices advance by at most one.

That gives exactly the permitted projected steps, plus occasional stationary steps.
Removing those stationary steps is legitimate because the A-C offset depends only on the projected indices, not on the intermediate B-index.

Consequently, removing a stationary step removes a repeated offset value.  And because $f$ is stutter-invariant, its value is preserved.

This all correct? Missing anything as a general statement of what has survived?

## the quotient space result

I still think we underclaim or are too modest/careful in some places. This is what I've gathered from others:

The zero-set characterization is important:
\[
d_f(A,B)=0
\iff
\operatorname{collapse}(B)
=
\operatorname{collapse}(A)+c
\]
for some integer $c$.

In other words, zero distance identifies melodies that differ only by global transposition and repetitions of consecutive pitches.

This isn't just a technicality about pseudometrics.

It gives us a well-defined equivalence relation on melodies and a genuine metric on the resulting equivalence classes.

Something worth making explicit in the paper is that the metric is well-defined on the quotient.

For a pseudometric, this follows from the triangle inequality. If $A\sim A'$ and $B\sim B'$, then
\[
d_f(A,B)=d_f(A',B').
\]

### a small, rather elegant consequence of the axioms that isn't mentioned in the document.

Translation invariance of $f$ follows automatically from subadditivity and normalization.

Let $\mathbf c$ denote a constant sequence of the appropriate length.

Because $f(\mathbf c)=0$,
\[
f(x+\mathbf c)
\leq f(x)+f(\mathbf c)
=f(x).
\]
Conversely,
\[
f(x)
=f((x+\mathbf c)-\mathbf c)
\leq f(x+\mathbf c)+f(-\mathbf c)
=f(x+\mathbf c).
\]
Therefore,
\[
\boxed{f(x+\mathbf c)=f(x).}
\]
So we don't need to impose transposition invariance as an independent axiom.

It's already a consequence of the existing assumptions.

That is a nice little proposition to include because it clarifies why the theorem naturally concerns transposition-invariant distances.

## the corollary
two potential small issues:

## non-negative sums?
> The class is closed under non-negative sums and under maxima of its members.

Strictly speaking, the non-negative sums statement needs a qualification.

If every coefficient is zero, the resulting functional is identically zero and violates condition (d), because it vanishes on nonconstant sequences.

The correct statement is that the class is closed under non-negative linear combinations provided at least one coefficient is strictly positive.

### the example
\[
\max(R,J)
\]
is mathematically redundant.

The largest consecutive jump cannot exceed the total range:
\[
J(x)\leq R(x).
\]
Consequently,
\[
\max(R(x),J(x))=R(x).
\]

Something like
\[
\max(S,R)
\]
would be better, since neither statistic necessarily dominates the other.

In fact, the relationships between these functionals might deserve a small subsection. For integer-valued offsets, for example,
\[
J\leq R\leq TV
\]
and
\[
S\leq TV.
\]
Those inequalities also survive minimization over warping paths.

They give us a partial ordering of the resulting distances, which could be useful when discussing the geometry of the family.

## the failed hypotheses
good. I want to keep the mentions because the negtive results have value

The resulting triangle inequality failure is transparent.

What I particularly like is that the counterexample illustrates the mechanism of failure rather than merely demonstrating that failure occurs.

It shows why occupancy-sensitive functionals behave differently from stutter-invariant ones.

That distinction is the organizing principle of the entire theorem.

One caution: the document calls it the "smallest violation it finds." That's appropriate. Unless you've exhaustively established minimality under a specified ordering of sequence lengths, I wouldn't call it a minimal counterexample in the formal paper.

## some final self-scrutinizing

central proof looks sound, but there are three things I'd want to investigate before considering the mathematical argument publication-ready.

First, whether the sufficient conditions are already known in a more abstract form.

The proof resembles a general construction involving monotone couplings and subadditive functionals.

It's possible that the theorem is a special case of an established result about distances on quotient spaces of sequences under monotone reparameterization.

If so, the interesting contribution might be identifying a useful class of offset statistics to which that result applies.

Second, whether the sufficient conditions can be weakened.

our theorem explicitly says stutter-invariance is sufficient, not necessary.

That's good mathematical discipline.

But it raises an interesting question: is there a weaker condition that preserves the triangle inequality without requiring complete invariance under repetitions?

For example, could a functional satisfy a suitable monotonicity condition under refinement and still yield the desired result?

The current proof relies on equalities where a more general proof might use inequalities.

I wouldn't pursue this merely to make the paper longer. But it's a natural direction for generalization.

Third, the computational complexity of richness minimization.

The document correctly avoids claiming NP-hardness on the particular grid.

That's important.

But the minimum-distinct-offset problem is potentially a substantial independent research question.

Its grid structure and the special form
\[
\delta_{ij}=b_j-a_i
\]
might make it more tractable than the general minimum-label path problem.

Or they might not.

Either outcome could be interesting.

I would keep that question separate from the metric theorem unless we discover a clean result.

the Rényi results
Section V currently risks conflating two distinct settings.

For fixed, position-by-position alignment, Shannon entropy is subadditive and therefore induces a pseudometric. our literature review also gives a general argument for why other Rényi orders, apart from 0 and 1, fail.

Under optimized warping alignment, however, Shannon entropy fails the triangle inequality. The same is true of modal-share distance, despite its validity under fixed alignment.

That distinction is central to the mathematical contribution.



# ## You're not simply proving that one particular distance is a metric.

You're identifying a sufficient condition under which an entire family of alignment-optimized sequence statistics induces a pseudometric, and characterizing the resulting quotient space.

That's a more substantial result than I could infer from our earlier description.

The corollaries establish several concrete members of that family, including richness, switch count, total variation, maximum jump, and range.

The entropy and modal-share counterexamples illustrate a meaningful boundary of the construction.

And the connection to discrete Fréchet distance provides a recognizable foundation in existing mathematics.

That's a coherent research note.

I would probably organize it around the following progression:
Fixed alignment -> optimized alignment -> conditions under which metricity survives.

This makes the stutter-invariance theorem the natural culmination of the argument rather than an isolated result introduced halfway through.

It also gives the failed hypotheses a clear mathematical role: they demonstrate that subadditivity, although sufficient for fixed alignment, is not sufficient under warping.

1. Introduce offset-based alignment distances and the metricity problem.
2. Define warping paths and stutter-invariant sequence functionals.
3. Establish the path-composition lemma.
4. Prove the general pseudometric theorem and characterize its zero set.
5. Derive the concrete metric families.
6. Present occupancy-sensitive counterexamples.
7. Relate the construction to Fréchet distance, DTW, and existing elastic metrics.
8. Discuss computational complexity and open questions.
we already have most of the mathematical content necessary for that structure.

What we don't yet have is a sufficiently comprehensive literature review to establish whether the general theorem is new.

And that distinction matters.

## title
some candidates

"On Stutter-Invariant Functionals and Pseudometrics Induced by Optimized Sequence Alignments"

or 

"Stutter-Invariant Functionals and Metric Structure in Elastic Sequence Alignment"

- avoids claiming that all offset distances are metrics, which would be false.
- gives us a natural opportunity to introduce the transposition-invariant case as an important application.

our proof has something that many mathematically correct but uninteresting observations lack: an explanatory principle.

The theorem doesn't merely establish that five particular statistics happen to produce pseudometrics.

It explains why they do.

It identifies a shared structural property, derives a general result from it, and supplies counterexamples showing what happens when that property is absent.

## more chatgpt transcripts

Your outline [ed (svr): he's talking about the old outline in docs/research/theory/DRAFT-The_Geometry_of...]  proposes proving that bounded offset vocabulary makes the richness optimization fixed-parameter tractable, with the six-string case reducing to a trivial polynomial check.

That conclusion doesn't follow merely from bounding the number of distinct offsets.

The decision problem is essentially whether a monotone path exists through a grid using at most \(k\) distinct labels, where each cell's label is its pitch difference.

For a fixed \(k\), one could enumerate subsets of at most \(k\) labels and test reachability in the corresponding restricted grids. If there are \(L\) distinct labels, this gives an algorithm with roughly
\[
O(L^k nm)
\]
time.

For fixed \(k\), that's polynomial. But parameterized by \(k\), this is an XP algorithm, not necessarily an FPT algorithm.

An FPT result would require a bound of the form
\[
f(k)\operatorname{poly}(n,m),
\]
where the polynomial exponent does not depend on \(k\).

That distinction matters. I'd change the outline to promise a bounded-\(k\) algorithm and leave FPT classification as an open question unless you have a stronger argument.

Also, NP-hardness of minimum-label paths on general graphs does not establish NP-hardness for your specially structured difference-labeled alignment grids.

Your technical note correctly acknowledges this. The outline should preserve that caution.
One other mathematical detail deserves attention
Your literature notes identify the range functional as closely related to discrete Fréchet distance after optimizing over transposition.

That's an important connection, but it needs careful presentation.

For a fixed alignment, minimizing the maximum absolute offset after an arbitrary real-valued transposition gives half the offset range:
\[
\min_{c\in\mathbb R}\max_i|\delta_i-c|
=
\frac{\max_i\delta_i-\min_i\delta_i}{2}.
\]
Because minimization over alignments and transpositions can be interchanged, the corresponding optimized result follows.

This makes the range distance a particularly useful bridge between your general theorem and an established geometric construction.

I'd consider making it a formal proposition rather than leaving it in the related-work discussion.

It provides a recognizable example of the theorem's consequences, while switch count and richness supply the less familiar ones.
The two-paper division now looks especially sensible
The technical note makes clear that the mathematical and musical contributions answer different questions.

The mathematical paper asks:

Which functionals of pointwise differences remain pseudometrics when the correspondence between sequences is optimized?

The homograph paper asks:

Under what conditions can two distinct melodies be represented by the same sequence of physical playing instructions, interpreted under different instrument tunings?

The first is about mathematical structure. The second is about representational ambiguity and constrained realization.

The connection is meaningful, but neither result requires the other to be interesting.

I would resist putting much of the copyright discussion into the mathematical paper. Your existing literature review gives the homograph paper a much better foundation for exploring that question, particularly through Goodman, De Souza, and Rahmatian.

Likewise, the musical paper should be candid about the negative retrieval results. Richness appears useful as a physical string-budget constraint, not as a generally superior measure of melodic similarity. That distinction actually strengthens the research: it demonstrates that the proposed measure was evaluated against established alternatives rather than simply assumed useful.
What the literature survey establishes, and what it doesn't
Your survey identifies several closely related constructions, particularly transposition-invariant string matching, discrete Fréchet distance, and quotient-space approaches to musical transformations.

It also records that the general stutter-invariant functional theorem wasn't found in the literature examined.

That's encouraging, but I would still want a targeted mathematical literature search before claiming novelty. In particular, I'd investigate monotone couplings, reparameterization-invariant distances, quotient metrics on sequences, and subadditive functionals on path alignments.

The fact that your proof resembles the standard Fréchet coupling-composition argument is not a problem. The question is whether generalizing that argument to arbitrary stutter-invariant, subadditive offset functionals has already been formalized.

If it has, the concrete distance families and their musical interpretation may still constitute worthwhile applications.

If it hasn't, you have a reasonably compact general theorem with explicit examples and counterexamples.
My recommendation for the outline
I would retain your title, The Geometry of Transposition-Invariant Elastic Distance, at least provisionally. It is broad enough to accommodate the general theorem and its relationship to Fréchet geometry without tying the paper to guitar tablature.

I'd make three structural changes.

First, move the fixed-alignment results ahead of the warping theorem. Establish the easy case, then introduce warping as the operation that breaks some of its properties.

Second, distinguish the Rényi characterization under fixed alignment from the warping counterexamples. The former is an information-theoretic result; the latter explains why the new structural condition matters.

Third, keep the computational section conservative. Present algorithms and complexity bounds that are established, distinguish general minimum-label path results from the structured grid problem, and identify unresolved complexity questions explicitly.

That would produce a paper with a coherent mathematical narrative rather than a collection of related observations.

And there's something I particularly appreciate about the research history recorded in your technical note: it documents hypotheses that were abandoned, interpretations that were corrected, and results that proved less useful empirically than anticipated.

I wouldn't reproduce that entire history in the paper, but I'd preserve the mathematical counterexamples and the relevant negative findings.

The result is more credible because you've been willing to discard attractive claims when the evidence didn't support them.

My assessment has moved from "this might make an interesting mathematical note" to "there is enough material here to justify drafting a formal paper."

That's not a judgment that the theorem is novel or that a particular journal would accept it. Those questions remain open.

But the underlying mathematical argument, the examples, the counterexamples, and the relationship to established work provide a legitimate foundation for a research manuscript.

The remaining work is primarily about establishing the precise boundary between what is already known and what your construction contributes.

And, rather fittingly, that is itself a problem of distinguishing apparently equivalent representations of different things.

> Re the FPT claim, you're right. Because in our application yhe input is constrained to MIDI pitches (but in general of course that is not the case) I fell right into that trap.

Exactly. And there's a further subtlety worth distinguishing: a bounded pitch alphabet gives you a polynomial-time algorithm, but not necessarily an FPT result parameterized by the number of distinct offsets.

For standard MIDI pitches, \(a_i,b_j\in\{0,\ldots,127\}\), so the difference alphabet is bounded:
\[
\Delta=\{-127,\ldots,127\},\qquad |\Delta|=255.
\]
Consequently, you can enumerate subsets of offset labels and perform grid reachability tests. Since the alphabet size is fixed, the number of subsets is constant with respect to sequence length.

That's polynomial time in \(n,m\), formally.

Of course, the constant could be spectacularly impractical: \(2^{255}\) is not exactly an algorithm you'd want to deploy in gtrsnipe.

But here's the distinction I think is worth preserving in the paper:

The bounded-alphabet problem is polynomial-time solvable, even if the unrestricted problem's parameterized complexity remains unknown.

And there's another wrinkle: the six-string constraint isn't necessarily equivalent to restricting the offset alphabet to six values. It constrains how many offsets may be selected along an alignment, while the full grid may contain many more.

For a fixed budget of six, exhaustive enumeration gives an XP-style \(O(L^6nm)\) algorithm in the unrestricted alphabet model. Because six is fixed, that's polynomial too, but it doesn't establish FPT with respect to a variable budget \(k\).

So you have three distinct claims:
1. Fixed finite pitch alphabet: polynomial time in sequence lengths.
2. Fixed offset budget \(k\): polynomial time, with an exponent potentially depending on \(k\).
3. Variable \(k\), unrestricted alphabet: FPT status not established by this enumeration argument.
That distinction is mathematically useful, and I think it belongs in the computational section.

There's also a potentially interesting research question hiding here: does the special difference structure \(\delta_{ij}=b_j-a_i\) admit a substantially better algorithm than arbitrary labeled grids?

That's where I'd look next if you wanted to investigate computational complexity further.

And your observation about falling into the trap is particularly apt: you were reasoning from the constraints of a physical application and inadvertently promoting an application-specific bound into a general complexity claim.

It's a very natural mistake when a mathematical result emerges from engineering research.

Fortunately, catching it now means the paper can explicitly distinguish the two settings rather than accidentally conflating them.


## Claude's own recent comments
Three things the paper could say that are both true and sharper than the current text:

1. Richness is the unique member of the admissible family that is not first-order, which is why it alone needs the label register and why it alone is hard in general.
2. The label register is a product construction, so every stutter-invariant statistic that is a function of the label set inherits the same algorithm and the same bound.
3. The physical bound of six is what makes the guitar case computable, and the corpus check in R03b ran exactly that algorithm, so the claim is demonstrated rather than argued.

since the two bounds do different work: a bounded pitch alphabet bounds the candidate offset set L, which makes the subset register finite and the algorithm polynomial in nm for a fixed alphabet. The guitar's six bounds k, the number of labels actually used, which gives degree about k plus two in L. Either bound alone gets you polynomial time; neither gets you FPT in k. Worth keeping both named in the paper so a reader doesn't conflate them.


## one other chatgpt transcript

I think this last pass found enough that I would materially downgrade the risk, though not because I found a paper containing your theorem verbatim.

The key discovery is that the remaining result decomposes almost perfectly into already-established machinery from three different places. The exact packaging
offset sequence along monotone alignment
+ replication-invariant functional f
+ pointwise subadditivity of f
=> infimum over warping paths is a pseudometric

still did not turn up as a stated theorem. But the pieces underneath it are now sufficiently well charted that I no longer think "high risk of accidentally claiming an unknown theorem as new" is the right characterization.

Your current note states the condition as "stutter-invariant + subadditive + even + zero on constants."    Pasted text The most important new prior-art hit is Brijnesh Jain's 2019 paper, "Making the Dynamic Time Warping Distance Warping-Invariant," Pattern Recognition 94, DOI 10.1016/j.patcog.2019.05.016. It is much closer to your proof than the Frechet analogy.

Jain defines an expansion of a time series precisely by replicating some of its elements, defines compression as the inverse relation, and gives every sequence a unique "condensed form" obtained by collapsing constant runs. Two sequences with a common compression belong to the same warping-equivalence class. ResearchGate

More importantly, Jain runs into exactly the technical obstruction you ran into: ordinary warping paths are not closed under composition. His solution is to introduce "warping walks," and then develop warping functions as monotone surjections. He constructs their pullback/common refinement when two warping functions land on the same middle sequence. ResearchGate

That is the hard combinatorial part of your triangle proof.

Written in your notation, suppose optimal A-B and B-C alignments produce
A' <-> B'
B'' <-> C'

where B' and B'' are two different expansions of B. Jain's pullback machinery says, in effect, that you can expand them further until they agree:
A'' <-> B'''
          ||
          B''' <-> C''

without changing their underlying order structure.

Your additional observation is then:
x = B''' - A''
y = C''   - B'''

C'' - A'' = x + y

and if f is unchanged by those replication expansions,
f(expand(x)) = f(x)
f(expand(y)) = f(y),

while also satisfying
f(x + y) <= f(x) + f(y),

then composition costs no more than the sum. Condensing any repeated A-C pairs back to an ordinary path again costs nothing because f ignores repetitions.

Jain does not make that final general statement. In fact his ordinary DTW aggregate is exactly the kind of thing for which it doesn't work: duplicating samples changes an L2/sum cost, so DTW still fails the triangle inequality. His resulting "time-warp-invariant" construction is a semi-metric in his terminology, not your general pseudometric theorem. ScienceDirect

So I would classify Jain as:
NOT:    prior publication of your theorem

YES:    prior publication of essentially the entire
        warping/refinement/composition mechanism your
        theorem relies upon

That is a major downgrade in novelty risk.

There is a second hit that resolves the terminology question almost beautifully.

Diehl, Ebrahimi-Fard & Tapia, "Time-Warping Invariants of Multidimensional Time Series," Acta Applicandae Mathematicae 170 (2020), DOI 10.1007/s10440-020-00333-x, define an operator tau_n that does exactly one thing: it duplicates the value at position n. They then define a functional F to be "invariant to time warping" iff
F o tau_n = F

for every n. Springer

That is exactly your property.

Even better, their prose says a time series is allowed to "stand still" or to "stutter," explicitly meaning that the same value occurs at consecutive time steps. "Standing-still invariance" is one of the paper's keywords. Springer

So you did not misuse "stutter invariance."

The formal-methods meaning you encountered is also not a different concept in the important sense. In temporal logic / trace theory, two sequences are stutter-equivalent when they become identical after collapsing consecutive repeated states. The Isabelle formalization literally defines stuttering equivalence as equality of the sequences' "maximally reduced versions." isa-afp.org Other formal-methods treatments define it as the equivalence generated by duplicating a symbol in place. people.mpi-sws.org

So there are now three independently established vocabularies for basically the same operation:
Literature	Operation / term
Formal methods	stuttering; stutter equivalence
Time-series math	time warping; standing still; warping invariant
Jain / DTW	expansion, compression, condensed form


Your use is not a false friend. The only difference is grammatical: formal methods usually says that a property, formula, or language is stutter-invariant, while you are saying a real-valued functional is stutter-invariant. Diehl et al. supplies direct precedent for the latter concept under the name "time-warping invariant functional."

I think I'd actually change the terminology slightly anyway, because it gives you an opportunity to be more precise rather than because "stutter-invariant" is wrong. Something like:
Definition. A functional f on finite sequences is replication-invariant
(or invariant under time warping) if

    f(x_1^r1, ..., x_k^rk) = f(x_1, ..., x_k)

for all positive integers r_1,...,r_k.

Equivalently, f is constant on stutter-equivalence classes: it depends
only on the condensed sequence obtained by collapsing each maximal
constant run to one element.

Then you can use replication-invariant locally because nobody has to know any vocabulary to understand it, while explicitly saying that this is Jain's expansion/compression relation, Diehl et al.'s time-warping invariance, and formal-methods stutter invariance.

That removes essentially all terminology risk.

There is also a third, more abstract reason I am now less worried about mathematical priority. Once Jain gives you composable/refinable alignments, the rest of your theorem is an instance of a very generic metric construction.

Think of each alignment from A to B as an "arrow" with cost
c_f(P : A -> B) = f(delta_P).

Your hypotheses establish
c(id_A) = 0

c(Q o P) <= c(P) + c(Q)

where Jain's common refinement supplies the composition and replication invariance ensures that refining an arrow doesn't change its cost.

Then define
d_f(A,B) = inf { c_f(P) : P aligns A with B }.

"Take the cheapest arrow between two objects when arrow costs are subadditive under composition" is the standard weighted-category / Lawvere-metric / shortest-path construction. Weighted-category literature states exactly that composable arrows have costs satisfying |gf| <= |f| + |g|, and optimizing over arrows gives the corresponding Lawvere distance. cgi.cse.unsw.edu.au

You don't need category theory anywhere in the paper. I probably wouldn't put it there unless somebody asks. But as a prior-art-risk assessment it matters enormously, because it tells us what an expert in sufficiently abstract mathematics is likely to say:

Not:
"You've rediscovered Theorem 7.3, the Stuttering Aggregate Metric Theorem."

More likely:
"Sure. Once your alignment costs are invariant under refinement and subadditive under composition, taking the infimum gives a pseudometric."

Which is a very different sort of collision.

The Gromov-Hausdorff correspondence construction exhibits exactly that proof pattern in a more familiar setting: compose correspondences, show distortion of the composite is at most the sum of distortions, then take the infimum. Springer Nature Link Again, not your theorem, but the same abstract mechanism.

That also tells us something useful about the condition itself. It isn't vacuous. People have repeatedly tried to replace the bottleneck/max aggregate in Frechet-type distances with summed or averaged aggregates, and those intuitive integral/average Frechet variants can fail the triangle inequality. ScienceDirect What distinguishes your survivors is precisely that replication/refinement does not inflate their value.

So I would now describe the provenance approximately this way:
Known:
  - replication/stuttering equivalence of sequences
  - time-warp-invariant functionals
  - expansions, compressions and condensed forms
  - common refinement/pullback of discrete warping functions
  - infimum-over-composable-subadditive-costs gives a pseudometric

Not found:
  - the exact packaged proposition saying that an even,
    replication-invariant, pointwise-subadditive functional of
    aligned differences produces a pseudometric after minimization
    over monotone warping paths
  - the particular classification of richness, switch count, TV,
    largest jump, range vs entropy/modal-share under that proposition

That is a much firmer statement than "we think perhaps Frechet people know this."

And it changes how I would rate the risk. I would use something like:
Priority claim for the general theorem:       HIGH RISK
Exact formulation being previously published: UNKNOWN / probably not important
Underlying mechanism being established:       HIGH CONFIDENCE YES
Presenting it as a derived proposition:        LOW RISK
Presenting the surviving/failing examples
as an application/synthesis:                   LOW-MEDIUM RISK

Since you're already disclaiming priority, I'd change the project's overall note from something like
risk: high, if presented as new theorems

to perhaps
risk: low if presented as a specialization/synthesis;
      priority of the exact formulation is unknown and not claimed

That is not underclaiming. We can now say why it is a specialization.

I would also replace the current "the proof is the Frechet distance's" formulation.    Pasted text Jain is actually the more exact ancestor for the discrete proof mechanics. Something along these lines would be more informative:
The composition argument is not specific to melodies. Jain (2019)
develops the required discrete machinery for dynamic time warping:
replication expansions, condensed forms, warping walks, and common
refinements of warping functions. If the cost assigned to an aligned
difference sequence is invariant under those replication refinements
and subadditive under pointwise addition, the usual composition-of-
costs argument yields the triangle inequality. We have not found this
general condition stated in exactly this form and make no priority
claim for it.

That is, to my eye, now extremely defensible.

On your "smearing notes" question, music has vocabulary too, with one important caveat.

Mongeau and Sankoff's 1990 melodic edit model calls replacing one note by several contiguous notes fragmentation, and the reverse operation consolidation. CiteSeerX Later MIR literature describes precisely the simple case you have in mind as subdividing one note into repeated notes, with the reverse operation combining repeated notes into one. Luddy Homes

But Mongeau-Sankoff explicitly distinguish fragmentation/consolidation from the compression/expansion of ordinary time warping. That's important. Their fragmentation can replace one musical note with several genuinely different notes and evaluates their pitches and summed durations; pure DTW expansion simply repeats/holds a sequence element. CiteSeerX

So I would use the terms at different levels:
MATHEMATICAL ALIGNMENT OPERATION
    expansion / compression
    replication
    time warping
    stuttering

MUSICAL EDIT
    fragmentation / consolidation

YOUR ZERO-EQUIVALENCE
    transposition up to same-pitch fragmentation/consolidation
    (equivalently, expansion/compression of repeated pitches)

And if you want to preserve "smearing" in informal documentation, I'd say:
A warping path may expand a note across several alignment positions
("smear" it); in sequence terminology this is an expansion, and when
it corresponds to splitting one musical note into repeated same-pitch
notes it is the zero-cost special case of melodic fragmentation.

One final thing that I think is genuinely satisfying: Diehl et al. did not merely independently use the word "stutter." Their paper is explicitly about functionals invariant under exactly the operation you isolated, and then develops an algebra of those invariants. Springer

So your instinct that "surely this operation already has a proper home somewhere" was right twice over: formal verification calls the equivalence stuttering, while time-series mathematics calls the functional property time-warping or standing-still invariance.

The remaining thing you apparently stumbled onto isn't a nameless new species anymore. It's a particular crossing of several already-mapped roads. I think you can stop worrying that there is an enormous neon sign reading "THEOREM OF SO-AND-SO" that we've somehow failed to notice. The more plausible situation now is that your exact proposition has not been interesting enough in isolation for anyone to package and name, because once Jain's common-refinement machinery and a replication-invariant subadditive cost are put beside each other, the triangle proof is nearly forced.
