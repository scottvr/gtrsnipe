# Design: Viterbi / DP Fretboard Mapper

_Epic B of v0.3.0. Branch `feat/viterbi-mapper`. This design was produced with
independent adversarial verification; the corrections that survived that review
are baked in below._

## 1. The problem, precisely

For a time-ordered sequence of note-groups (chords) `g_1 … g_T`, each pitch can
be played at several `(string, fret)` positions, so each group `g_t` has a set
of candidate **fingerings** `C_t`. The mapper must choose one fingering per
group to maximize an additive playability score

```
J = Σ_t  score(f_t, f_{t-1}, f_{t-2})
```

where `score` = `GuitarMapper._score_fingering` (shape + position + barre +
transition + prefer-open). Searching all sequences is `∏_t |C_t|` — exponential
in `T`. **That cross-time exponential is the real "combinatorial explosion."**

### What the code does today (ground truth — the whitepaper is aspirational)

`map_events_to_fretboard` is **greedy**: for each group it enumerates
`itertools.product(*note_positions)` and picks the single best fingering *given
the already-fixed previous group*. It never reconsiders. `_score_fingering`
reads `prev_prev_fingering` (t-2) in exactly one place — the `let_ring`-gated
diagonal-span extension (`mapper.py:123-125`) — so the objective has a genuine
**two-step** memory.

## 2. The fix: dynamic programming over a trellis (Viterbi)

Model each group as a **trellis stage** whose nodes are its candidate
fingerings. Emission/step cost and transition cost both come from the
**unmodified** `_score_fingering`. The Viterbi recurrence finds the global
`argmax J` in time **linear in `T`** instead of exponential. This is the
shortest-path-through-a-Markov-chain idea (Viterbi decoding).

Two design choices make it both **exact** and **simple**:

### 2.1 Enumerate *all* valid fingerings per chord — no lossy beam

