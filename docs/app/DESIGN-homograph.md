# Tab homographs — one tab, a different song per tuning

`--homograph A B [C …]` finds a single tablature that plays song A in one tuning,
song B in another (and C in a third…). It generalizes `--solve-tuning` (a melody
behind an all-open tab) from "a tab that carries nothing" to "an ordinary,
fretted, fingerable tab that carries two songs at once" (fingerable, not
necessarily comfortable: see "Playability" in §3). It's the executable form of
the (tab, tuning-key) reductio: a fixed text whose musical identity is decided
entirely by an external key.

- **Code:** `gtrsnipe/guitar/homograph.py` (solver), `gtrsnipe/guitar/strings.py`
  (string physics), `gtrsnipe/research/` (the `gtrsnipe-research` corpus tools,
  including `scan` and `aswritten`, §5).
- **Tests:** `tests/unit/test_homograph.py`, `tests/unit/test_strings.py`,
  `tests/unit/test_research*.py`.
- **Worked examples:** [`examples/homograph/`](../../examples/homograph/).
- **The research** (theory, literature, experiments): [`../research/README.md`](../research/README.md).

## 1. When can two songs share a tab? (the eligibility theorem)

A tab assigns every note a (string *s*, fret *f*); a tuning gives each string an
open pitch *o(s)*; the sounding pitch is *o(s) + f*.

Align A and B note for note (§4), giving pairs *(aᵢ, bᵢ)*. If note *i* sits on
string *s* at fret *f*, then *aᵢ = o_A(s) + f* and *bᵢ = o_B(s) + f*, so

> **bᵢ − aᵢ = o_B(s) − o_A(s)** — the interval between the songs is a property of
> the *string*, not of the note.

**Theorem.** A and B share a tab on an *N*-string, *F*-fret instrument **iff** their
aligned notes can be split into ≤ *N* classes ("strings") such that, within each
class:

1. the difference *d = b − a* is constant;
2. no two notes sound at the same time (a string plays one note at a time);
3. A's pitches span ≤ *F* semitones (every fret fits on the neck).

*Proof.* (⇒) the strings of any shared tab are such a split, by the identity above.
(⇐) given a split, set *o_A(s)* = the class's lowest A pitch, *o_B(s) = o_A(s) + d*,
*f = a − o_A(s)* ∈ [0, F]; decoding in either tuning returns the right song. ∎

### Consequences

- **Richness.** Let *r(A,B)* = the number of distinct intervals *bᵢ − aᵢ*. Every class
  holds one interval, so *N ≥ r* is necessary; for a monophonic line whose
  classes each span ≤ F semitones (typical on a 24-fret neck) it is also sufficient. **Neither the number of notes nor the
  overall pitch range matters.** A 500-note pair is eligible on a guitar if it
  differs by ≤ 6 distinct intervals; a 7-note pair isn't if it differs by 7.
- **r = 1** means B is A transposed — a capo, not a homograph. The report says so.
- **Transposition-invariant.** Transposing B adds a constant to every *d*, so *r*
  (and eligibility) depends only on the melodic *shapes*, never the keys. The free
  transposition is spent on keeping the retune physically sane (§3).
- **F = 0 is the old all-open solver**: each class then holds a single pitch pair,
  so strings = distinct *(a, b)* pairs.
- **K songs.** One tab, K tunings: the class key becomes the difference *vector*
  *(b − a, c − a, …)*. Same theorem, *r* = distinct vectors.
- **log r is a pseudometric** on rhythm-aligned melodies. The intervals A→C are
  sums of intervals A→B and B→C, so *r(A,C) ≤ r(A,B)·r(B,C)*; hence
  *ρ = log r* satisfies the triangle inequality, is symmetric, and is 0 iff the
  songs are transpositions. Read *log₂ r* as the bits per note the tab's string
  choices must carry to tell the songs apart; the tunings carry the rest. More in
  the [structure note](../research/theory/coupled_transposition_structure.md) and
  [PROOF-alignment](../research/theory/PROOF-alignment.md), which shows it stays a
  pseudometric under optimized alignment. As a *similarity*, though, the one test run gave a
  negative result: in [R03](../research/results/RESULTS-R03-families.md),
  transposition-invariant Hamming was best among the tested measures.
