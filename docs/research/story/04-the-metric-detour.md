# 4. The metric detour

*Claude's account.*

## A casual claim

While building the homograph solver, Claude mentioned in passing that log(richness) behaves
like a *distance* between melodies. It's zero for a melody and its transposition, symmetric,
and it obeys the triangle inequality, because richness multiplies at worst:
r(A,C) ≤ r(A,B) · r(B,C). The implication was that the solver's by-product might be a new
way to measure how alike two melodies are.

That was true, and it was more exciting than it deserved to be.

## A draft full of possibly-new results

scottvr took the idea and developed it into a technical note, *Coupled Transposition Structure
in Aligned Melodies*. It covered:
- the offset sequence δ = B − A as the object carrying everything about two aligned melodies;
- several statistics of it (richness, entropy, the modal share, the switch count);
- a family of distances across diversity orders (the Hill/Rényi family);
- homograph corollaries.

In the draft, many of these were candidates for new results.

> ✎ **scottvr:** how the draft was written with ChatGPT, and which of its "novel" results
> ChatGPT was most enthusiastic about.

## Revision 1: checking before claiming

Claude revised the draft on two fronts.

**A numeric check** ([`triangle_check.py`](../theory/triangle_check.py)). The "family of
metrics" failed. Hill orders 0 (richness) and 1 (entropy) give distances. Orders ½, 2 and ∞
don't, with explicit counterexamples: a 16-note one for 2 and ∞, and a 10-note one for ½.
Claude had already said in chat that "only orders 0 and 1 work" *before* running the check.
The check agreed, but the claim came before the evidence, and that belongs in this story too.
(The survey later found the classical reason: Rényi entropy is subadditive only at orders 0
and 1, per Aczél, Forte & Ng, 1974.)

**A prior-art pass.** Nearly everything had a name already:
- the modal share's distance is transposition-invariant Hamming distance (Mäkinen, Navarro &
  Ukkonen, 2005);
- the switch count and total variation are Hamming and L1 distances between interval
  sequences;
- richness and its relatives are Hill numbers (Hill 1973, Jost 2006), the ecologists'
  diversity indices;
- "modulo transposition" is the T in Callender, Quinn & Tymoczko's OPTIC (2008).

The metric facts survived, but they were elementary.

What was left as possibly new was narrow: the contrast between **how many** distinct
transposition offsets a pair of melodies needs (its *vocabulary*) and **how often** it switches
between them. Existing transposition-aware alignment charges every switch. A guitar charges
only for vocabulary: going back to a string you've already retuned is free. The revision wrote
down an experiment to test whether that contrast is musically useful, *with its decision rule
in advance*: if it doesn't beat the established baselines, richness is "a guitar statistic,
not a similarity measure". Stop there.

scottvr then corrected the revision in turn:
- Richness is a **lower bound** on the strings a pair needs, exact only in an idealized
  model; fret range and simultaneous notes can demand more.
- "Richness ≤ 6" is a *budget*, not an equivalence relation: it isn't transitive.

## How it came out

- **The literature survey (R06)** found that the offset *set* is in Mäkinen, Navarro &
  Ukkonen (2005), used only for its most common value. Counting it as a measure appears
  unused, but the risk of calling the metric facts new theorems is high.
- **The experiment (R03)** said no: richness is a weak similarity measure, and the
  plain transposition-invariant Hamming distance beats it.
- **The one genuinely general result** came later, from a question the note left open
  (chapter 6).

## scottvr's account

> ✎ what it was like to have one model spark the idea and another inflate it, and when it
> became clear which parts were folklore.
