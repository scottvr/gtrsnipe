"""Tests for the Viterbi/DP fretboard mapper (Epic B).

Covers: candidate enumeration, global-optimality vs brute force (first- and
second-order), the >=-greedy guarantee, determinism, and the _normalize_pitch
dedupe regression.
"""
import copy
import itertools
from itertools import groupby

import pytest

from gtrsnipe.core.config import MapperConfig
from gtrsnipe.core.types import FretPosition, MusicalEvent
from gtrsnipe.guitar.mapper import GuitarMapper


def ev(time, pitch):
    return MusicalEvent(time=time, pitch=pitch, duration=0.5, velocity=100)


def make_mapper(**overrides):
    return GuitarMapper(MapperConfig(tuning="STANDARD", num_strings=6, **overrides))


def _groups(mapper, events):
    qr = mapper.config.quantization_resolution
    q = lambda b: round(b / qr) * qr
    se = sorted(events, key=lambda e: e.time)
    return [list(g) for _, g in groupby(se, key=lambda e: q(e.time))]


def total_J(mapper, fingerings):
    """Realized objective along a chosen fingering sequence (same formula both
    optimizers accumulate: score(f_t, f_{t-1}, f_{t-2}))."""
    sc = mapper._score_fingering
    J = 0.0
    for t, f in enumerate(fingerings):
        prev = fingerings[t - 1] if t >= 1 else None
        pp = fingerings[t - 2] if t >= 2 else None
        J += sc(f, prev, pp)
    return J


def realized_fingerings(mapper, mapped_events):
    out = []
    for g in _groups(mapper, mapped_events):
        if any(e.string is None for e in g):
            continue  # dead-end group, not emitted
        out.append(tuple(FretPosition(e.string, e.fret) for e in g))
    return out


def brute_force_best_J(mapper, events):
    cand = []
    for g in _groups(mapper, events):
        cs = mapper.generate_candidates(mapper._preprocess_group(g))
        if cs:
            cand.append(cs)
    best = None
    for seq in itertools.product(*cand):
        J = total_J(mapper, list(seq))
        if best is None or J > best:
            best = J
    return best


# A short melody whose pitches each have several fretboard positions.
MELODY = [ev(0, 64), ev(1, 65), ev(2, 67), ev(3, 69)]

# A DISCRIMINATING line: an awkward wide-interval melody where greedy's local
# choices are strictly worse than the global optimum, so these fixtures can tell
# a real Viterbi apart from a trivial "pick the first candidate" stub.
# (Verified: first-order brute=greedy? NO — brute=-24, greedy=-36.)
DISCRIMINATING = [ev(0, 63), ev(1, 72), ev(2, 62), ev(3, 63)]

ALL_MELODIES = [MELODY, DISCRIMINATING]


def test_generate_candidates_are_distinct_string_and_sorted():
    mapper = make_mapper()
    chord = [ev(0, 40), ev(0, 47), ev(0, 52)]  # a 3-note chord
    cands = mapper.generate_candidates(chord)
    assert cands, "expected at least one valid fingering"
    for f in cands:
        strings = [p.string for p in f]
        assert len(set(strings)) == len(strings), "fingering reuses a string"
    # deterministic sorted order
    assert cands == sorted(cands, key=mapper._cand_key)


def test_default_optimizer_is_viterbi():
    assert MapperConfig().optimizer == "viterbi"


@pytest.mark.parametrize("melody", ALL_MELODIES)
def test_viterbi_matches_bruteforce_first_order(melody):
    mapper = make_mapper()  # default: first-order (no let_ring/diagonal)
    best = brute_force_best_J(mapper, copy.deepcopy(melody))
    mapped = mapper.map_events_to_fretboard(copy.deepcopy(melody), no_articulations=True)
    got = total_J(mapper, realized_fingerings(mapper, mapped))
    assert got == pytest.approx(best), f"viterbi J={got} != brute-force optimum {best}"


@pytest.mark.parametrize("melody", ALL_MELODIES)
def test_second_order_matches_bruteforce(melody):
    mapper = make_mapper(let_ring_bonus=1.0, diagonal_span_penalty=True)
    best = brute_force_best_J(mapper, copy.deepcopy(melody))
    mapped = mapper.map_events_to_fretboard(copy.deepcopy(melody), no_articulations=True)
    got = total_J(mapper, realized_fingerings(mapper, mapped))
    assert got == pytest.approx(best), f"pair-state J={got} != brute-force optimum {best}"


