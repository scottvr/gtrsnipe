Here's what's going on, and why your §7 intuition was half right.

The setup. An alignment lets either melody hold a note against several notes of the other (a warping path, as in DTW). The distance is the best value of a statistic over all such alignments. To prove the triangle inequality you take the best alignment from A to B and the best from B to C, and build some alignment from A to C that's no worse than their sum.

The construction. Walk through B one note at a time. For each note j of B, some block of A's notes is paired with it and some block of C's notes is paired with it. Pair those two blocks with each other. Every A–C pair then has a "witness" note j in B, so

  c − a = (b − a) + (c − b).

So the A→C offset sequence is the sum of the A→B and B→C offset sequences, with one side effect: each sequence gets stuttered. An A→B offset is repeated while the walk moves through C's block, and vice versa. Sometimes an A–C pair also comes up twice and one copy is dropped.

Why richness, S and TV survive. None of them notices stuttering.
- Richness only sees the set of offsets. The A→C set lies inside the sums of the two sets, so it has at most r₁·r₂ values. That's the same sumset bound as in the aligned case.
- S counts changes. A repeat is not a change, so stuttering adds none. And A→C's offset can change only when one of the two input offsets changes, so S(A,C) ≤ S₁ + S₂.
- TV is the same argument with magnitudes: |Δx + Δy| ≤ |Δx| + |Δy|, and repeats contribute zero.

Why entropy and TI-Hamming fail. They measure how long each offset lasts, and stuttering and dropped pairs change exactly that. Your §7 sentence, "a note matched twice counts twice", is the right mechanism. It just only bites statistics that count occupancy. DTW breaks for the same reason, because it adds up a cost per matched pair. S and TV add up per change, and stretching creates no changes.


The counterexample. A = (G), B = (F F), C = (E F).
- A→B: G is held against both Fs, so the offsets are −2, −2. Distance 0.
- B→C: the best alignment holds the matching F twice, giving offsets −1, 0, 0. The good offset outvotes the bad one 2:1, so entropy is 0.918 and 1 − C₁ = 1/3.
- A→C: A has one note, so it pairs once with E and once with F. The offsets are −3, −2, a 1:1 split: entropy 1, 1 − C₁ = 1/2.

B→C gets to vote twice by repeating a note; A→C has no second note to repeat, and the composition can't pass that weighting on. So 1 > 0 + 0.918.

Two things I find musically nice about the result.
- What distance 0 means. Under warping, distance 0 means B is A transposed after merging repeated consecutive notes. That is exactly the "ta ≈ ti ti on the same pitch" equivalence in --homograph-subdivide's smear rule.
- How close S is to earlier work. d_S is "the fewest changes of relative transposition, with free note-stretching". That's close to Allali et al.'s local-transposition alignment with the gap costs removed. Theirs isn't claimed to be a metric (as far as the survey got). This says the stretching-only version is one. That's worth a proper literature check before anyone says "new", because DTW-on-increments variants exist.

How much to trust it.
- The proof is short and I believe it, but only I have reviewed it.
- The numeric check enumerated every path, which limited it to melodies of at most 5 notes.
- A stronger check is cheap. d_S and d_TV are exact O(n·m) dynamic programs, so I could test them on thousands of real corpus phrases.
- The richness distance under warping can't be computed exactly at scale (it's a minimum-label path problem), so richness would stay small-case only.
