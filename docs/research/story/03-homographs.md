# 3. One tab, two songs

*Claude's account.*

## The one-line fact

On a single string, fret f sounds `open + f`. Play the same tab in two tunings, A and B, and
every note on that string moves by the same amount: `b − a = open_B − open_A`. The interval
between the two songs is a property of the **string**, not the note.

So two songs, aligned note for note, can share a tab exactly when their note pairs split into
at most six groups, each with one constant interval (plus two practical conditions: one note
at a time per string, and every fret on the neck). That's the eligibility theorem in
[`../../app/DESIGN-homograph.md`](../../app/DESIGN-homograph.md) §1. The proof is two lines in
each direction, and it turns the question "can this tab be that song?" into arithmetic.

The number of distinct intervals got a name. It was *rank* at first, then **richness**, to
avoid clashing with matrix rank. `--solve-tuning` is the case where every fret is 0.

## Building it (v0.6.0)

`gtrsnipe --homograph A B` checks, in order:
1. whether the songs align;
2. their richness;
3. whether a tab exists with any tunings at all (*free*);
4. whether one exists where A stays an ordinary standard-tuned tab (*anchored*).

It names the first obstacle it hits. When a tab exists, it's written with every song's
tuning in its header and verified by decoding it back into each song. The first worked
example: an ordinary standard-tuned tab of *Old MacDonald* which, with four strings retuned
by a few semitones and no new strings, plays *Twinkle, Twinkle*.

Three of the solver's ideas came from scottvr's side of the conversation:
- **"Meet in the middle."** Instead of keeping A in standard tuning and bending B around it,
  retune *both* songs from one strung guitar, each string moving partway. This often needs no
  new strings when anchored mode does. It became `--homograph-mode middle`.
- **Rhythm slop as a ratio.** Real songs rarely share a rhythm exactly, so each gap between
  notes may stretch by a factor.
- **"Ta" ≈ "ti ti".** A quarter note in one song can stand for two eighths on the same pitch
  in the other (`--homograph-subdivide`): the alphabet song's "L-M-N-O" against Twinkle's
  two Ds. On that pair the report honestly says *richness 1: the songs are identical*.

## Keeping it physical

A retuning that snaps a string is no demonstration. So gtrsnipe learned string physics
([`strings.py`](../../../gtrsnipe/guitar/strings.py)):
- tension from gauge, scale and pitch, matching D'Addario's published tensions within 1–2%;
- a slack limit;
- restringing suggestions.

One fact fell out that most guitarists know by feel but rarely see derived: a plain steel
string's breaking pitch depends on the scale length, **not the gauge**. The stress is ρ(2Lf)²,
and the area cancels. At 25.5″ that pitch is about A4, which is why the high E is the string
that snaps and why a heavier one doesn't help.

## The review

Before release, a set of agents tried to break the feature and confirmed 22 real problems:
- middle mode wasn't always a superset of anchored;
- the first wound-string model was wrong;
- several re-rhythm edge cases;
- rendering bugs.

All were fixed, each with a regression test. v0.6.0 shipped on 2026-09-26.

## scottvr's account

> ✎ the moment the idea went from "all open strings" to "an ordinary tab"; what you hoped
> the first shared tab would show; and how "meet in the middle" and "ta ≈ ti ti" came up.
