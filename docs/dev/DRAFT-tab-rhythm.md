# Rhythm in gtrsnipe's tabs: the dash-count layout

**A draft for scottvr to mark up (2026-10-07). Nothing here is built.** Background, the three
earlier layouts and the measurements are in [`PARKING-LOT.md`](PARKING-LOT.md), "Tabs that
keep time".

## The idea in one sentence

**The dashes after a note say how long it lasts**: until the next note, or the bar line.

To the eye it reads the way hand-written tabs do: longer notes get more room, though not in
proportion. To gtrsnipe it is exact, because the *number* of dashes names the length.

## The table

One dash is the tune's shortest note (the *base*). Each doubling adds two dashes; a dot adds
one.

| length, in base notes | 1 | 1½ | 2 | 3 | 4 | 6 | 8 | 12 | 16 |
|---|---|---|---|---|---|---|---|---|---|
| dashes | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
| with a sixteenth as the base | s | s. | e | e. | q | q. | h | h. | w |

## The rules

1. **A bar is one measure.** It is written `|`, one padding dash, its notes, `|`.
2. **Each onset** is its fret number, then its dashes on every string. The notes of a chord
   start in the same column and share one length: the time to the next onset.
3. **Dashes are counted from the end of the fret number**, so a two-digit fret makes a bar
   wider but never changes what it says.
4. **A rest at the start of a bar** is its dashes after the padding dash: one dash before the
   first note means no rest; more means a rest of that many dashes, less one.
5. **A rest after a note** isn't written. A note's dashes run to the next onset; whether it
   rings or is damped for that time is something a tab doesn't say (`--sustain` decides, as
   now).
6. **A bar with no notes** is a silent measure, however wide. gtrsnipe writes `|----|`.
7. **The legend** is a header line. It names the layout and the base, and it is what tells a
   reader to count dashes:

   ```
   // Rhythm: dash-count, base 1/16   (s=1 s.=2 e=3 e.=4 q=5 q.=6 h=7 h.=8 w=9)
   ```

   A tab without this line is read as today: each bar a measure, notes placed in proportion
   to their columns. So older gtrsnipe tabs, tabs from elsewhere, and a tab whose comments
   were left out all still read, approximately.
8. **The check.** A bar's rest and note lengths must add up to a measure (from `// Time:`).
   A bar that doesn't, because someone edited it by hand or it holds a length the table
   lacks, is read in proportion like any other tab, and the reader can say which bars those
   were.

## Examples

A sixteenth-note run, then a whole note (base: a sixteenth). The second bar is the case
scottvr described: one fret number with enough room to say "this is not another sixteenth",
and nowhere near in proportion.

```
e|-0-1-3-5-7-5-3-1-0-1-3-5-7-5-3-1-|-0---------|
```

*Ode to Joy*, bars 1 to 4 (base: an eighth, the tune's shortest note; `e=1 q=3 q.=4 h=5`).
Bar 4 is a dotted quarter, an eighth and a half:

```
B|-5---5---6---8---|-8---6---5---3---|-1---1---3---5---|-5----3-3-----|
```

*Battle Hymn of the Republic*, bars 1 and 2 (base: a sixteenth; `s=1 e.=4 h=7`), with one-
and two-digit frets:

```
e|----------------------8----10-|-12----12-12----10-8-------|
B|-8----8-8----6-5----8---------|---------------------------|
```

A quarter rest and three quarter notes; a silent bar; two half-note chords (base: a quarter;
`q=1 h=3`):

```
e|--0-3-8-|----|---------|
B|--------|----|---------|
G|--------|----|-0---0---|
D|--------|----|-2---0---|
A|--------|----|-3---2---|
E|--------|----|-----3---|
```

## Width and rows

- A note costs its digits plus its dashes, so a bar's width depends on how many notes it has
  and not on how long its silences are. With one-digit frets a bar is never wider than two
  columns per base note, plus one: 33 columns for a 4/4 bar in sixteenths, 17 in eighths.
  With two-digit frets, 49 and 25.
- On 300 folk tunes this layout came to 1.3 times today's total width, with 98% of bars
  exactly decodable (today: 33%).
- Rows work as now: whole bars only, as many as fit `--max-line-width`, and a bar wider than
  the limit gets a row to itself.

## What it doesn't do

- **Two voices with different rhythms.** An onset has one length.
- **Lengths outside the table**: five or seven base notes, a tie across a bar line, triplets
  mixed with even notes. About 2% of bars on the test tunes. Such a bar is written with the
  nearest lengths, fails the check, and is read approximately.
- **Other tools.** A reader that takes columns as time will get the order and the bars right
  and the lengths squeezed. A structured file (see the parking lot: `.gp` for the tab
  editors) is the place for exact rhythm that other programs must read.

## Options

Each extra is a flag with a default, as with everything else:

- the layout: `--tab-rhythm dashes` (this), or `loose` (today's);
- note-length letters over the staff (`w h q e s`, a dot for dotted), on top of either layout;
- leaving comment lines out (`--omit-comments`).

## Questions for scottvr

1. **The default.** Should dash-count become the default at once (every tab changes its
   look, so a minor version), or be opt-in for a release first? Claude would make it opt-in
   for one release and look at real tabs before switching.
2. **The base.** The tune's shortest note, as above (compact, but two tunes can have
   different bases), or always a sixteenth (one table to learn, wider tabs: 1.6 times today's
   width on the test tunes, against 1.3)?
3. **The row width.** The default is 40 columns. At 40, a sixteenth-note bar is alone on
   its row. Raise the default to 80?
4. **The legend's wording.** Is the line in rule 7 what you would want to read at the top of
   a tab?
5. **Lengths outside the table.** Nearest length and a failed check, as above, or mark such a
   bar visibly?
6. **A pickup bar.** A first bar shorter than a measure fails the check. Treat a short first
   bar as a pickup that ends at the bar line?
7. **The letters.** When they are on: lowercase or capitals, and how should a rest look?
