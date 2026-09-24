from dataclasses import dataclass
from itertools import product
from typing import Dict, Set, Optional, List, Tuple
from itertools import groupby
from ..core.types import MusicalEvent, FretPosition, Tuning, Technique
from ..core.config import MapperConfig
from ..core.theory import note_name_to_pitch
from collections import Counter

import logging

logger = logging.getLogger(__name__)

Fingering = Tuple[FretPosition, ...]

class GuitarMapper:
    def __init__(self, config: MapperConfig):
        self.config = config
        try:
            self.tuning = Tuning[self.config.tuning.upper()]
        except KeyError:
            logger.warning(f"Unknown tuning '{self.config.tuning}'. Defaulting to STANDARD.")
            self.tuning = Tuning.STANDARD
        self.open_string_pitches = [note_name_to_pitch(n) for n in self.tuning.value] 
        self.pitch_to_positions: Dict[int, Set[FretPosition]] = {}
        self._build_pitch_maps()
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

    def _score_fingering(self, fingering: Fingering, prev_fingering: Optional[Fingering], prev_prev_fingering: Optional[Fingering]) -> float:
        """Scores a fingering based on internal shape, position, and transition cost."""
        
        # 1. Internal Shape Score (Compactness)
        if self.config.ignore_open:
            frets = [pos.fret for pos in fingering if pos.fret > 0]
        else:
            frets = [pos.fret for pos in fingering]
        fret_span = (max(frets) - min(frets)) if frets else 0
        if fret_span > self.config.unplayable_fret_span:
            return -1000
        score = -fret_span * self.config.fret_span_penalty 

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
            score -= fret_diff * self.config.movement_penalty
            
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
                # silently breaks.
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
    
    
    def _find_optimal_fingering(self, notes: List[MusicalEvent], prev_fingering: Optional[Fingering], prev_prev_fingering: Optional[Fingering]) -> Optional[Fingering]:
        note_positions = []
        for note in notes:
            positions = self.pitch_to_positions.get(note.pitch)
            if not positions: return None
            note_positions.append(positions)

        all_combinations = product(*note_positions)
        best_fingering = None
        max_score = -float('inf')

        for fingering in all_combinations:
            strings_used = {pos.string for pos in fingering}
            if len(strings_used) != len(fingering):
                continue

            score = self._score_fingering(fingering, prev_fingering, prev_prev_fingering)
            
            logger.debug(f"considering score: {score} {fingering}")
            if score > max_score:
                max_score = score
                best_fingering = fingering
        logger.debug(f"best score: {max_score} {best_fingering}")
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
            pos = self.pitch_to_positions.get(n.pitch)
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
        sc = self._score_fingering

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
                    s = V[(NONE, i)] + sc(fj, fi, None)
                    st = (i, j)
                    if st not in Vn or s > Vn[st]:
                        Vn[st] = s
                        BP[1][st] = (NONE, i)
            V = Vn

        # stages t >= 2: ordered pair-state (f_{t-1}, f_t)
        for t in range(2, T):
            Vn = {}
            for k, fk in enumerate(cand[t]):
                for j, fj in enumerate(cand[t - 1]):
                    best_s = None
                    best_prev = None
                    if second_order:
                        for i, fi in enumerate(cand[t - 2]):
                            if (i, j) not in V:
                                continue
                            s = V[(i, j)] + sc(fk, fj, fi)   # fi is the TRUE f_{t-2}
                            if best_s is None or s > best_s:
                                best_s = s
                                best_prev = (i, j)
                    else:
                        # score is independent of f_{t-2}: pick best predecessor,
                        # then add the (t-2-independent) step cost once.
                        for i, _fi in enumerate(cand[t - 2]):
                            if (i, j) not in V:
                                continue
                            if best_s is None or V[(i, j)] > best_s:
                                best_s = V[(i, j)]
                                best_prev = (i, j)
                        if best_prev is not None:
                            best_s += sc(fk, fj, None)
                    if best_prev is None:
                        continue
                    Vn[(j, k)] = best_s
                    BP[t][(j, k)] = best_prev
            V = Vn

        if not V:
            return []

        # termination + traceback (store current-fingering index at each stage)
        end_state = max(sorted(V, key=lambda s: (s[0], s[1])), key=lambda s: V[s])
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
            out.extend(g2)
        return out

    def _map_multi_string_greedy(self, time_groups: List[List[MusicalEvent]]) -> List[MusicalEvent]:
        """Legacy greedy per-step mapping, kept behind --optimizer greedy."""
        multi_string_events = []
        last_fingering: Optional[Fingering] = None
        prev_prev_fingering: Optional[Fingering] = None

        for note_group in time_groups:
            group_to_finger = self._preprocess_group(note_group)
            fingering = self._find_optimal_fingering(group_to_finger, last_fingering, prev_prev_fingering)
            if fingering:
                for i, note_event in enumerate(group_to_finger):
                    note_event.fret = fingering[i].fret
                    note_event.string = fingering[i].string
                multi_string_events.extend(group_to_finger)
                prev_prev_fingering = last_fingering
                last_fingering = fingering
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