@pytest.mark.parametrize("melody", ALL_MELODIES)
def test_viterbi_at_least_greedy(melody):
    g_mapper = make_mapper(optimizer="greedy")
    v_mapper = make_mapper(optimizer="viterbi")
    g_out = g_mapper.map_events_to_fretboard(copy.deepcopy(melody), no_articulations=True)
    v_out = v_mapper.map_events_to_fretboard(copy.deepcopy(melody), no_articulations=True)
    g_J = total_J(g_mapper, realized_fingerings(g_mapper, g_out))
    v_J = total_J(v_mapper, realized_fingerings(v_mapper, v_out))
    assert v_J >= g_J - 1e-9, f"viterbi J={v_J} < greedy J={g_J}"


def test_viterbi_strictly_beats_greedy_on_hard_line():
    """A discriminating case: the global optimum is strictly better than greedy,
    so this fails against a trivial 'first candidate' stub (see review finding)."""
    g_mapper = make_mapper(optimizer="greedy")
    v_mapper = make_mapper(optimizer="viterbi")
    best = brute_force_best_J(v_mapper, copy.deepcopy(DISCRIMINATING))
    g_out = g_mapper.map_events_to_fretboard(copy.deepcopy(DISCRIMINATING), no_articulations=True)
    v_out = v_mapper.map_events_to_fretboard(copy.deepcopy(DISCRIMINATING), no_articulations=True)
    g_J = total_J(g_mapper, realized_fingerings(g_mapper, g_out))
    v_J = total_J(v_mapper, realized_fingerings(v_mapper, v_out))
    assert v_J == pytest.approx(best), f"viterbi J={v_J} != optimum {best}"
    assert v_J > g_J + 1e-9, f"expected viterbi to strictly beat greedy, got v={v_J} g={g_J}"


def test_viterbi_is_deterministic():
    m1 = make_mapper()
    m2 = make_mapper()
    out1 = m1.map_events_to_fretboard(copy.deepcopy(MELODY), no_articulations=True)
    out2 = m2.map_events_to_fretboard(copy.deepcopy(MELODY), no_articulations=True)
    pos1 = [(e.string, e.fret) for e in out1]
    pos2 = [(e.string, e.fret) for e in out2]
    assert pos1 == pos2


def test_dedupe_path_does_not_crash():
    # Regression: _normalize_pitch was called but never defined -> AttributeError.
    mapper = make_mapper(deduplicate_pitches=True)
    chord = [ev(0, 64), ev(0, 64), ev(0, 67)]  # duplicate pitch in a chord
    out = mapper.map_events_to_fretboard(chord, no_articulations=True)
    assert out, "dedupe path should still map notes"
    assert all(e.string is not None and e.fret is not None for e in out)


def test_viterbi_handles_chords_matches_bruteforce():
    # Two multi-note chords -> exercises multi-note candidate generation + DP,
    # not just the monophonic path.
    mapper = make_mapper()
    events = [ev(0, 40), ev(0, 47), ev(0, 52),   # E2 B2 E3
              ev(1, 45), ev(1, 52), ev(1, 57)]   # A2 E3 A3
    best = brute_force_best_J(mapper, copy.deepcopy(events))
    mapped = mapper.map_events_to_fretboard(copy.deepcopy(events), no_articulations=True)
    got = total_J(mapper, realized_fingerings(mapper, mapped))
    assert got == pytest.approx(best), f"chord viterbi J={got} != optimum {best}"


def test_empty_input_returns_empty():
    assert make_mapper().map_events_to_fretboard([], no_articulations=True) == []


# -- H08: the tests the design doc promised --------------------------------------------

FLAT = dict(fret_span_penalty=0.0, movement_penalty=0.0, string_switch_penalty=0.0,
            high_fret_penalty=0.0, sweet_spot_bonus=0.0, fretted_open_penalty=0.0)


