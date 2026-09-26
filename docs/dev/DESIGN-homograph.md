# Tab homographs — one tab, a different song per tuning

`--homograph A B [C …]` finds a single tablature that plays song A in one tuning,
song B in another (and C in a third…). It generalizes `--solve-tuning` (a melody
behind an all-open tab) from "a tab that carries nothing" to "an ordinary,
fretted, playable tab that carries two songs at once". It's the executable form of
the (tab, tuning-key) reductio: a fixed text whose musical identity is decided
entirely by an external key.

Code: `gtrsnipe/guitar/homograph.py` (solver), `gtrsnipe/guitar/strings.py`
(string physics). Tests: `tests/unit/test_homograph.py`, `tests/unit/test_strings.py`.
Worked examples: `examples/homograph/`.

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

- **Rank.** Let *r(A,B)* = the number of distinct intervals *bᵢ − aᵢ*. Every class
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
  choices must carry to tell the songs apart; the tunings carry the rest.
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
| rank | how many interval classes? | (always reported; ≥ N means impossible) |
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
- **Wound strings** load only their core (the wrap adds mass), so they have huge
  breaking headroom; their practical limit is tension.
- **Down never snaps** but below ~55% of normal tension (≈ −5 semitones) a
  string flops.

Status per string per song: `ok` · `slack` (< 55% tension) · `tight` (> 145%
tension or ≥ 70% of breaking stress) · `breaks` (≥ 90% of breaking stress, or ≥ 2×
tension — a bridge/neck hazard) · `impossible` (no steel string holds it at this
scale). For slack/tight/breaks the report suggests a catalog gauge that holds the
pitch at the original string's tension.

**Retune cost** (what the solver minimizes): semitones moved (tightening × 1.5 —
down never snaps) + 10 per string that needs a different gauge; impossible = ∞.
`--scale-length` and `--string-gauges` override the default set (10-46 guitar,
10-59 seven, 13-62 baritone @27″, 45-105 bass @34″, else a balanced ~17 lb set).

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
  split adds no interval class, so it costs almost nothing in rank.

Every edit is listed in the report and in the tab header (`// Re-rhythmed:`).
With `--homograph-octaves`, individual notes of B may also be displaced by
octaves (an arrangement liberty that folds intervals mod 12); the octave kept for
each class minimizes retune + notes displaced, and the count is reported.

**Chords.** Within a chord, which voice of B answers which voice of A is free (the
tab only fixes strings). Pairing is greedy: fewest new classes / simultaneous-class
collisions, tie-broken toward voice order. It's exact for melodies and a heuristic
for chords (a pairing search could only ever *lower* the rank it reports).

## 5. Limits and next steps

- Alignment + subdivision is pairwise (K = 2); K ≥ 3 songs need a 1:1 skeleton.
- The anchored search enumerates ≤ 20,000 string assignments (it notes truncation;
  never hit on 6 strings).
- **Phase 3 — in the wild.** Two searches, both cheap because rank needs no tab:
  (a) *pairs*: over a corpus of melodies (public-domain ABC/EsAC folk collections,
  hymn tunes sharing a metre), slide every alignment offset and find the longest
  window whose rank ≤ 6 — a sliding-window "≤ k distinct values" pass along each
  diagonal; (b) *fixed tabs*: take real published tabs of A and test them
  **as written** against candidate B's (per-string interval constancy is a linear
  check). Copyrighted inputs stay local (the golden-gate pattern).
