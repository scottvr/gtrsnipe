# 6. The research track

*Claude's account.*

Step 2 of the backlog (2026-09-26 to 27, v0.6.2–v0.6.5) turned the construction into
questions with answers. Each tool shipped as a patch release, and each result got its own
document in [`../results/`](../results/).

## Corpora and tools (R01, R02)

`gtrsnipe-research corpus` reads five collections into one cached format:
- **Essen** folk songs (kern);
- **the Meertens Tune Collections** (kern, grouped into tune families by expert annotators;
  scottvr filled in the download form);
- **Nottingham** (ABC, the reason the parser had to be right);
- **POP909**'s melody tracks;
- **Lakh**, with a melody track picked by name or by skyline.

The kern reader was written natively, so it could keep phrase marks. It matches music21 on
8,469 of 8,473 Essen files; the other 4 have malformed ties.

`gtrsnipe-research profile` computes every statistic from chapter 4 for any two melodies.

## What's already known (R06)

A Claude research agent searched the literature and recorded how it checked each source
(full text, abstract, or unverified): [`../literature/LITERATURE-offsets.md`](../literature/LITERATURE-offsets.md).
- **The offset set** is defined in Mäkinen, Navarro & Ukkonen (2005, §6), but only its most
  common value is used. Counting it appears unused.
- **The homograph's ingredients are old:** tunings that change what notation means
  (scordatura, the lute's *accords nouveaux*) and Allen & Goudeseune's (2011) per-string
  retuning vectors, which are the construction's dual and must be cited. Nothing found builds
  one tab for two given, unrelated melodies.
- **The legal literature** treats tabs as copies. Rahmatian (2024) states the principle the
  construction instantiates: "similarity of notation without similarity of the listening
  experience points away from infringement."

## Tune families (R03): the decision rule fires

The experiment the note had specified in advance: on the Meertens collections, does richness
find variants of the same tune better than established measures? **No.** Transposition-invariant
Hamming distance, which scores only the single most common offset, wins. Richness trails it by
0.13–0.21 mean average precision, and adding richness, entropy and reuse to the baselines gains
at most 0.006.

The reason is instructive. Variants of a tune keep one transposition and depart from it here
and there, so a measure that counts *every* departing offset is dominated by noise. That's
the ecologists' old warning about order-0 diversity (a rare species counts as much as a common
one), met in melodies.

So richness is a guitar statistic. The homograph work was unaffected, since it needs richness
as a string budget, not as a similarity. [`RESULTS-R03`](../results/RESULTS-R03-families.md).

## The alignment proof (R07): half a guess wrong, and a principle

The note's §7 had guessed (Claude's guess, in revision 1) that when the alignment between two
melodies is *optimized* rather than fixed, log-richness might stay a distance while entropy,
the switch count and total variation might not. **Half of that was wrong.** The truth has a
clean shape:

> A statistic of the offset sequence that ignores consecutive repeats and is subadditive
> stays a pseudometric when minimized over warping paths.

Richness, the switch count and total variation ignore repeats, and they survive. Entropy and
the modal share count how long each offset lasts, and they fail. The counterexample is tiny:
one melody of a single note (G), and two of two notes each (F F, and E F). [`../theory/PROOF-alignment.md`](../theory/PROOF-alignment.md) has the proof and
a brute-force check.

scottvr then reviewed the proof with ChatGPT. That review was useful:
- it separated two objects the first draft had blurred;
- it tightened the statement of when the distance is zero;
- it suggested stating the result as a general principle rather than a list of cases.

The revision then placed the result: its composition step is the classical proof that the
*discrete Fréchet distance* is a metric. Fréchet's distance (the largest pointwise gap) is the
prototype of this class. So the argument is known, and the general condition is the kind of
generalization an expert would call immediate: best treated as folklore, not a new result.

## Homographs in the wild (R04)

`gtrsnipe-research scan` slides windows over every melody, buckets them by rhythm, and asks
which pairs from *different* songs fit six strings. The first results were dominated by junk,
and each kind of junk became a filter:
- **Trivial pairs.** The intro arpeggio of *You Light Up My Life* against a figure from *For
  Whom the Bell Tolls* fit, but only because each is a six-note cell repeated. Any two such
  patterns fit.
- **Mechanical figures:** scales, broken chords, and anything with a short period.
- **Look-alikes.** Two descending scales in different modes differ in most notes by the
  transposition measure, yet sound alike. A contour-agreement cutoff removes them.

After the filters, among folk phrase pairs from different tunes with the same rhythm, about a
third of 8-note pairs fit six strings *and* sound unrelated; 8% at 12 notes and 3% at 16.
The full solver places 93–100% of them on a real guitar, with song A in standard tuning.
Pop melodies looked easier still, but mostly because they circle a few pitches.
[`RESULTS-R04`](../results/RESULTS-R04-scan.md), with charts.

Those numbers made the argument look strong. The next two findings tempered it.

## scottvr's account

> ✎ the Meertens download and the corpora; reading the R03 verdict; the ChatGPT review of
> the proof; and the first homographs found in real songs.
