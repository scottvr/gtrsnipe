from dataclasses import dataclass
from itertools import product
from typing import Dict, Set, Optional, List, Tuple
from itertools import groupby
from ..core.types import MusicalEvent, FretPosition, Tuning, Technique
from ..core.config import MapperConfig
from ..core.theory import note_name_to_pitch, pitch_to_note_name
from collections import Counter

import logging

logger = logging.getLogger(__name__)

Fingering = Tuple[FretPosition, ...]

class GuitarMapper:
    def __init__(self, config: MapperConfig):
        self.config = config
        if getattr(config, "custom_tuning", None):
            # User-defined tuning (--tuning-pitches): note names low->high.
            self.tuning = None
            self.tuning_names = tuple(config.custom_tuning)
        else:
            try:
                self.tuning = Tuning[self.config.tuning.upper()]
            except KeyError:
                logger.warning(f"Unknown tuning '{self.config.tuning}'. Defaulting to STANDARD.")
                self.tuning = Tuning.STANDARD
            self.tuning_names = tuple(self.tuning.value)
        # tuning_names are low->high; string index 0 is the HIGHEST string, so the
        # open-string pitch array is the reverse (high->low).
        self.open_string_pitches = [note_name_to_pitch(n) for n in reversed(self.tuning_names)]
        self.pitch_to_positions: Dict[int, Set[FretPosition]] = {}
        self._build_pitch_maps()
        # Objective value of the last map_multi_string() path (None until run).
        self.last_path_score: Optional[float] = None
        logger.info("--- Chord-Aware Mapper initialized. ---")

    def _build_pitch_maps(self):
        capo_fret = self.config.capo
        for string_idx, base_pitch in enumerate(self.open_string_pitches):
            # The effective pitch of the "open" string is the base pitch + the capo position.
            capo_base_pitch = base_pitch + capo_fret
           # The number of available frets decreases by the capo position.
            # The loop now represents frets *above* the capo.
            for fret in range(self.config.max_fret - capo_fret + 1):
                # The actual MIDI pitch is the capo'd open string + the fret number.
                pitch = capo_base_pitch + fret
                
                # The FretPosition stores the fret number relative to the capo,
                # which is what will be displayed on the tab.
                pos = FretPosition(string_idx, fret)
                
                if pitch not in self.pitch_to_positions:
                    self.pitch_to_positions[pitch] = set()
                self.pitch_to_positions[pitch].add(pos)

    def _positions_for(self, note: MusicalEvent) -> Optional[Set[FretPosition]]:
        """Candidate positions for one note. A hook: a subclass can restrict them
        (the homograph solver pins each note to the strings of its interval class)."""
        return self.pitch_to_positions.get(note.pitch)

    def _map_to_single_string(self, events: List[MusicalEvent], string_index: int) -> List[MusicalEvent]:
        open_string_pitch = self.open_string_pitches[string_index]
        mapped_events = []
        for event in sorted(events, key=lambda e: e.time):
            fret = event.pitch - open_string_pitch
            if 0 <= fret <= self.config.max_fret:
                event.string = string_index
                event.fret = fret
                mapped_events.append(event)
            else:
                logger.warning(f"Note with pitch {event.pitch} is unplayable on string {string_index+1} (fret {fret}) and was dropped.")
        return mapped_events

    def _chord_span(self, fingering: Fingering) -> int:
        """Fret span of a fingering as the scorer sees it (open strings dropped under --ignore-open)."""
        if self.config.ignore_open:
            frets = [pos.fret for pos in fingering if pos.fret > 0]
        else:
            frets = [pos.fret for pos in fingering]
        return (max(frets) - min(frets)) if frets else 0

    def _report_no_fit(self, group: List[MusicalEvent], fingering: Fingering) -> None:
        """Tell the player when the chosen fingering is wider than the hand: every
        fingering of that chord was, and the mapper chose the least bad."""
        span = self._chord_span(fingering)
        if span > self.config.unplayable_fret_span:
            names = " ".join(pitch_to_note_name(ev.pitch) for ev in group)
            shape = " ".join(f"S{p.string + 1}:F{p.fret}" for p in fingering)
            logger.warning(
                f"No fingering of the chord at beat {group[0].time:g} ({names}) fits within "
                f"{self.config.unplayable_fret_span} frets; chose the least bad: {shape} (span {span})."
            )

    def _movement_factor(self, gap_seconds: Optional[float]) -> float:
        """How much dearer a hand move is for the time it had (M08): reference / gap, floored;
        1.0 when the time base is off or the gap is unknown (the first onset)."""
        if not self.config.movement_time_base or gap_seconds is None:
            return 1.0
        gap = max(gap_seconds, self.config.min_gap_seconds)
        return self.config.movement_reference_seconds / gap

    def _gap_seconds(self, prev_group: Optional[List[MusicalEvent]], group: List[MusicalEvent]) -> Optional[float]:
        """The time the hand had between two onset groups, by the configured time base; None
        when there is no previous group or the time base is off."""
        if not self.config.movement_time_base or not prev_group:
            return None
        spb = 60.0 / (self.config.tempo_bpm if self.config.tempo_bpm and self.config.tempo_bpm > 0 else 120.0)
        t = group[0].time
        if self.config.movement_time_base == "end":
            start = max(e.time + e.duration for e in prev_group)
        else:
            start = prev_group[0].time
        return max(0.0, (t - start) * spb)

    def _score_fingering(self, fingering: Fingering, prev_fingering: Optional[Fingering], prev_prev_fingering: Optional[Fingering],
                         gap_seconds: Optional[float] = None) -> float:
        """Scores a fingering based on internal shape, position, and transition cost.
        ``gap_seconds`` is the time the hand had for the move from ``prev_fingering`` (M08);
        a per-stage constant, so it leaves first-order Viterbi exact."""
        
        # 1. Internal Shape Score (Compactness)
        fret_span = self._chord_span(fingering)
        score = -fret_span * self.config.fret_span_penalty
        if fret_span > self.config.unplayable_fret_span:
            # Wider than the hand: rank it below every fingering that fits, but keep
            # scoring, so that when no fingering of a chord fits (all of them land here)
            # the other terms still choose the least bad one instead of the first one.
            score -= 1000

        # 2. Positional Score (Where on the neck?)
        if fingering:
            avg_fret = sum(p.fret for p in fingering) / len(fingering)
            if self.config.sweet_spot_low <= avg_fret <= self.config.sweet_spot_high:
                score += self.config.sweet_spot_bonus
            elif avg_fret > self.config.sweet_spot_high:
                positional_penalty = (avg_fret - self.config.sweet_spot_high) * self.config.high_fret_penalty
                strings_used = {pos.string for pos in fingering}
                if any(s >= 4 for s in strings_used): # Penalize high frets on low strings more
                    positional_penalty *= self.config.low_string_high_fret_multiplier
                score -= positional_penalty

        # 3. Barre Chord Score (Economy of Motion)
        if len(fingering) > 1: # Only apply to chords of 2 or more notes
            # We only consider fretted notes for barre shapes, ignoring open strings
            fretted_notes = [pos.fret for pos in fingering if pos.fret > 0]
            if fretted_notes:
                # Count the occurrences of each fret number
                fret_counts = Counter(fretted_notes)
                # Find the most common fret in the chord
                most_common_fret, count = fret_counts.most_common(1)[0]
                
                # If more than one note is on the same fret, it's a potential barre
                if count > 1:
                    # The bonus/penalty is proportional to the number of notes in the barre
                    score += (count - 1) * self.config.barre_bonus
                    score -= (count - 1) * self.config.barre_penalty

        # 4. Transition Score (Cost of movement from previous fingering)
        if prev_fingering and fingering:
            # Penalize movement up/down the neck
            avg_current_fret = sum(p.fret for p in fingering) / len(fingering)
            avg_prev_fret = sum(p.fret for p in prev_fingering) / len(prev_fingering)
            fret_diff = abs(avg_current_fret - avg_prev_fret)
            score -= fret_diff * self.config.movement_penalty * self._movement_factor(gap_seconds)
            
            # Penalize changing strings
            strings_used = {pos.string for pos in fingering}
            prev_strings_used = {pos.string for pos in prev_fingering}
            string_changes = len(strings_used.symmetric_difference(prev_strings_used))
            score -= string_changes * self.config.string_switch_penalty

            # Penalize fingerings that require an impossible stretch from the previous note.
            if self.config.diagonal_span_penalty:
                all_frets = [pos.fret for pos in fingering if pos.fret > 0]
                prev_frets = [pos.fret for pos in prev_fingering if pos.fret > 0]
                
                # Include the "previous-previous" frets if let-ring is on ---
                # This checks the span of the full three-note context.
                #
                # LANDMINE GUARD: this is the ONLY place the scorer reads t-2
                # (prev_prev_fingering). The Viterbi mapper's first-order collapse
                # is exact only because the score depends on t-2 solely through
                # this let_ring + diagonal_span gate — see `needs_second_order` in
                # map_multi_string(). If you add any deeper-history read here,
                # update needs_second_order (and its test) or global optimality
                # silently breaks. map_multi_string's _t2_delta mirrors this block
                # for the bucketed second-order DP: change both together.
                if self.config.let_ring_bonus > 0 and prev_prev_fingering:
                    prev_prev_frets = [pos.fret for pos in prev_prev_fingering if pos.fret > 0]
                    prev_frets.extend(prev_prev_frets)

                if all_frets and prev_frets:
                    # Calculate the maximum span between any note in the previous fingering
                    # and any note in the current fingering.
                    min_fret_combined = min(all_frets + prev_frets)
                    max_fret_combined = max(all_frets + prev_frets)
                    diagonal_span = max_fret_combined - min_fret_combined
                    
                    if diagonal_span > self.config.unplayable_fret_span:
                        # Apply a heavy penalty to effectively disqualify this fingering.
                        score -= 1000 

            # Reward fingerings that leave the previous note's string open.
            if self.config.let_ring_bonus > 0:
                # Find which strings from the previous fingering are now free.
                ringing_strings = prev_strings_used - strings_used
                if ringing_strings:
                    # Apply a bonus for each string that is now allowed to ring out.
                    score += len(ringing_strings) * self.config.let_ring_bonus

        if self.config.prefer_open:
            # Create a set of open string pitches for fast lookups
            open_pitches_set = set(self.open_string_pitches)
            
            for pos in fingering:
                # If this is a fretted note...
                if pos.fret > 0:
                    # ...calculate its pitch.
                    current_pitch = self.open_string_pitches[pos.string] + pos.fret
                    
                    # If that same pitch exists as an open string...
                    if current_pitch in open_pitches_set:
                        # ...apply a penalty to this fretted fingering.
                        score -= self.config.fretted_open_penalty

        return score    
    
    
    def _find_optimal_fingering(self, notes: List[MusicalEvent], prev_fingering: Optional[Fingering], prev_prev_fingering: Optional[Fingering],
                                gap_seconds: Optional[float] = None) -> Optional[Fingering]:
        note_positions = []
        for note in notes:
            positions = self._positions_for(note)
            if not positions: return None
            note_positions.append(positions)

        all_combinations = product(*note_positions)
        best_fingering = None
        max_score = -float('inf')

        for fingering in all_combinations:
            strings_used = {pos.string for pos in fingering}
            if len(strings_used) != len(fingering):
                continue

            score = self._score_fingering(fingering, prev_fingering, prev_prev_fingering, gap_seconds)

            logger.debug(f"considering score: {score} {fingering}")
            if score > max_score:
                max_score = score
                best_fingering = fingering
        logger.debug(f"best score: {max_score} {best_fingering}")
        self._last_choice_score = max_score if best_fingering is not None else None
        return best_fingering


    def _infer_technique_between_notes(self, prev_event: MusicalEvent, curr_event: MusicalEvent) -> str:
        if prev_event.fret is None or curr_event.fret is None: return Technique.PICK.value
        time_delta = curr_event.time - prev_event.time
        if time_delta < 0.01: return Technique.PICK.value
        if prev_event.string != curr_event.string: return Technique.PICK.value
        if time_delta > self.config.legato_time_threshold: return Technique.PICK.value
        if curr_event.fret > prev_event.fret: return Technique.HAMMER.value
        if curr_event.fret < prev_event.fret: return Technique.PULL.value
        return Technique.PICK.value

    def _infer_techniques_from_positions(self, mapped_events: List[MusicalEvent], no_articulations: bool, single_string_mode: bool = False) -> List[MusicalEvent]:
        if no_articulations or not mapped_events:
            if mapped_events:
                for event in mapped_events: event.technique = Technique.PICK.value
            return mapped_events

        # --- Pass 1: Infer base techniques (pick, hammer-on, pull-off) for all notes ---
        events_with_base_techniques = [mapped_events[0]]
        mapped_events[0].technique = Technique.PICK.value

        for i in range(1, len(mapped_events)):
            prev_event = mapped_events[i-1]
            curr_event = mapped_events[i]
            curr_event.technique = self._infer_technique_between_notes(prev_event, curr_event)
            events_with_base_techniques.append(curr_event)

        # --- Pass 2: If in single-string mode, identify runs and mark the highest note as a 'tap' ---
        if single_string_mode:
            runs, current_run = [], []
            for event in events_with_base_techniques:
                if event.technique == Technique.PICK.value:
                    if current_run: runs.append(current_run)
                    current_run = [event]
                else:
                    current_run.append(event)
            if current_run: runs.append(current_run)

            for run in runs:
                # Tapping is usually for runs of 3+ notes (e.g., pick-pull-tap)
                # This also prevents simple hammer-ons (e.g., 5h7) from becoming taps.
                if len(run) > self.config.tapping_run_threshold:
                    highest_pitch = max(e.pitch for e in run)

                    # If the highest note only appears once and is the first note,
                    # it's likely a descending run (e.g., 7p5p3), not a tapping one.
                    is_descending_run = sum(1 for e in run if e.pitch == highest_pitch) == 1 and run[0].pitch == highest_pitch

                    if not is_descending_run:
                        for note in run:
                            if note.pitch == highest_pitch:
                                note.technique = Technique.TAP.value
            
        return events_with_base_techniques
    
    def _normalize_pitch(self, pitch: int) -> int:
        """Normalization key used by the --dedupe path to collapse duplicate
        notes within a chord. Currently the identity (two notes dedupe iff they
        share the exact MIDI pitch); kept as a hook in case octave/enharmonic
        folding is wanted later."""
        return pitch

    def _preprocess_group(self, note_group: List[MusicalEvent]) -> List[MusicalEvent]:
        """Shared preprocessing for both optimizers: truncate an over-full chord
        to num_strings (keeping the lowest notes) and optionally deduplicate
        pitches. Ordering is preserved for determinism."""
        if len(note_group) > self.config.num_strings:
            logger.warning(
                f"Found an unplayable chord with {len(note_group)} notes at time "
                f"{note_group[0].time:.2f}. Keeping the lowest {self.config.num_strings} notes."
            )
            note_group = sorted(note_group, key=lambda event: event.pitch)[:self.config.num_strings]

        if not self.config.deduplicate_pitches:
            return note_group

        unique_pitches = {}
        deduplicated_note_group = []
        for note in note_group:
            norm_pitch = self._normalize_pitch(note.pitch)
            if norm_pitch not in unique_pitches:
                unique_pitches[norm_pitch] = note
                deduplicated_note_group.append(note)
        return deduplicated_note_group

    @staticmethod
    def _cand_key(fingering: Fingering):
        """Deterministic total order over fingerings (by string then fret)."""
        return tuple((p.string, p.fret) for p in fingering)

    def generate_candidates(self, group_notes: List[MusicalEvent]) -> List[Fingering]:
        """Enumerate ALL valid (distinct-string) fingerings for a group via a
        collision-pruned DFS. No lossy beam: the distinct-string constraint keeps
        this bounded (<=720 on a 6-string, usually a handful). Returns [] for a
        dead-end group (any note has no playable position), matching greedy."""
        note_positions = []
        for n in group_notes:
            pos = self._positions_for(n)
            if not pos:
                return []
            note_positions.append(sorted(pos, key=lambda p: (p.string, p.fret)))

        valid: List[Fingering] = []
        cap = self.config.hard_enum_cap
        capped = False

        def dfs(i, chosen, used):
            nonlocal capped
            if len(valid) >= cap:
                capped = True
                return
            if i == len(note_positions):
                valid.append(tuple(chosen))
                return
            for p in note_positions[i]:
                if p.string in used:            # distinct-string prune
                    continue
                chosen.append(p)
                used.add(p.string)
                dfs(i + 1, chosen, used)
                chosen.pop()
                used.discard(p.string)

        dfs(0, [], set())
        if capped:
            logger.warning(
                f"hard_enum_cap ({cap}) hit at time {group_notes[0].time:.2f}; "
                "fingering for this group may be non-optimal."
            )
        valid.sort(key=self._cand_key)          # deterministic DP order
        return valid

    def _t2_delta(self, rk, rj, rpp) -> float:
        """What the scorer's t-2 term adds to score(f_k, f_j, None) when the true
        f_{t-2} has fretted range ``rpp``: the diagonal-span check over the three
        fingerings' fretted frets fires (-1000) where the check over two did not.
        Mirrors the LANDMINE GUARD block in _score_fingering exactly (the only t-2
        read), with ranges in place of fret lists; the equivalence test holds the
        plain triple loop as the oracle for both."""
        if rpp is None or rk is None:
            return 0.0
        cap = self.config.unplayable_fret_span
        if rj is not None and max(rk[1], rj[1]) - min(rk[0], rj[0]) > cap:
            return 0.0                      # already -1000 without f_{t-2}
        lo = min(rk[0], rpp[0]) if rj is None else min(rk[0], rj[0], rpp[0])
        hi = max(rk[1], rpp[1]) if rj is None else max(rk[1], rj[1], rpp[1])
        return -1000.0 if hi - lo > cap else 0.0

    @staticmethod
    def _fretted_range(fingering: Fingering):
        """(lowest, highest) fretted fret of a fingering, or None if all strings are
        open: everything the scorer's t-2 term reads from prev_prev_fingering."""
        frets = [p.fret for p in fingering if p.fret > 0]
        return (min(frets), max(frets)) if frets else None

    def map_multi_string(self, time_groups: List[List[MusicalEvent]]) -> List[MusicalEvent]:
        """Global-optimum fretboard mapping via Viterbi/DP over a trellis.

        Each time-group is a stage whose nodes are its valid fingerings. Edge and
        emission costs come from the UNMODIFIED _score_fingering, so the DP's
        objective is identical to greedy's, and its optimum is provably >= greedy.
        First-order Viterbi is exact unless the scorer's t-2 term is active
        (let_ring + diagonal_span), in which case an ordered pair-state carries
        the true f_{t-2}. See DESIGN-viterbi-mapper.md.
        """
        NONE = -1  # sentinel index for "no fingering" (absent prev / prev_prev)
        self.last_path_score = None    # until this call finds a path (the early returns below)

        kept: List[List[MusicalEvent]] = []
        cand: List[List[Fingering]] = []
        for g in time_groups:
            g2 = self._preprocess_group(g)
            cs = self.generate_candidates(g2)
            if cs:
                kept.append(g2)
                cand.append(cs)
            else:
                # Dead-end group: notes not emitted, context does not advance
                # (identical to greedy's None-skip).
                logger.warning(f"Could not find a playable fingering for notes at time {g[0].time}")

        T = len(cand)
        if T == 0:
            return []

        second_order = bool(self.config.diagonal_span_penalty and self.config.let_ring_bonus > 0)
        # Per-song memo of step scores (scottvr, 2026-11-07): pieces repeat their progressions,
        # so the same (fingering, previous, gap) comes round again; hit rates 27-78% measured.
        _score, _memo = self._score_fingering, {}
        def sc(f, p, pp, gap=None):
            if pp is not None:
                return _score(f, p, pp, gap)
            key = (f, p, gap)
            v = _memo.get(key)
            if v is None:
                v = _memo[key] = _score(f, p, None, gap)
            return v
        # M08: the time each stage's hand move had, a per-stage constant (None = time base off)
        gaps = [None] + [self._gap_seconds(kept[t - 1], kept[t]) for t in range(1, T)]

        BP = [dict() for _ in range(T)]

        # stage 0: virtual predecessor; emission = score(f, None, None)
        V = {}
        for j, fj in enumerate(cand[0]):
            V[(NONE, j)] = sc(fj, None, None)
            BP[0][(NONE, j)] = None

        # stage 1: prev_prev is still None (matches greedy at t=1)
        if T > 1:
            Vn = {}
            for j, fj in enumerate(cand[1]):
                for i, fi in enumerate(cand[0]):
                    if (NONE, i) not in V:
                        continue
                    s = V[(NONE, i)] + sc(fj, fi, None, gaps[1])
                    st = (i, j)
                    if st not in Vn or s > Vn[st]:
                        Vn[st] = s
                        BP[1][st] = (NONE, i)
            V = Vn

        # stages t >= 2: ordered pair-state (f_{t-1}, f_t).
        #
        # Both branches below are exact rewrites of the plain triple loop
        # "for k, for j, for i: V[(i, j)] + score(f_k, f_j, f_i)", with the same
        # tie-break (among equal values, the smallest i), so the path and its
        # score are identical; tests/mapper/test_viterbi_equivalence.py holds the
        # plain loop as the oracle. The rewrites remove a factor of K_{t-2} from
        # the work on chordal music, where K reaches the hundreds.
        ranges = [[self._fretted_range(f) for f in cs] for cs in cand] if second_order else None
        for t in range(2, T):
            Vn = {}
            prev_c, pp_c = cand[t - 1], cand[t - 2]
            if second_order:
                # The scorer reads f_{t-2} only through the lowest and highest fretted
                # fret it carries (the combined-span check), so f_{t-2} candidates that
                # share that pair are interchangeable: keep the best path value per
                # (pair, j) and score once per bucket instead of once per candidate.
                keys = ranges[t - 2]
                buckets: List[dict] = [dict() for _ in prev_c]   # j -> {key: (V, i)}
                for (i, j), v in V.items():
                    b = buckets[j]
                    cur = b.get(keys[i])
                    if cur is None or v > cur[0] or (v == cur[0] and i < cur[1]):
                        b[keys[i]] = (v, i)
                for k, fk in enumerate(cand[t]):
                    rk = ranges[t][k]
                    for j, fj in enumerate(prev_c):
                        # score(f_k, f_j, f_i) == score(f_k, f_j, None) + _t2_delta(...): the
                        # t-2 term is a flat -1000 the combined-span check may add, nothing else.
                        base = sc(fk, fj, None, gaps[t])
                        rj = ranges[t - 1][j]
                        best_s = None
                        best_i = -1
                        for key, (v, i) in buckets[j].items():
                            s = v + base + self._t2_delta(rk, rj, key)
                            if best_s is None or s > best_s or (s == best_s and i < best_i):
                                best_s = s
                                best_i = i
                        if best_s is None:
                            continue
                        Vn[(j, k)] = best_s
                        BP[t][(j, k)] = (best_i, j)
            else:
                # The score is independent of f_{t-2}: the best predecessor of each j
                # is the same for every k, so find it once per j, then add the step
                # cost once per (j, k).
                best_prev: dict = {}                          # j -> (V, i)
                for (i, j), v in V.items():
                    cur = best_prev.get(j)
                    if cur is None or v > cur[0] or (v == cur[0] and i < cur[1]):
                        best_prev[j] = (v, i)
                for k, fk in enumerate(cand[t]):
                    for j, fj in enumerate(prev_c):
                        bp = best_prev.get(j)
                        if bp is None:
                            continue
                        Vn[(j, k)] = bp[0] + sc(fk, fj, None, gaps[t])
                        BP[t][(j, k)] = (bp[1], j)
            V = Vn

        if not V:
            return []

        # termination + traceback (store current-fingering index at each stage)
        end_state = max(sorted(V, key=lambda s: (s[0], s[1])), key=lambda s: V[s])
        self.last_path_score = V[end_state]
        chosen_idx = [0] * T
        st = end_state
        for t in range(T - 1, -1, -1):
            chosen_idx[t] = st[1]
            st = BP[t][st]

        # index-aligned write-back
        out: List[MusicalEvent] = []
        for t, g2 in enumerate(kept):
            f = cand[t][chosen_idx[t]]
            for i, ev in enumerate(g2):
                ev.fret, ev.string = f[i].fret, f[i].string
            self._report_no_fit(g2, f)
            out.extend(g2)
        return out

    def _map_multi_string_greedy(self, time_groups: List[List[MusicalEvent]]) -> List[MusicalEvent]:
        """Legacy greedy per-step mapping, kept behind --optimizer greedy.

        Sets ``last_path_score`` like the Viterbi mapper: the sum of the chosen
        fingerings' scores under the same objective, so the two can be compared."""
        multi_string_events = []
        last_fingering: Optional[Fingering] = None
        prev_prev_fingering: Optional[Fingering] = None
        last_group: Optional[List[MusicalEvent]] = None
        self.last_path_score = None
        path_score = 0.0

        for note_group in time_groups:
            group_to_finger = self._preprocess_group(note_group)
            fingering = self._find_optimal_fingering(group_to_finger, last_fingering, prev_prev_fingering,
                                                     self._gap_seconds(last_group, group_to_finger))
            if fingering:
                for i, note_event in enumerate(group_to_finger):
                    note_event.fret = fingering[i].fret
                    note_event.string = fingering[i].string
                self._report_no_fit(group_to_finger, fingering)
                multi_string_events.extend(group_to_finger)
                prev_prev_fingering = last_fingering
                last_fingering = fingering
                last_group = group_to_finger
                path_score += self._last_choice_score
                self.last_path_score = path_score
            else:
                logger.warning(f"Could not find a playable fingering for notes at time {note_group[0].time}")
        return multi_string_events

    def map_events_to_fretboard(self, events: List[MusicalEvent], no_articulations: bool, single_string: Optional[int] = None) -> List[MusicalEvent]:
        if not events: return []

        mapped_events: List[MusicalEvent]

        if single_string is not None:
            logger.info(f"--- Single-string mode active. Mapping all notes to string {single_string}. ---")
            string_index = single_string - 1
            mapped_events = self._map_to_single_string(events, string_index)
        else:
            QUANTIZATION_RESOLUTION = self.config.quantization_resolution
            def quantize_time(beat): return round(beat / QUANTIZATION_RESOLUTION) * QUANTIZATION_RESOLUTION

            sorted_events = sorted(events, key=lambda e: e.time)
            time_groups = [list(g) for t, g in groupby(sorted_events, key=lambda e: quantize_time(e.time))]

            if self.config.optimizer == "greedy":
                mapped_events = self._map_multi_string_greedy(time_groups)
            else:
                mapped_events = self.map_multi_string(time_groups)

        return self._infer_techniques_from_positions(mapped_events, no_articulations, single_string_mode=(single_string is not None))