def test_an_exact_tie_goes_to_the_lexicographically_smallest_path():
    """With every weight at zero all paths score the same, so the tie-break alone
    decides: the smallest candidate (highest string, then lowest fret) at every
    stage (DESIGN-viterbi-mapper §5)."""
    mapper = make_mapper(**FLAT)
    notes = [ev(0.0, 64), ev(0.5, 67), ev(1.0, 69), ev(1.5, 64)]
    groups = _groups(mapper, notes)
    cands = [mapper.generate_candidates(g) for g in groups]
    assert all(len(c) > 1 for c in cands)                       # there is a choice at every stage
    scores = {mapper._score_fingering(f, p, None) for f in cands[1] for p in cands[0]}
    assert scores == {0.0}                                       # and it is a real tie
    mapped = mapper.map_multi_string(groups)
    assert [(e.string, e.fret) for e in mapped] == [min(GuitarMapper._cand_key(f) for f in c)[0]
                                                     for c in cands]
    assert mapper.last_path_score == 0.0


def _ungated_reads(source):
    """Lines where a scorer's source reads prev_prev_fingering outside an `if` on
    let_ring_bonus nested in one on diagonal_span_penalty (being in such an `if`'s own
    test counts, being in its `else` doesn't)."""
    import ast
    import textwrap
    fn = ast.parse(textwrap.dedent(source)).body[0]
    parent = {child: node for node in ast.walk(fn) for child in ast.iter_child_nodes(node)}
    bad = []
    for node in ast.walk(fn):
        if not (isinstance(node, ast.Name) and node.id == "prev_prev_fingering"):
            continue
        gates, child = "", node
        while child in parent:
            up = parent[child]
            if isinstance(up, ast.If) and child not in up.orelse:
                gates += ast.dump(up.test)
            child = up
        if not ("let_ring_bonus" in gates and "diagonal_span_penalty" in gates):
            bad.append(node.lineno)
    return bad


def test_the_scorer_reads_no_history_deeper_than_two_steps():
    """The landmine guard (DESIGN-viterbi-mapper §2.3). The DP's states carry at most
    the fingering two steps back, and only when let-ring and the diagonal span check
    are both on. If the scorer learns to look further back, or reads t-2 anywhere
    else, the search stops being exact: update `second_order` in map_multi_string
    and this test together."""
    import inspect
    source = inspect.getsource(GuitarMapper._score_fingering)
    params = list(inspect.signature(GuitarMapper._score_fingering).parameters)
    assert params == ["self", "fingering", "prev_fingering", "prev_prev_fingering"]
    assert "prev_prev_fingering:" in source                     # it is still read somewhere
    assert _ungated_reads(source) == []
    # the DP turns its pair-states on under exactly that gate
    dp = inspect.getsource(GuitarMapper.map_multi_string)
    assert "second_order = bool(self.config.diagonal_span_penalty and self.config.let_ring_bonus > 0)" in dp
    # the check itself catches a read outside the gate, or in a gate's else branch
    leak = "def f(self, fingering, prev_fingering, prev_prev_fingering):\n" \
           "    if prev_prev_fingering:\n        return 1\n    return 0\n"
    assert _ungated_reads(leak) == [2]
    half = "def f(self, fingering, prev_fingering, prev_prev_fingering):\n" \
           "    if self.config.diagonal_span_penalty:\n" \
           "        if self.config.let_ring_bonus > 0:\n            pass\n" \
           "        else:\n            return len(prev_prev_fingering)\n"
    assert _ungated_reads(half) == [6]


def test_hard_enum_cap_limits_candidates_and_says_so(caplog):
    """The safety valve: past the cap, enumeration stops, a warning says the group
    may be non-optimal, and the mapper still returns a fingering."""
    chord = [ev(0.0, p) for p in (52, 55, 59, 64)]               # E3 G3 B3 E4
    full = make_mapper().generate_candidates(chord)
    assert len(full) > 3
    capped = make_mapper(hard_enum_cap=3)
    with caplog.at_level("WARNING", logger="gtrsnipe.guitar.mapper"):
        some = capped.generate_candidates(chord)
    assert len(some) == 3 and set(some) <= set(full)
    assert some == sorted(some, key=GuitarMapper._cand_key)
    assert "hard_enum_cap (3) hit" in caplog.text
    mapped = capped.map_multi_string([chord])
    assert len(mapped) == 4 and len({e.string for e in mapped}) == 4


def test_a_reused_mapper_forgets_the_last_score():
    mapper = make_mapper()
    mapper.map_multi_string([[ev(0.0, 64)]])
    assert mapper.last_path_score is not None
    assert mapper.map_multi_string([]) == [] and mapper.last_path_score is None
    mapper.map_multi_string([[ev(0.0, 64)]])
    assert mapper.map_multi_string([[ev(0.0, 5)]]) == [] and mapper.last_path_score is None   # unplayable
