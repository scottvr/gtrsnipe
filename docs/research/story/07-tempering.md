# 7. Tempering

*Claude's account.*

R04 let the solver choose which notes share a string. Two later findings asked what happens
when that choice isn't free: first, when a real tab has already made it; then, when a
guitarist has to play the result.

## Real tabs, as written (R05)

A real tab has already chosen its fingering. It can be retuned into another song only if
every note it puts on one string moves by the *same* interval. The test used the tabs from
gtrsnipe's own wiki, not third-party ones: the Bach Cello Suite No. 1 Prelude, and six successive transcriptions of
Albéniz's *Asturias*. The first Asturias was an "unplayable abomination"; the sixth came from
options tuned until the output matched how scottvr plays it.

- **As written is about 10,000× stricter than a free fit.**
- **Short passages are still ambiguous.** Hundreds of unrelated-sounding 8-note passages
  (1,512 for Asturias v6) fit a real fingering exactly.
- **Long passages are not.** At 24 and 32 notes, nothing unrelated-sounding fits either
  piece. What still fits is look-alike figuration.
- **The fingering decides, not the melody alone.** One Bach measure, fingered with the
  string-switch penalty removed (the wiki's second step), gives every string a single pitch.
  So it "matches" 8% of every candidate passage, and every match is trivial: the tab says only
  which string to pluck. The same measure with scottvr's final options (two pitches on one
  string) matches 85× less.

So the strong form of the claim, "any tab could be any song", holds for short passages, and
for a tab stripped of its tuning. It doesn't hold for a long, fully specified tab.
[`RESULTS-R05`](../results/RESULTS-R05-aswritten.md).

A correction belongs here. Claude's first write-up called that tuned Bach measure a
*hand* fingering, because scottvr had described its output as "exactly how I would have
transcribed it manually". scottvr pointed out that it, and Asturias v6, were gtrsnipe output
too, from options tuned by ear, not tabs written by hand. The labels and the file name were
fixed on 2026-09-27.

## Comfort (F06)

R04 said the solver places 93–100% of the sampled folk pairs on a real guitar. Claude
summarized that as "physics barely filters". That was true of **string tension** and nothing
else.

scottvr's idea: score each shared tab by how *playable* it is, using the mapper's own
scoring. Compare it with the tab gtrsnipe would write for song A alone, and let the user set
a limit. That became `--homograph-max-discomfort` (v0.6.6): the number of mapper points per
note a shared tab costs over A's own best tab.

On 50 sampled folk pairs:

| max discomfort (points per note) | pairs with a tab |
|---|---|
| no limit | 49 (median about 100–120, usually reaching fret 24) |
| 50 (about a 17-fret leap per note) | 19 |
| 20 | 4 |
| 5 | 0 |

A's own tab scores about −2 to −7 per note. The shared tabs exist and can be fingered, but
they're awkward: pinning each note to a string by its interval forces big leaps. **String
tension barely filters, but comfort does.** R04's summary was corrected to say so, and the
"Playability" section records the counts. (They're lower bounds, because the solver offers
each interval class only a few strings; that's in the parking lot.)

## What survived

The existence result is untouched: shared tabs exist, they're valid, and they can be
fingered. What changed is the practical claim. A homograph worth playing needs a hand-picked
pair and a comfort limit, and a real, long tab with its tuning stated nearly pins its music
down. The paper is better for it: the argument now rests on what the tab *omits* (the
tuning), not on any tab being every song.

## scottvr's account

> ✎ seeing the numbers shrink; where the playability-threshold idea came from; and how the
> tempered claim changes the paper.