Adversarial review killed the original "beam to top-K by emission score" idea:
emission-only ranking ignores exactly the transition terms the DP exists to
exploit, so it can prune the globally-optimal candidate. It is also
**unnecessary**: the per-chord candidate count is *already bounded* by the
distinct-string constraint (two notes can't share a string). For a 6-string
instrument the worst case is `6·5·4·3·2·1 = 720`, and real chords are a
handful; a single melody note has ≤ `num_strings`. So we enumerate **every**
valid fingering exactly via a collision-pruned DFS.

- `hard_enum_cap` (default 4096) is only a **pathological safety valve**; if it
  ever triggers we **log a warning** (results are then no longer provably
  optimal for that group). It is expected never to fire on real music.
- No approximation in the normal case → the DP returns the **true global
  optimum** (for the applicable model order, see §2.3).

### 2.2 Reuse `_score_fingering` verbatim (identical scoring semantics)

The DP never re-implements the scoring math. Two equivalent framings — pick per
implementation:

- **Pair-state framing (used below):** the edge cost is the single unmodified
  call `score(f_t, f_{t-1}, f_{t-2})`.
- **Decomposition framing (equivalent):** `emission(f) = score(f, None, None)`
  and `transition(prev,cur,pp) = score(cur,prev,pp) − score(cur,None,None)`.
  This is exact because block 4 (the only transition-dependent block) is gated
  by `if prev_fingering and fingering:`, so `score(cur,None,None)` is exactly
  blocks 1+2+3+5. The `-1000` short-circuits stay correct (both terms return
  `-1000` → transition 0 → total `-1000`). **If you use this framing, the
  subtraction is mandatory** — adding `score(cur,prev,pp)` on top of `emission`
  double-counts blocks 1/2/3/5.

Because greedy's realized total is `Σ_t score(chosen_t, …)` over the same
candidate universe and the same function, the DP optimum is provably **≥ greedy**.

### 2.3 Adaptive model order — first-order by default, exact second-order when needed

`score` depends on `f_{t-2}` **only** through the block guarded by
`if let_ring_bonus > 0 and prev_prev_fingering` combined with
`diagonal_span_penalty`. Therefore:

```
needs_second_order = config.diagonal_span_penalty and config.let_ring_bonus > 0
```

- **Default config (`let_ring_bonus == 0` or `diagonal_span_penalty` off):** the
  score is independent of `f_{t-2}`; the max over predecessors factors out and a
  **first-order** Viterbi (state = one fingering) is *provably exact*.
  Cost `O(T·K²)`.
- **Second-order needed:** use an ordered **pair-state** `(f_{t-1}, f_t)`. An
  edge `(a,b) → (b,c)` carries the true `f_{t-2}=a`, so the diagonal/let-ring
  t-2 term is evaluated exactly — **no backpointer heuristic** (adversarial
  review showed the backpointer-recovery approach is inexact; pair-state is the
  correct default whenever second order is required). Cost `O(T·K³)`.

> **Landmine guard (must implement):** the first-order collapse is valid *only*
> because `_score_fingering` reads no history deeper than t-2. Add an assertion
> / unit test that fails if the scorer gains a new `prev_prev` (or deeper)
> reference, and a comment at the `prev_prev` site pointing back to
> `needs_second_order`. Otherwise a future scorer edit silently breaks exactness.

## 3. Reference algorithm (pair-state, collapsing to first-order)

```python
NONE = -1  # sentinel index: "no fingering" (absent prev / prev_prev)

def cand_key(f):                      # deterministic total order
    return tuple((p.string, p.fret) for p in f)

def generate_candidates(self, group_notes):
    note_positions = []
    for n in group_notes:
        pos = self.pitch_to_positions.get(n.pitch)
        if not pos:
            return []                 # unmappable note -> dead-end group (== mapper.py:168)
        note_positions.append(sorted(pos, key=lambda p: (p.string, p.fret)))
    valid = []
    def dfs(i, chosen, used):
        if len(valid) >= self.config.hard_enum_cap:
            logger.warning("hard_enum_cap hit at t=%.2f; result may be non-optimal", group_notes[0].time)
            return
        if i == len(note_positions):
            valid.append(tuple(chosen)); return
        for p in note_positions[i]:
            if p.string in used:       # distinct-string prune (== the len(strings)!=len filter, mapper.py:177)
                continue
            chosen.append(p); used.add(p.string)
            dfs(i + 1, chosen, used)
            chosen.pop(); used.discard(p.string)
    dfs(0, [], set())
    valid.sort(key=cand_key)           # stable, deterministic DP order
    return valid                       # ALL valid fingerings; no beam

def map_multi_string(self, time_groups):
    kept, cand = [], []
    for g in time_groups:
        g2 = self._preprocess_group(g)          # num_strings truncation + deduplicate_pitches (== mapper.py:265-290)
        cs = self.generate_candidates(g2)
        if cs:
            kept.append(g2); cand.append(cs)
        else:
            logger.warning("Could not find a playable fingering for notes at time %s", g[0].time)
            # dropped: notes not emitted, context does NOT advance (== mapper.py:302-303)
    T = len(cand)
    if T == 0:
        return []

    second_order = self.config.diagonal_span_penalty and self.config.let_ring_bonus > 0
    sc = self._score_fingering                  # UNMODIFIED scorer

    # stage 0 : virtual state (prev=NONE, cur=j); emission = score(f, None, None)
    V, BP = {}, [dict() for _ in range(T)]
    for j, fj in enumerate(cand[0]):
        V[(NONE, j)] = sc(fj, None, None); BP[0][(NONE, j)] = None

    # stage 1 : prev_prev is None (matches greedy: prev_prev still None at t=1)
    if T > 1:
        Vn = {}
        for j, fj in enumerate(cand[1]):
            for i, fi in enumerate(cand[0]):
                s, st = V[(NONE, i)] + sc(fj, fi, None), (i, j)
                if st not in Vn or s > Vn[st]:          # strict >, sorted iteration => deterministic
                    Vn[st] = s; BP[1][st] = (NONE, i)
        V = Vn

    # stages t >= 2 : pair-state
    for t in range(2, T):
        Vn = {}
        for k, fk in enumerate(cand[t]):
            for j, fj in enumerate(cand[t - 1]):
                best_s = best_prev = None
                if second_order:
                    for i, fi in enumerate(cand[t - 2]):
                        if (i, j) not in V: continue
                        s = V[(i, j)] + sc(fk, fj, fi)   # fi is the TRUE f_{t-2}
                        if best_s is None or s > best_s: best_s, best_prev = s, (i, j)
                else:                                     # score independent of f_{t-2}
                    for i, _ in enumerate(cand[t - 2]):
                        if (i, j) not in V: continue
                        if best_s is None or V[(i, j)] > best_s: best_s, best_prev = V[(i, j)], (i, j)
                    if best_prev is not None:
                        best_s += sc(fk, fj, None)
                if best_prev is None: continue
                Vn[(j, k)] = best_s; BP[t][(j, k)] = best_prev
        V = Vn

    # termination + traceback (store the current-fingering index at each stage)
    end_state = max(sorted(V, key=lambda s: (s[0], s[1])), key=lambda s: V[s])
    chosen_idx = [0] * T
    st = end_state
    for t in range(T - 1, -1, -1):
        chosen_idx[t] = st[1]                  # second element == current-fingering index
        st = BP[t][st]

    # write-back (index-aligned, == mapper.py:296-299)
    out = []
    for t, g2 in enumerate(kept):
        f = cand[t][chosen_idx[t]]
        for i, ev in enumerate(g2):
            ev.fret, ev.string = f[i].fret, f[i].string
        out.extend(g2)
    return out

# caller keeps single-string mode untouched and still runs:
#   mapped = map_multi_string(time_groups)   # multi-string branch only
#   return self._infer_techniques_from_positions(mapped, no_articulations, single_string_mode=False)
```

## 4. Correctness & edge cases (verified)

- **Scoring identity.** Every group's full score is placed on exactly one
  edge/stage via the unmodified `_score_fingering`, counted once. The line-71
  early return still suppresses the line-136 diagonal `-1000` exactly as greedy.
- **t-2 exactness.** Pair-state carries the true `f_{t-2}`; verifier confirmed
  `prev_prev` is read only at `mapper.py:123-125`, so `needs_second_order` is
  correct *for the current scorer* (hence the landmine guard in §2.3).
- **Dead-ends match greedy.** Groups with an unmappable pitch or no
  distinct-string assignment yield `[]`, are logged, and are **excluded from the
  trellis** without advancing context — identical threading to greedy's
  `None`-skip. All groups dead → returns `[]`.
- **All-`-1000` (unplayable but mappable) groups.** Kept as states; the DP still
  selects the least-bad path and writes a fingering — matching greedy's "keep
  the note anyway" fallback (objective ≥ greedy, never crashes).
- **Boundaries.** Stage 0 uses `score(f,None,None)`; stage 1 uses `prev_prev=None`
  — byte-matching greedy's first two calls. `T==1` reduces to greedy's
  first-group argmax (up to the deterministic tie-break).
- **Complexity.** First-order `O(T·K²)` time / `O(T·K)` space; pair-state
  `O(T·K³)` time / `O(T·K²)` space (K ≤ 720, usually ≪). Candidate generation is
  bounded DFS. A strict, bounded improvement over greedy's unbounded per-chord
  `product()` while searching globally.

## 5. Determinism (a deliberate, documented change)

Greedy's tie-break silently depends on Python set/hash iteration order of
`FretPosition` sets. The DP sorts every candidate list by `cand_key` and uses
strict `>` in every argmax, so **among equal-scoring paths the lexicographically
smallest (lowest string indices, then frets) wins** — a pure function of the
input. This differs from greedy **only on exact ties**. Document it; cover it
with a real-tie unit test.

## 6. Backward compatibility & rollout

- **`--optimizer {viterbi,greedy}`**, default **`viterbi`** (D3). Add
  `MapperConfig.optimizer: str = "viterbi"` plus `candidate_cap` (unused in the
  no-beam design but reserved) and `hard_enum_cap: int = 4096`. Keep the greedy
  code path intact behind the flag for one release.
- **Where output changes vs. greedy:** (a) globally re-optimized fingerings on
  tracks where greedy's local choice was suboptimal (strictly better/equal J);
  (b) deterministic tie-breaks. No change to per-fingering semantics, dead-end
  handling, single-string mode, or technique inference.
- **Golden files** (e.g. the Asturias output in
  `docs/wiki/4.Example-Asturias_Leyenda.md`) were produced by greedy and will
  need regeneration + human review once Viterbi lands — done as a **separate
  blessing step** from the bug-fix re-bless (Risk R1).

## 7. Corrections carried over from adversarial review (do not skip)

1. **Traceback**: store the current-fingering index (`st[1]`) at each stage
   during the backward walk; do not recompute. Unit-test on a hand-built ≥3-stage
   trellis with a tie.
2. **Determinism**: sort candidates by `cand_key`; strict `>`; test with a
   constructed exact tie. Ensure `deduplicate_pitches` ordering is deterministic too.
3. **Preserve** single-string mode, `_infer_techniques_from_positions`, and
   index-aligned write-back after `_preprocess_group`.
4. **No emission-only beam** (§2.1). If `hard_enum_cap` ever fires, log it and
   treat that group's result as non-guaranteed.
5. **Landmine guard** for the scorer's history depth (§2.3).
6. **Equivalence test**: on a `let_ring + diagonal_span` input, assert the
   pair-state (`O(K³)`) and first-order-collapse paths agree where the collapse
   claims exactness; assert Viterbi's `J` ≥ greedy's `J` on a corpus.
