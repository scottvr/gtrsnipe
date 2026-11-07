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

    # ---- the scorer as features x weights -------------------------------------------
    #
    # A step score is a dot product: step_features() extracts what a fingering and its
    # transition look like (frets of span, frets of hand travel, strings changed, ...) and
    # step_weights() turns the config into the vector it is multiplied by. Structural
    # settings (sweet-spot bounds, the unplayable span, ignore-open, the diagonal-span
    # flag, and whether let-ring is on at all) live in the features; everything that is
    # an exchange rate lives in the weights. This lets a profile be a weight vector,
    # lets tempo scale one component (M08 multiplies the travel feature), and lets a
    # sweep or a weight fit extract features once and re-score by dot product
    # (map_paths_for_weights). The arithmetic is the pre-refactor scorer's, term by term
    # and in the same order, so scores are identical to the last bit on every input
    # tested (tests/mapper/test_viterbi_equivalence.py).

    FEATURE_NAMES: Tuple[str, ...] = (
        "span",            # fret span of the fingering (open strings dropped under ignore_open)
        "span_break",      # 1 if that span is wider than unplayable_fret_span
        "in_sweet_spot",   # 1 if the mean fret is inside [sweet_spot_low, sweet_spot_high]
        "over_sweet_spot", # frets the mean sits above sweet_spot_high (x low_string multiplier if a low string is used)
        "barre",           # notes sharing the most common fretted fret, minus one
        "move",            # frets of mean-position travel from the previous fingering, x the M08 time factor
        "string_switch",   # strings used by exactly one of the two fingerings
        "diagonal_break",  # 1 if the combined fretted span over the last two (or three) fingerings is unplayable
        "ringing",         # previous strings this fingering leaves free to ring
        "fretted_open",    # fretted notes whose pitch an open string could play
    )

    def step_weights(self) -> Tuple[float, ...]:
        """The config as the weight vector step_features() is scored against (same order
        as FEATURE_NAMES; penalties negative, bonuses positive)."""
        c = self.config
        return (
            -c.fret_span_penalty,
            -1000.0,
            c.sweet_spot_bonus,
            -c.high_fret_penalty,
            c.barre_bonus - c.barre_penalty,
            -c.movement_penalty,
            -c.string_switch_penalty,
            -1000.0 if c.diagonal_span_penalty else 0.0,
            c.let_ring_bonus,
            -c.fretted_open_penalty if c.prefer_open else 0.0,
        )

    EMISSION = 5   # the first EMISSION features depend on the fingering alone

    def emission_features(self, fingering: Fingering) -> Tuple[float, ...]:
        """The features of a fingering by itself: span, span_break, in_sweet_spot,
        over_sweet_spot, barre (FEATURE_NAMES[:EMISSION]). The DP computes these once per
        candidate per stage, not once per pair."""
        c = self.config

        # 1. internal shape
        span = float(self._chord_span(fingering))
        span_break = 1.0 if span > c.unplayable_fret_span else 0.0

        # 2. position on the neck
        in_spot = over = 0.0
        if fingering:
            avg_fret = sum(p.fret for p in fingering) / len(fingering)
            if c.sweet_spot_low <= avg_fret <= c.sweet_spot_high:
                in_spot = 1.0
            elif avg_fret > c.sweet_spot_high:
                over = avg_fret - c.sweet_spot_high
                if any(p.string >= 4 for p in fingering):   # high frets on the low strings
                    over *= c.low_string_high_fret_multiplier

        # 3. barre (two or more notes on the same fret)
        barre = 0.0
        if len(fingering) > 1:
            fretted_notes = [p.fret for p in fingering if p.fret > 0]
            if fretted_notes:
                _, count = Counter(fretted_notes).most_common(1)[0]
                if count > 1:
                    barre = float(count - 1)

        return (span, span_break, in_spot, over, barre)

    def transition_features(self, fingering: Fingering, prev_fingering: Optional[Fingering],
                            prev_prev_fingering: Optional[Fingering],
                            gap_seconds: Optional[float] = None) -> Tuple[float, ...]:
        """The features of the step into a fingering: move, string_switch, diagonal_break,
        ringing, fretted_open (FEATURE_NAMES[EMISSION:]). ``gap_seconds`` is the time the
        hand had for the move (M08), a per-stage constant. (fretted_open depends on the
        fingering alone but is scored after the transition terms, and the sum is kept in the
        pre-refactor order so scores stay bit-identical.)"""
        c = self.config
        move = switch = diagonal = ringing = 0.0
        if prev_fingering and fingering:
            avg_current = sum(p.fret for p in fingering) / len(fingering)
            avg_prev = sum(p.fret for p in prev_fingering) / len(prev_fingering)
            move = abs(avg_current - avg_prev) * self._movement_factor(gap_seconds)

            strings_used = {p.string for p in fingering}
            prev_strings_used = {p.string for p in prev_fingering}
            switch = float(len(strings_used.symmetric_difference(prev_strings_used)))

            if c.diagonal_span_penalty:
                all_frets = [p.fret for p in fingering if p.fret > 0]
                prev_frets = [p.fret for p in prev_fingering if p.fret > 0]
                # LANDMINE GUARD: this is the ONLY place the scorer reads t-2
                # (prev_prev_fingering). The Viterbi mapper's first-order collapse is
                # exact only because the score depends on t-2 solely through this
                # let_ring + diagonal_span gate; see `second_order` in _viterbi and
                # `_t2_delta`, which mirrors this block. Any deeper-history read here
                # must update both (and the test), or global optimality silently breaks.
                if c.let_ring_bonus > 0 and prev_prev_fingering:
                    prev_frets.extend(p.fret for p in prev_prev_fingering if p.fret > 0)
                if all_frets and prev_frets:
                    if max(all_frets + prev_frets) - min(all_frets + prev_frets) > c.unplayable_fret_span:
                        diagonal = 1.0

            ringing = float(len(prev_strings_used - strings_used))

        # fretted notes an open string could have played
        fretted_open = 0.0
        open_pitches = self.open_string_pitches
        for p in fingering:
            if p.fret > 0 and (open_pitches[p.string] + p.fret) in open_pitches:
                fretted_open += 1.0

        return (move, switch, diagonal, ringing, fretted_open)

    def step_features(self, fingering: Fingering, prev_fingering: Optional[Fingering],
                      prev_prev_fingering: Optional[Fingering],
                      gap_seconds: Optional[float] = None) -> Tuple[float, ...]:
        """The feature vector of one step (see FEATURE_NAMES): emission_features of the
        fingering followed by transition_features of the step into it."""
        return self.emission_features(fingering) + self.transition_features(
            fingering, prev_fingering, prev_prev_fingering, gap_seconds)

    @staticmethod
    def score_features(features: Tuple[float, ...], weights: Tuple[float, ...],
                       more: Tuple[float, ...] = (), more_weights: Tuple[float, ...] = ()) -> float:
        """Dot product accumulated term by term in feature order, continuing through
        ``more`` (the transition features after the emission ones) in ONE running sum: the
        pre-refactor scorer's order, so scores are bit-identical and near-ties break the
        same way. (Two partial sums added together moved the last bit on fret averages
        over three notes and flipped a tie on one classtab piece.)"""
        score = 0.0
        for f, w in zip(features, weights):
            if f:
                score += f * w
        for f, w in zip(more, more_weights):
            if f:
                score += f * w
        return score

    def _score_fingering(self, fingering: Fingering, prev_fingering: Optional[Fingering], prev_prev_fingering: Optional[Fingering],
                         gap_seconds: Optional[float] = None) -> float:
        """Score of a fingering given the previous (and, under the second-order gate, the one
        before): step_features() dotted with step_weights(). Kept as the one scoring entry
        point the greedy path, the tests and the research code call."""
        return self.score_features(self.step_features(fingering, prev_fingering, prev_prev_fingering, gap_seconds),
                                   self.step_weights())

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

    def _trellis(self, time_groups: List[List[MusicalEvent]]):
        """Stages of the DP: the kept groups, their candidate fingerings, and the time each
        hand move had (M08). Dead-end groups are dropped as greedy drops them."""
        kept: List[List[MusicalEvent]] = []
        cand: List[List[Fingering]] = []
        for g in time_groups:
            g2 = self._preprocess_group(g)
            cs = self.generate_candidates(g2)
            if cs:
                kept.append(g2)
                cand.append(cs)
            else:
                logger.warning(f"Could not find a playable fingering for notes at time {g[0].time}")
        gaps = [None] + [self._gap_seconds(kept[t - 1], kept[t]) for t in range(1, len(kept))]
        return kept, cand, gaps

    def _viterbi(self, cand: List[List[Fingering]], gaps: List[Optional[float]],
                 weights: Tuple[float, ...], memo: dict):
        """Best path through the trellis under ``weights``: (chosen candidate index per
        stage, path score), or (None, None) if there is none. ``memo`` caches step
        feature vectors by (fingering, previous, gap) and may be shared across calls with
        different weights (map_paths_for_weights): features do not depend on weights.

        First-order Viterbi is exact unless the scorer's t-2 term is active (let_ring +
        diagonal_span), in which case an ordered pair-state carries the true f_{t-2}.
        See DESIGN-viterbi-mapper.md. Both stage loops below are exact rewrites of the
        plain triple loop "for k, for j, for i", with the same tie-break (the smallest i
        among equal values); tests/mapper/test_viterbi_equivalence.py keeps that loop as
        the oracle."""
        NONE = -1
        T = len(cand)
        if T == 0:
            return None, None
        second_order = bool(self.config.diagonal_span_penalty and self.config.let_ring_bonus > 0)
        emit, trans, dot = self.emission_features, self.transition_features, self.score_features
        E = self.EMISSION
        w_e, w_t = weights[:E], weights[E:]
        emis = memo.setdefault("emission", {})      # fingering -> emission features
        pairs = memo.setdefault("transition", {})   # (fingering, prev, gap) -> transition features

        def sc(f, p, pp, gap=None):
            e = emis.get(f)
            if e is None:
                e = emis[f] = emit(f)
            if pp is not None:
                return dot(e, w_e, trans(f, p, pp, gap), w_t)
            key = (f, p, gap)
            v = pairs.get(key)
            if v is None:
                v = pairs[key] = trans(f, p, None, gap)
            return dot(e, w_e, v, w_t)

        BP = [dict() for _ in range(T)]
        V = {}
        for j, fj in enumerate(cand[0]):
            V[(NONE, j)] = sc(fj, None, None)
            BP[0][(NONE, j)] = None
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

        ranges = [[self._fretted_range(f) for f in cs] for cs in cand] if second_order else None
        for t in range(2, T):
            Vn = {}
            prev_c = cand[t - 1]
            if second_order:
                # f_{t-2} matters only through its (lowest, highest) fretted fret, so bucket
                # the predecessors by that and score once per (f_{t-1}, f_t) pair, adding the
                # flat t-2 delta per bucket.
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
                # the best predecessor of each j is the same for every k
                best_prev: dict = {}
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
            return None, None
        end_state = max(sorted(V, key=lambda s: (s[0], s[1])), key=lambda s: V[s])
        chosen = [0] * T
        st = end_state
        for t in range(T - 1, -1, -1):
            chosen[t] = st[1]
            st = BP[t][st]
        return chosen, V[end_state]

    def map_multi_string(self, time_groups: List[List[MusicalEvent]]) -> List[MusicalEvent]:
        """Global-optimum fretboard mapping via Viterbi/DP over a trellis.

        Each time-group is a stage whose nodes are its valid fingerings. Edge and
        emission costs come from the UNMODIFIED _score_fingering (features x the
        config's weights), so the DP's objective is identical to greedy's and its
        optimum is provably >= greedy's."""
        self.last_path_score = None    # until this call finds a path
        kept, cand, gaps = self._trellis(time_groups)
        chosen, score = self._viterbi(cand, gaps, self.step_weights(), {})
        if chosen is None:
            return []
        self.last_path_score = score
        out: List[MusicalEvent] = []
        for t, g2 in enumerate(kept):
            f = cand[t][chosen[t]]
            for i, ev in enumerate(g2):
                ev.fret, ev.string = f[i].fret, f[i].string
            self._report_no_fit(g2, f)
            out.extend(g2)
        return out

    def map_paths_for_weights(self, time_groups: List[List[MusicalEvent]],
                              weight_vectors: List[Tuple[float, ...]]):
        """The best path under each weight vector, from ONE feature pass: the trellis is
        built once and step features are memoised across all the vectors (research use:
        knob sweeps, weight fits). Returns, per vector, (fingerings per kept group, path
        score, kept groups). Structural settings come from this mapper's config and are
        shared by every vector: sweet-spot bounds, the unplayable span, ignore-open, the
        diagonal-span flag and whether let-ring is on at all (the second-order gate), so
        a vector that turns let-ring on or off against the config is not a faithful
        stand-in for a mapper built with that config. Weights are the exchange rates:
        span, position, barre, travel, string switch, ringing, fretted-open. Events are
        not written back."""
        kept, cand, gaps = self._trellis(time_groups)
        memo: dict = {}
        results = []
        for w in weight_vectors:
            chosen, score = self._viterbi(cand, gaps, tuple(w), memo)
            path = None if chosen is None else [cand[t][chosen[t]] for t in range(len(kept))]
            results.append((path, score, kept))
        return results

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
