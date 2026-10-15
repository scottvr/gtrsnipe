# The story

How a joke about guitar chords turned into a MIDI-to-tab converter, and the converter into a
small research programme about what a guitar tab actually means, told in chapters. The chapters
stand alone, so they can be reordered, linked separately, or cut up into posts.

| # | chapter | covers |
|---|---|---|
| 1 | [Prologue: a tab tool, and a new collaborator](01-prologue.md) | the joke gtrsnipe began as; the tab tool before September 2026; Claude joins; v0.2.2–v0.5.0 |
| 2 | [The reductio](02-the-reductio.md) | the copyright argument, and `--solve-tuning` |
| 3 | [One tab, two songs](03-homographs.md) | the eligibility theorem, the solver, string physics (v0.6.0) |
| 4 | [The metric detour](04-the-metric-detour.md) | a casual claim, a draft full of "novel" results, and what survived |
| 5 | [The Dull Protocol](05-the-dull-protocol.md) | taming the tangents: the backlog, the parking lot, a correctness sweep |
| 6 | [The research track](06-the-research-track.md) | corpora, the tune-family test, the alignment proof, homographs in the wild |
| 7 | [Tempering](07-tempering.md) | real tabs as written, and comfort as the real filter |
| 8 | [Side discoveries](08-side-discoveries.md) | a free tab checker, StegTab, and other things found along the way |
| 9 | [Where it landed](09-where-it-landed.md) | what holds, what doesn't, and fodder for posts and a paper |
| 10 | [Process notes](10-process-notes.md) | working with two LLMs; the overclaims caught, and how |
| A | [Appendix A: the first README](A-README.V0.2.2~131.md) | gtrsnipe's README as first committed (`fd583c0`, 2024-12-27): the guitar computer and its journal |

## Timeline

| date | release | what happened |
|---|---|---|
| 2024-12-02 | | "FizzBuzz in Powerchords" on Hacker News; scottvr's reply and fork the next day |
| 2024-12-27 | | gtrsnipe's first commits: a joke guitar computer, with MIDI-to-tab and a fretboard mapper as by-products |
| 2025-07-25 | | "complete refactor into a useful tool": the guitar computer goes, the by-products stay; the mapper's tunables arrive one by one over the next week |
| 2026-09-05 | | scottvr retells the origin on Hacker News, having "completely forgotten about" it |
| 2026-09-12 | | Claude's first session: planning v0.3.0 |
| 2026-09-23 | v0.2.2, v0.3.0 | the two clones reconciled; a CPU-only core; the Viterbi mapper |
| 2026-09-24 | v0.4.0 | the player, chord charts, audio |
| 2026-09-25 | v0.5.0 | unified I/O, profiles, custom tunings, **`--solve-tuning`** |
| 2026-09-26 | v0.6.0 | **`--homograph`** and string physics; the structure note; the Dull Protocol |
| 2026-09-26 | v0.6.1–v0.6.4 | the correctness sweep; research tools, literature survey, R03, R07, R04 |
| 2026-09-27 | v0.6.5 | R05: real fingerings, as written (gtrsnipe's wiki tabs) |
| 2026-09-27 | v0.6.6–v0.6.9 | playability (F06), `--analyze`, note lengths, instruments |
| 2026-09-28 | v0.6.10 | the StegTab source found; these docs organized and audited |
| 2026-09-29 | v0.6.11 | chord names over the tab; the tech note's revisions 3 and 4: vocabulary vs. switches parallels computer vision's label costs; an overcorrection to "nothing is new", then calibrated |

## About these chapters

- **One account, two authors.** Claude drafted every chapter first. scottvr then revised
  them inline, and from there both of us edit freely. The text says "we", and names one of
  us where it matters who did or thought something. (The first plan was two accounts per
  chapter, Claude's and then scottvr's. It made for more than anyone would read.)
- **Who wrote what.** Claude's drafts alone, before any of scottvr's revisions, are these
  files as of commit `988e359`. After that the text is joint.
- **Who answers for it.** scottvr reads and approves all of it before it is published. What
  it says is his responsibility.
- **Sources:** the git history, the CHANGELOG, the design and research docs, Claude's session
  notes, and scottvr's memory. Chapters 2–10 are first-hand. The prologue before September
  2026 is reconstructed from commit messages, the first README (Appendix A) and two Hacker
  News threads, and quotes them word for word (Hacker News dates are UTC).
- **✎ markers** flag gaps that only scottvr can fill: the reasons behind decisions, the
  ChatGPT sessions, and what came before. They come out as they are filled.
- **Numbers** are copied from the results docs. If a chapter and a results doc disagree, the
  results doc wins.
- **Not yet public:** these chapters stay private until scottvr has revised and reviewed all
  of them.