- **The tell.** A constructed homograph often plays one pitch on different strings
  for no ergonomic reason (Old MacDonald's three opening C4s land on D10, D10, G5
  because the third one must also be Twinkle's leap). That's a forensic signature
  of a *constructed* homograph; a *natural* one needn't show it.

## 2. The eligibility check, level by level

`analyze()` / `gtrsnipe --homograph` reports each level and stops at the first
failure with the reason:

| level | question | failure message names |
|---|---|---|
| alignment | same onset skeleton (§4)? | the first onset where counts/chord sizes/timing diverge |
| richness | how many interval classes? | (always reported; > N means impossible) |
| free | can the classes be packed onto ≤ `--max-strings` strings (chords, fret span)? | strings needed |
| anchored | on the real instrument, with A's tuning fixed (an *ordinary* tab of A)? | the smallest group of classes needing more strings than can reach them (a Hall's-theorem certificate) |
| middle | on the real instrument, with every song's tuning a retune of it? | same |
| as written | (A read from a .tab) does A's *own* fingering retune into B? | the first string that would have to carry two intervals |

The **anchored** and **middle** searches are exact over which strings each interval
class owns (every inclusion-minimal choice, plus at most one redundant string for
playability), then the fretboard mapper's Viterbi objective fingers the leaders.
Every solution is independently verified by decoding in each tuning; the tests
also re-parse the rendered ASCII text.

## 3. Physical plausibility: string physics

A retune that would snap a string (or flop it) is no demo. `strings.py` models
real strings:

- **Tension** `T[lb] = UW·(2·L·f)²/386.4` (the formula string makers publish).
  Plain steel matches D'Addario EXL110 within 1%; nickel round-wound = 0.83 × solid
  steel of the same gauge, within 2%.
- **Plain steel breaks at a pitch set by scale length alone.** UW = ρA, so the
  stress T/A = ρ(2Lf)² — *independent of gauge*. At 25.5″ (music wire, UTS ≈ 2.7 GPa)
  that's ≈ A4: a high E at E4 sits at 53% of breaking stress, F♯4 67%, G4 75%,
  G♯4 84%, A4 94%. A heavier string doesn't help; that's why the high E is the one
  that snaps, and why no steel string (plain has the least stress per pitch)
  can be tuned there at this scale.
