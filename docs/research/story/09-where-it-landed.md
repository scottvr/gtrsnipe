# 9. Where it landed

*Claude's account.*

## The claims

The full table, with evidence for each row, is in [`../README.md`](../README.md) ("Where the
claims stand"). In short:

- **Holds:** one ordinary tab can carry two unrelated melodies. There's an exact criterion for
  when, and a solver that finds such tabs, verifies them, and keeps them physically
  plausible. For short passages this is common in real folk song.
- **Tempered:** those tabs are rarely comfortable, and a real, long tab with its tuning stated
  nearly pins its music down. The ambiguity lives in the tuning, which tabs state in one line
  or not at all.
- **Deflated:** the offset statistics' metric properties are elementary. Richness is not a
  useful melodic similarity.
- **Placed, not deflated:** the condition for distances to survive optimized alignment uses
  the Fréchet distance's proof mechanism, and wasn't found stated in general form; "vocabulary
  vs. switches" parallels computer vision's label cost against its Potts term. The tech note
  (revision 4) makes no claim of a new mathematical result, and says which combinations we
  didn't find documented: the homograph criterion, its decoder reading, and the general
  alignment condition.

## Fodder: posts

Each of these is roughly one chapter, or one results doc, with a demo:

| working title | the hook | sources |
|---|---|---|
| A tab is not a song | `--solve-tuning` and one tab that plays *Old MacDonald* and *Twinkle, Twinkle* | chapters 2–3, `examples/homograph/` |
| How often do two songs share a tab? | a third of short folk phrase pairs; the charts | chapter 6, R04 |
| The real filter is your hand | tension says yes, comfort says no | chapter 7, F06 |
| Your tab says more than you think | real fingerings pin the music down | chapter 7, R05 |
| My metric wasn't new, and that's fine | a casual claim, a draft of "novel" results, named prior art, Fréchet, label costs, and not overcorrecting | chapters 4 and 6 |
| A free tab checker | "wrong-wrong" tabs, detected by the homograph machinery | chapter 8 |
| Thirty knobs, tuned by hand | 22 mapper options today (closer to 30 at their peak), each added for one transcription, and how to learn them | chapter 8 |
| Two LLMs and a guitarist | the collaboration itself | chapter 10 |

## Fodder: papers

A sketch, for scottvr to overrule:

1. **The copyright paper** (scottvr's follow-up to *"Part of Your World"*). The construction
   gives it a concrete, pre-digital instance of an encoding whose decoding key is a free
   parameter. The tab is the notation; the tuning is the key.
   - The tempered results sharpen the argument rather than weaken it. It's not that every
     tab is every song. It's that the thing people compare (the tab) underdetermines the
     thing that matters (the sound) exactly to the extent the key is left out.
   - Hooks from the survey: Rahmatian (2024) on similarity of notation without similarity of
     the listening experience; Goodman's semantic disjointness for notations; the
     idea/expression line.
2. **A music-informatics paper** on the construction itself: the eligibility theorem, the
   solver with string physics and playability, R04's rates in real song collections, and
   R05's as-written test. It would also report R03's negative result, since it saves the
   next person from trying richness as a similarity. The survey's suggested wording for
   related work is in [`../literature/LITERATURE-offsets.md`](../literature/LITERATURE-offsets.md).
3. **An optional expository note or post**, not a research paper: the dictionary that connects
   the tab problem to music-retrieval measures and image-regularization terms, and which of
   those terms survive optimized alignment, and why. Framed as a synthesis, it makes no claim
   of a new mathematical result, and says which combinations weren't found documented.

> ✎ **scottvr:** what you actually plan to write, and where.

## Still open

- **R13:** the citation pass (scottvr, in progress).
- **R10–R12:** re-rhythm in the scan, the full Lakh corpus, and richness under its own
  optimal warping.
- **The comfort counts are lower bounds:** offer every compatible string to each interval
  class (parking lot).
- **Third-party tabs as written:** the natural next input for R05, kept local for copyright
  reasons.

## scottvr's account

> ✎ where you think it landed, and what surprised you.
