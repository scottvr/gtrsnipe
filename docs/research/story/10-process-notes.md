# 10. Process notes

*Claude's account.*

How the work actually got done, including what went wrong.

## Who did what

- **scottvr:** the ideas, the legal argument, the musical judgment, and the decisions. The
  corrections were decisive: they came from knowing guitars, the codebase's history, and
  what the argument was for. Several solver features were scottvr's: "meet in the middle",
  rhythm slop as a ratio, "ta ≈ ti ti", and the playability threshold.
- **Claude:** the code, the experiments, the checks, and the first drafts of the documents.
  Also several of the overclaims below.
- **ChatGPT:** developed the structure note's first draft with scottvr, and later reviewed the
  alignment proof, where it improved the statement and the rigour.

> ✎ **scottvr:** the ChatGPT side, in your words.

Between 2026-09-23 and 09-27 there were 14 releases, and the test suite grew from 56 tests to 611.

## Practices that worked

1. **Write the decision rule before the experiment.** The structure note said in advance
   what result would mean "richness is just a guitar statistic, stop". When R03 came back
   negative, there was nothing to argue about.
2. **Check numerically before claiming.** A short script (the triangle check, the alignment
   check, a planted wrong fret) settled more than any amount of reasoning in chat.
3. **Try to break it before release.** Separate agents reviewed each major feature with
   instructions to find real bugs. They found 9 in v0.4.0 and 22 in v0.6.0, each fixed with a
   regression test.
4. **Let the junk at the top of the results define the filters.** R04's first top pairs were
   trivial, mechanical, or look-alikes. Each became a filter, stated in the results doc.
5. **Record provenance.** The literature survey says how each source was checked. The proof
   says what came from the ChatGPT review. The story marks what it doesn't know (✎).
6. **Park, don't start** (The Dull Protocol, chapter 5).
7. **The human stays the judge** of what sounds unrelated and what's comfortable to play.
   The tools only rank.

## Overclaims, and what caught them

| the claim | whose | what corrected it |
|---|---|---|
| log(richness) is a (new) melodic distance | Claude, in passing | the prior-art pass: true, and elementary |
| a whole Hill/Rényi family of melodic metrics | the first draft | counterexamples at orders ½, 2 and ∞ |
| "only orders 0 and 1 work", said before any check | Claude | the check agreed, and the literature explains why; still, the claim came first |
| the offset profile might find tune families | the structure note (a hypothesis, with a test) | R03: it doesn't |
| under optimized alignment, entropy, S and TV might fail while richness survives | Claude (revision 1, §7) | R07: half wrong; S and TV survive too |
| "physics barely filters" shared tabs | Claude, summarizing R04 | F06: tension barely filters; comfort does |
| the tuned Bach measure was fingered by hand | Claude | scottvr: it's gtrsnipe output from tuned options |
| StegTab hides bits in redundant fingerings | the literature agent's guess | scottvr found the source: a letter cipher |
| a minimum-note-length filter was needed with P01 | Claude | scottvr: `--velocity-cutoff` was always the cruft filter |
| "vocabulary vs. switches" might be new | the structure note, revision 1 (Claude) | scottvr's question about image processing: it's label costs vs. the Potts term (revision 3) |
| "the note claims no new result"; the alignment condition is "folklore"; richness is "not useful" | Claude, the tech note's revision 3 | scottvr: an overcorrection. Claiming there's nothing new needs knowledge we don't have, just as claiming novelty does (revision 4) |

The pattern in Claude's column is mostly **summary overreach**: a true finding stated one
notch more broadly than the evidence. Two things caught these: running the check, and
scottvr knowing something the data couldn't say (how the wiki tabs were really made, the
codebase's past, how a guitar feels). Neither model was a reliable judge of its own novelty
claims. The literature search and the experiments were.

**Underclaiming is overclaiming too.** Revision 3 of the tech note swung from "possibly new"
to "nothing here is new", from "useful?" to "not useful", and from "the same mechanism as
Fréchet's proof" to "Fréchet's proof". Each was as unsupported as the claim it replaced. The
fix (revision 4) was to say what was tested and what was searched, and to stop there:
neither novelty nor its absence, and a negative result reported as a negative result.

## scottvr's account

> ✎ working with two models at once; the ADHD "what if we…" loop, and what it's like when
> the tool can keep up; what you'd do differently.