- **Wound strings** load only their core (the wrap adds mass): core stress is
  plain stress × *m* (total/core mass), and *m* depends on core sizes makers don't
  publish (≈2–3 for a wound G, 4–6 for a low E). So wound strings are judged by
  **tension**, with only a conservative ceiling from the thinnest plausible wrap
  (*m* ≥ 2). (A first cut used one fixed core fraction for every wound string;
  that made each one break at ≈G3 regardless of gauge and flagged every acoustic
  set's wound G. The review caught it.)
- **Down never snaps** but below ~55% of normal tension (≈ −5 semitones) a
  string flops.

Status per string per song, relative to the string's normal tension: `ok` ·
`slack` (< 55%) · `tight` (> 145%, or a plain string ≥ 70% of breaking stress) ·
`breaks` (≥ 2× tension, a bridge/neck hazard, or at the breaking stress) ·
`impossible` (no steel string holds that pitch at this scale). For slack/tight/breaks the report suggests a catalog gauge that holds the
pitch at the original string's tension.

**Retune cost** (what the solver minimizes): semitones moved (tightening × 1.5 —
down never snaps) + 10 per string that needs a different gauge; impossible = ∞.
**Default strings**: the conventional set only for the tuning it is designed for
(STANDARD 10-46, SEVEN_STRING_STANDARD 10-59, BARITONE_B 13-62 @27″,
BASS_STANDARD 45-105 @34″). Any other tuning (drop, open, custom) gets a set
designed for it at ~17 lb per string (~42 lb bass), so "normal tension" is
physical. A 10-46 set in DROP_C would make the dropped C2 the low string's
"normal", and then E2 would read as "too tight". Scale: a conventional set keeps
its own, so SEVEN_STRING_STANDARD's 10-59 set stays at 25.5″. A designed set gets
34″ for a `BASS_` tuning, or one whose lowest string is G1 or below *and* whose
top string is D3 or below; 27″ for a `BARITONE_` tuning, or one whose lowest
string is B1 or below (most 7- and 8-string tunings, such as SEVEN_STRING_DROP_A);
else 25.5″. It is shortened (to 25.5″, then 24.75″) if the top string couldn't
hold its own pitch.
`--scale-length` and `--string-gauges` override. Gauges are listed low string first; a
thin→thick set such as `10 13 17 26w 36w 46w` is flipped, except for a re-entrant tuning
(such as Nashville), which is read as written. `w` = wound, `p` = plain; unsuffixed gauges
above .020 count as wound. The same physics drives `--show-tuning` and the tension warnings
for custom tunings (F04).

### Modes and transposition

- **anchored** (default): A keeps the instrument's tuning, so the tab is an
  ordinary tab of A; the other songs are retunes.
- **middle**: every song's tuning is a retune of the same strung guitar; each
  string may move partway for each song ("meet in the middle"), keeping tensions
  balanced. Often needs no re-stringing when anchored does.
- **free**: no instrument at all (the pure math).

Transposing a whole song moves every string equally — one global knob per song.
B's is always optimized (`--homograph-transpose`). A's (`--homograph-transpose-a`)
matters only through which strings can reach which notes, so it is moved only when
its own key fails or needs re-stringing. Middle mode's per-string offsets are the
stronger, per-string version of the same idea.

### Playability: discomfort (F06)

A shared tab is a restriction of A's fingering: each note must sit on a string of its
interval class, which is often far from where a guitarist would play it. Each anchored or
middle solution is scored against the tab gtrsnipe writes for song A alone, in the same
tuning and key:

    discomfort = (score of A's best unrestricted tab - score of the shared tab) / notes

It is measured in the mapper's own points (see `MapperConfig`). It is never negative,
since the pinned search is a restriction of the free one, and it is 0 when the homograph
costs no comfort. With default weights, most of it is **hand movement** (3 points per fret
shifted between consecutive notes) plus **high-fret penalties** (5 per fret above the 12th,
more on the low strings). So a discomfort of 30 is roughly an extra 10-fret leap per note.
For reference, song A's own best tab typically scores −2 to −7 per note.

The report prints each solution's discomfort and fret range. `--homograph-max-discomfort
POINTS` rejects placements over the limit, and the solver then fingers up to 16× the usual 64
placements (1,024) looking for one within it. That's slower, but opt-in.
`gtrsnipe-research scan` takes `--max-discomfort` and `--max-fret` too.

**What it showed.** On 50 random different-sounding eligible folk pairs from R04
([`RESULTS-R04-scan.md`](../research/results/RESULTS-R04-scan.md), "Playability"), the anchored solver found a tab for 49. But the
median discomfort was about 100–120 points per note, with the top fret usually 24. With a limit,
the anchored solver found this many:

| max discomfort | fingering 256 placements | fingering 1,024 (the default with a limit) |
|---|---|---|
| 50 | 8 | 19 |
| 20 | 4 | 4 |
| 5 | 0 | 0 |

So moderate limits are partly search-limited, while strict ones reflect real scarcity.
String tension barely filters shared tabs, but *comfort* does.

Middle mode found fewer than anchored under a limit (6 vs 19 at 50). Its larger pool of
placements pushes the anchored ones past the budget, so under a limit it is no longer
guaranteed to be a superset.

**A known limit.** An interval class may use only the strings its placement assigned it,
plus one spare (`EXTRA_STRINGS`). A string whose tuning would happen to fit another class
too, e.g. every string when B is a plain transposition, isn't offered. So discomfort is an
upper bound on what the best placement could achieve. Offering every compatible string to
each class would lower it.

## 4. Alignment and re-rhythming

A tab has one onset sequence, so the songs must share one: every tab onset sounds
the same number of notes in each song. Tabs carry little rhythm, so this is
tolerant:

- `--homograph-rhythm strict` (default): onsets identical, or the same rhythm at
  another note value (all onsets proportional).
- `--homograph-rhythm RATIO` (e.g. `1.5`, `2`): after a global tempo scale, each
  gap between onsets may differ by up to that factor. A per-gap *ratio* is used,
  not a coarser grid: snapping to a grid merges/splits onsets and lets small
  differences accumulate into drift, whereas a tab reader infers rhythm locally
  from spacing — which is what the ratio models.
- `--homograph-rhythm sequence`: pitch order only.
- `--homograph-subdivide K` (two songs): one note may stand for up to K notes of the
  other — "ta" ≈ "ti ti" — found by dynamic programming. Where the covered notes
  repeat one pitch they're **smeared** into one held note (legato); otherwise the
  single note is **re-struck**. Song A is kept intact wherever possible (so the
  tab stays A's). Cost order: 1:1 < same-pitch smear < re-strike; a same-pitch
  split adds no interval class, so it costs almost nothing in richness.

Every edit is listed in the report and in the tab header (`// Re-rhythmed:`).
With `--homograph-octaves`, individual notes of B may also be displaced by
octaves (an arrangement liberty that folds intervals mod 12); the octave kept for
each class minimizes retune + notes displaced, and the count is reported.

**Chords.** Within a chord, which voice of B answers which voice of A is free (the
tab only fixes strings). Pairing is greedy: fewest new classes / simultaneous-class
collisions, tie-broken toward voice order. It's exact for melodies and a heuristic
for chords (a pairing search could only ever *lower* the richness it reports).

## 5. Limits and next steps

**Done: the searches in the wild** (v0.6.4–v0.6.5, `gtrsnipe-research`).

- **R04, `gtrsnipe-research scan`:** pairs of passages from different songs,
  bucketed by rhythm (the phrases marked in the Essen and Meertens folk
  collections; fixed-length windows of Lakh pop melodies), then sampled through the
  solver. Among same-rhythm folk phrase pairs from different tunes, the share that
  fits six strings and sounds unrelated is about a third at 8 notes, 8% at 12 and
  3% at 16. String tension rarely rules a pair out; comfort does (§3,
  "Playability"). See [`RESULTS-R04-scan.md`](../research/results/RESULTS-R04-scan.md).
- **R05, `gtrsnipe-research aswritten`:** real fingerings as written, tested on
  gtrsnipe's own wiki tabs (the six Asturias versions and Bach's Cello Suite No. 1
  Prelude), not on third-party tabs. As written is about 10,000× stricter than a
  free fit, and past 16 notes nothing unrelated-sounding fits either piece's
  fingering. See [`RESULTS-R05-aswritten.md`](../research/results/RESULTS-R05-aswritten.md).

**Open** (IDs in [`BACKLOG.md`](../dev/BACKLOG.md)):

- Alignment + subdivision is pairwise (K = 2); K ≥ 3 songs need a 1:1 skeleton (R08).
- Chord-voice pairing is greedy (§4, "Chords"); an exact pairing search could only
  lower the richness (R08).
- Middle mode gives a string an offset only if the whole interval class fits on it,
  so a class too wide for one retuned string is split across strings only at
  offset 0, through the anchored placements that middle includes (R08).
- The anchored and middle searches enumerate ≤ 20,000 string assignments
  (`ENUM_CAP`, R08). The report notes truncation; it was never hit on 6 strings.
- A class may use only its assigned strings plus one spare (`EXTRA_STRINGS`, §3),
  so discomfort is an upper bound. Offering every compatible string is in the
  parking lot ([`PARKING-LOT.md`](../dev/PARKING-LOT.md)), not yet the backlog.
- `scan` and `aswritten` compare only identical or proportional rhythms, with no
  re-rhythming (R10).
- Third-party tabs as written, kept local for copyright reasons (R14).
