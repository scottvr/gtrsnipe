# 5. The Dull Protocol

*Claude's account.*

## The tangents

By the afternoon of 2026-09-26, the list of "what if we…" ideas was growing faster than
anything was getting finished:
- homographs in real song collections;
- a tune-family experiment;
- better ABC parsing;
- chord names over the tab;
- open-position chord voicings;
- a playability-based `--analyze`;
- corpora to download;
- a literature search;
- bugs spotted along the way.

Every one was interesting, and each tended to start the moment it came up. scottvr describes
this as ADHD scope creep, and enjoys it. The risk was a dozen half-built things.

## The protocol

scottvr named the fix **The Dull Protocol**, and it's written at the top of
[`../../dev/BACKLOG.md`](../../dev/BACKLOG.md):
- **New ideas go in the parking lot:** one or two lines each, captured, not started.
- **One step of the backlog at a time.** Finish it, release it, then triage.
- **Triage** moves every parking-lot entry into the backlog, or declines it, and empties the
  lot.
- **Releases are patch-first**, so shipping is cheap and frequent.

It worked because it didn't forbid the tangents; it gave them somewhere to land. Over the next
two days the parking lot filled and emptied twice, and 9 releases shipped. New ideas still
arrive mid-task (a 12-string "ludicrous mode", learned scoring weights, optional notes), and
they go into the lot in a minute and wait.

> ✎ **scottvr:** why "Dull".

## Step 0 and step 1: decisions, then correctness

The backlog opened with six decisions, all taken in one sitting. For example: fix a tab bug even
though it changes the bytes of old tabs; close a stale GitHub issue with a thank-you; archive
the v0.3.0-era planning docs.

Step 1 was a correctness sweep (v0.6.1). Most of the bugs had surfaced while building
homographs:
- **The ABC parser ignored key signatures**, accidentals within a bar, and ties, and read chord
  symbols as notes. The rewrite was checked against music21 on all 1,034 Nottingham tunes:
  94% match note for note, and the rest are music21's own quirks. This mattered for more than
  ABC: the folk corpora the research needed are ABC and kern.
- **Hammer-ons and pull-offs** were written one column late, so a chord with one hammered note
  decoded as a two-note arpeggio.
- **RIFF-wrapped MIDI files** (259 of them in the Lakh corpus) came back as empty songs, with no
  error.
- **An explicit `--tuning STANDARD`** couldn't override a tab's own header.
- **`--num-strings 7` silently dropped every note below E2**, found while fixing the previous bug.

With the tools trustworthy, the research could start.

## scottvr's account

> ✎ what the tangents felt like from the inside, and whether the protocol changed how the
> work felt.
