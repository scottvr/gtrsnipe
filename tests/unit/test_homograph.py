"""Tab homographs: one tab, a different song per tuning (gtrsnipe.guitar.homograph).

The core claim under test: songs A and B share a tab on an N-string, F-fret
neck iff their aligned notes split into <= N classes of constant interval
b - a (one note at a time per class, span <= F). Property tests build a random
tab + tunings, decode both songs, and require the solver to recover it.
"""
import random

import pytest

from gtrsnipe.core.config import MapperConfig
from gtrsnipe.core.theory import note_name_to_pitch, pitch_to_note_name
from gtrsnipe.core.types import MusicalEvent, Song, Track
from gtrsnipe.formats.tab.parser import AsciiTabParser
from gtrsnipe.guitar import homograph as hg

STD = MapperConfig()                                 # STANDARD, 24 frets

OLDMAC = "C4 C4 C4 G3 A3 A3 G3:2 E4 E4 D4 D4 C4:2"
TWINKLE = "C4 C4 G4 G4 A4 A4 G4:2 F4 F4 E4 E4 D4"
MARY = "E4 D4 C4 D4 E4 E4 E4:2"
TWINKLE7 = "C4 C4 G4 G4 A4 A4 G4:2"


def song(spec, title="s"):
    return hg.parse_inline(spec, title)


def pitches_by_onset(s: Song):
    evs = sorted((e for t in s.tracks for e in t.events), key=lambda e: (e.time, e.pitch))
    return [e.pitch for e in evs]


def decode_text(text: str, sol: hg.Solution, j: int):
    """Independent round trip: re-parse the rendered ASCII tab in song j's tuning."""
    parsed = AsciiTabParser.parse(text, open_string_pitches=sol.opens[j])
    return pitches_by_onset(parsed)


def _random_tab(rng, T, N, F, chords=False):
    """A random tab (string, fret per note) plus two random tunings; returns the
    two songs it spells and the tunings (high->low)."""
    opens = [[rng.randint(40, 70) for _ in range(N)] for _ in range(2)]
    ev_a, ev_b, t = [], [], 0.0
    for _ in range(T):
        k = rng.randint(1, min(3, N)) if chords else 1
        for s in rng.sample(range(N), k):
            f = rng.randint(0, F)
            ev_a.append(MusicalEvent(t, opens[0][s] + f, 1.0, 100, string=s, fret=f))
            ev_b.append(MusicalEvent(t, opens[1][s] + f, 1.0, 100))
        t += 1.0
    return (Song(tracks=[Track(events=ev_a)], title="A"),
            Song(tracks=[Track(events=ev_b)], title="B"), opens)


# -- the theorem -------------------------------------------------------------------

@pytest.mark.parametrize("seed", range(60))
def test_any_tab_pair_is_recovered_free_mode(seed):
    rng = random.Random(seed)
    N, F = rng.randint(3, 7), rng.choice([0, 3, 12, 24])
    a, b, _ = _random_tab(rng, rng.randint(1, 14), N, F)
    rep = hg.analyze([a, b], max_fret=F, max_strings=N)
    assert rep.alignment.ok
    assert rep.rank <= N                              # the lower bound can't exceed a witness
    assert rep.free is not None and rep.free_needed <= N   # exact for melodies


@pytest.mark.parametrize("seed", range(25))
def test_anchored_search_is_complete(seed):
    # The original tab is a witness in tuning A, so anchoring to A must succeed,
    # and the rendered text must decode to both songs.
    rng = random.Random(1000 + seed)
    N, F = 6, rng.choice([5, 12])
    a, b, opens = _random_tab(rng, rng.randint(2, 10), N, F)
    anchor = MapperConfig(tuning="CUSTOM", num_strings=N, max_fret=F,
                          custom_tuning=tuple(pitch_to_note_name(p) for p in reversed(opens[0])))
    rep = hg.analyze([a, b], anchor=anchor, max_fret=F, max_strings=N, transpose="keep",
                     transpose_a="keep", string_physics=False)
    sol = rep.anchored
    assert sol is not None, rep.anchored_reason
    assert sol.opens[0] == opens[0]                   # anchored: A's tuning untouched
    text = hg.render_tab(rep, sol)
    assert decode_text(text, sol, 0) == pitches_by_onset(a)
    assert decode_text(text, sol, 1) == pitches_by_onset(b)


@pytest.mark.parametrize("seed", range(25))
def test_a_real_tab_is_eligible_as_written(seed):
    rng = random.Random(2000 + seed)
    a, b, opens = _random_tab(rng, rng.randint(2, 12), 6, 12)
    rep = hg.analyze([a, b], max_fret=12, max_strings=6, transpose="keep",
                     tab_tuning=opens[0])
    sol = rep.as_written
    assert sol is not None, rep.as_written_reason
    for s, used in enumerate(sol.used):               # recovers the very tunings used
        if used:
            assert sol.opens[0][s] == opens[0][s] and sol.opens[1][s] == opens[1][s]


def test_as_written_rejects_a_string_with_two_intervals():
    # Standard tab: both notes on the high e string, but B moves them by
    # different amounts -> that fingering can't be retuned into B.
    a = Song(tracks=[Track(events=[MusicalEvent(0, 64, 1, 100, string=0, fret=0),
                                   MusicalEvent(1, 65, 1, 100, string=0, fret=1)])])
    b = song("E4 G4")                                  # intervals 0, +2
    rep = hg.analyze([a, b], tab_tuning=[64, 59, 55, 50, 45, 40])
    assert rep.as_written is None
    assert "string 1 carries 2 different intervals" in rep.as_written_reason


def test_chord_tabs_verify_whenever_solved():
    # Chord pairing is a heuristic (melodies are exact), but anything it solves
    # must still verify (analyze() raises on a verification failure).
    for seed in range(40):
        rng = random.Random(3000 + seed)
        a, b, _ = _random_tab(rng, rng.randint(1, 8), 6, 12, chords=True)
        rep = hg.analyze([a, b], max_fret=12, max_strings=12)
        assert rep.alignment.ok


# -- rank ----------------------------------------------------------------------------

def test_rank_counts_distinct_intervals():
    rep = hg.analyze([song(MARY), song(TWINKLE7)])
    assert [s.key[0] for s in rep.slots] == [-4, -2, 7, 5, 5, 5, 3]
    assert rep.rank == 5
    assert hg.rank(song(MARY), song(TWINKLE7)) == 5


def test_rank_is_transposition_invariant():
    up7 = " ".join(pitch_to_note_name(note_name_to_pitch(n) + 7) for n in TWINKLE7.split()[:-1])
    up7 += " " + pitch_to_note_name(note_name_to_pitch("G4") + 7) + ":2"
    assert hg.rank(song(MARY), song(up7)) == hg.rank(song(MARY), song(TWINKLE7))


def test_transposition_is_rank_one_and_flagged_trivial():
    rep = hg.analyze([song("C4 D4 E4"), song("G4 A4 B4")], anchor=STD)
    assert rep.rank == 1
    assert "transpositions of each other" in hg.format_report(rep)


def test_open_string_solver_is_the_zero_fret_case():
    # F = 0: each string holds one pitch pair, so strings = distinct (a, b) pairs.
    a, b = song(MARY), song(TWINKLE7)
    rep = hg.analyze([a, b], max_fret=0)
    pairs = {s.pitches for s in rep.slots}
    assert rep.free_needed == len(pairs)
    assert all(f == 0 for _, f in rep.free.positions)


def test_octave_folding_lowers_rank_and_counts_displacements():
    plain = hg.analyze([song(OLDMAC), song(TWINKLE)])
    folded = hg.analyze([song(OLDMAC), song(TWINKLE)], octaves=True)
    assert plain.rank == 5 and folded.rank == 4
    assert folded.displaced[1] > 0
    assert all(abs(k[0]) < 12 for k in folded.classes)


def test_three_songs_share_one_tab():
    oldmac7 = "C4 C4 C4 G3 A3 A3 G3:2"
    rep = hg.analyze([song(oldmac7), song(TWINKLE7), song(MARY)], anchor=STD)
    assert rep.alignment.ok and rep.anchored is not None
    text = hg.render_tab(rep, rep.anchored)
    for j, spec in enumerate([oldmac7, TWINKLE7, MARY]):
        want = [p + rep.anchored.shifts[j] for p in pitches_by_onset(song(spec))]
        assert decode_text(text, rep.anchored, j) == want
    assert text.count("//   Key ") == 3


# -- alignment -----------------------------------------------------------------------

def test_alignment_rejects_different_lengths():
    rep = hg.analyze([song("C4 D4 E4"), song("C4 D4")])
    assert not rep.alignment.ok
    assert "3 onsets" in rep.alignment.reason and "first 2" in rep.alignment.reason
    assert "NOT ALIGNED" in hg.format_report(rep)


def test_alignment_rejects_chord_shape_mismatch():
    rep = hg.analyze([song("C4 D4+F4"), song("C4 D4")])
    assert not rep.alignment.ok and "onset 2" in rep.alignment.reason


def test_rhythm_strict_vs_sequence():
    a, b = song("C4 D4 E4"), song("C4 D4:2 E4")
    assert not hg.analyze([a, b]).alignment.ok
    rep = hg.analyze([a, b], rhythm="sequence")
    assert rep.alignment.ok and rep.alignment.rhythm == "sequence-only"


def test_proportional_rhythm_counts_as_same_rhythm():
    rep = hg.analyze([song("C4 D4:2 E4"), song("E4:1/2 F4 G4:1/2")])
    assert rep.alignment.ok and rep.alignment.rhythm == "proportional"


# -- chords --------------------------------------------------------------------------

def test_chord_voices_pair_to_reuse_existing_classes():
    # Singletons establish intervals {+4, -5}; the chord C4+G4 vs D4+E4 pairs
    # low-with-low as {+2, -3} (two new classes) but crossed as {+4, -5} (none).
    rep = hg.analyze([song("C4 G4 C4+G4"), song("E4 D4 D4+E4")])
    assert rep.rank == 2
    assert set(rep.classes) == {(4,), (-5,)}


# -- anchored ------------------------------------------------------------------------

def test_oldmac_twinkle_standard_tab_round_trips():
    rep = hg.analyze([song(OLDMAC, "oldmac"), song(TWINKLE, "twinkle")], anchor=STD,
                     octaves=True)
    sol = rep.anchored
    assert sol is not None
    assert sol.opens[0] == [64, 59, 55, 50, 45, 40]              # it IS a standard tab
    text = hg.render_tab(rep, sol)
    assert "// Tuning: E2,A2,D3,G3,B3,E4" in text
    assert AsciiTabParser.header_tuning(text) == sol.opens[0]    # parses as plain A
    assert decode_text(text, sol, 0) == pitches_by_onset(song(OLDMAC))
    want_b = [s.pitches[1] + sol.shifts[1] for s in rep.slots]   # (octave-folded) B
    assert decode_text(text, sol, 1) == want_b
    # physically plausible: every retuned string stays within its gauge's limits
    assert sol.regauges() == 0


def test_anchored_rank_exceeds_strings():
    a = song("C4 D4 E4 F4 G4 A4 B4")
    b = song("C4 E4 G4 B4 D5 F5 A5")                  # 7 distinct intervals
    rep = hg.analyze([a, b], anchor=STD)
    assert rep.anchored is None and "rank 7 > 6 strings" in rep.anchored_reason
    assert rep.free is not None                       # fine with 7 free strings


def test_anchored_out_of_range_note():
    rep = hg.analyze([song("C1 D1"), song("C1 E1")], anchor=STD)
    assert rep.anchored is None and "out of range" in rep.anchored_reason


def test_anchored_hall_diagnosis_names_the_bottleneck():
    # Open strings only: E4 is reachable on the high e string alone, but its two
    # notes need different intervals (+1, +3) -> two classes, one string.
    cfg = MapperConfig(max_fret=0)
    rep = hg.analyze([song("E4 E4"), song("F4 G4")], anchor=cfg, max_fret=0)
    assert rep.anchored is None
    assert "need 2 string(s)" in rep.anchored_reason and "E4" in rep.anchored_reason


def test_max_retune_is_honored_or_reported():
    rep = hg.analyze([song(OLDMAC), song(TWINKLE)], anchor=STD, octaves=True, max_retune=4)
    assert rep.anchored is not None
    assert all(abs(d) <= 4 for d in rep.anchored.retunes(1))
    tight = hg.analyze([song(OLDMAC), song(TWINKLE)], anchor=STD, octaves=True, max_retune=1)
    assert tight.anchored is None and "within ±1" in tight.anchored_reason


def test_keep_transpose_holds_b_in_its_key():
    rep = hg.analyze([song(MARY), song(TWINKLE7)], anchor=STD, transpose="keep")
    assert rep.anchored.shifts[1] == 0       # B holds its key (A may still move)
    rep = hg.analyze([song(MARY), song(TWINKLE7)], anchor=STD, transpose="keep",
                     transpose_a="keep")
    assert rep.anchored.shifts == [0, 0]


def test_neutral_tab_privileges_no_song():
    rep = hg.analyze([song(OLDMAC), song(TWINKLE)], anchor=STD, octaves=True)
    sol = rep.anchored
    text = hg.render_tab(rep, sol, neutral=True)
    assert "// Tuning:" not in text and AsciiTabParser.header_tuning(text) is None
    tab_lines = [ln for ln in text.splitlines() if "|" in ln and not ln.startswith("//")]
    assert [ln.split("|")[0] for ln in tab_lines[:6]] == ["1", "2", "3", "4", "5", "6"]
    assert decode_text(text, sol, 0) == pitches_by_onset(song(OLDMAC))


# -- inline melodies -------------------------------------------------------------------

def test_parse_inline_notes_chords_rests_durations():
    s = hg.parse_inline("C4, E4:1/2 r:1/2 C3+G3:2 Bb3:1.5")
    got = [(e.time, pitch_to_note_name(e.pitch), e.duration) for e in s.tracks[0].events]
    assert got == [(0.0, "C4", 1.0), (1.0, "E4", 0.5), (2.0, "C3", 2.0),
                   (2.0, "G3", 2.0), (4.0, "Bb3", 1.5)]


def test_parse_inline_rejects_garbage():
    with pytest.raises(ValueError):
        hg.parse_inline("C4 H9")
    with pytest.raises(ValueError):
        hg.parse_inline("r r")
    for bad in ("C4 D4:1/0", "C4:0 D4"):            # review: crashed / fused into a chord
        with pytest.raises(ValueError):
            hg.parse_inline(bad)


def test_parse_inline_enharmonic_octaves():
    # review: Cb4 came out as B4 (an octave high), B#3 as C3
    s = hg.parse_inline("Cb4 B#3")
    assert [e.pitch for e in s.tracks[0].events] == [59, 60]


# -- CLI ---------------------------------------------------------------------------------

def _run_cli(argv, capsys):
    from gtrsnipe.arguments import setup_parser
    from gtrsnipe.converter import run_homograph
    args = setup_parser().parse_args(argv)
    code = run_homograph(args)
    return code, capsys.readouterr().out


def test_cli_writes_a_tab_that_decodes_per_key(tmp_path, capsys):
    out = tmp_path / "shared.tab"
    code, text = _run_cli(["--homograph", OLDMAC, TWINKLE, "--homograph-octaves",
                           "-o", str(out)], capsys)
    assert code == 0
    assert "Anchored   ELIGIBLE - an ordinary STANDARD tab" in text and "Verified" in text
    tab_text = out.read_text()
    keys = [ln.split("Key ")[1].split()[1] for ln in tab_text.splitlines() if "//   Key " in ln]
    a = [note_name_to_pitch(n) for n in keys[0].split(",")][::-1]
    assert pitches_by_onset(AsciiTabParser.parse(tab_text, open_string_pitches=a)) \
        == pitches_by_onset(song(OLDMAC))


def test_cli_reads_files_and_reports_ineligible(tmp_path, capsys):
    abc = tmp_path / "a.abc"
    abc.write_text("X:1\nT:a\nM:4/4\nL:1/4\nK:C\nC D E F|\n")
    code, text = _run_cli(["--homograph", str(abc), "C4 D4 E4"], capsys)
    assert code == 1 and "NOT ALIGNED" in text


def test_cli_rejects_non_tab_output(tmp_path, capsys):
    code, _ = _run_cli(["--homograph", MARY, TWINKLE7, "-o", str(tmp_path / "x.mid")], capsys)
    assert code == 1


def test_save_args_never_persists_the_songs(tmp_path):
    from gtrsnipe.arguments import apply_profiles, setup_parser
    apply_profiles(setup_parser(), ["--homograph", "a.mid", "b.mid", "--homograph-octaves",
                                    "--save-args", "hp", "--config-dir", str(tmp_path)])
    saved = (tmp_path / "hp").read_text()
    assert "homograph-octaves" in saved and "a.mid" not in saved


# -- physics in the solver ---------------------------------------------------------------

def test_meeting_in_the_middle_avoids_restringing():
    # Without octave folding the +12 class forces one string far up in anchored
    # mode (a restring); letting both tunings move ("middle") needs none.
    rep = hg.analyze([song(OLDMAC), song(TWINKLE)], anchor=STD)
    assert rep.anchored is not None and rep.anchored.regauges() >= 1
    assert rep.middle is not None and rep.middle.regauges() == 0
    assert rep.middle.opens[0] != [64, 59, 55, 50, 45, 40]      # A retuned too
    text = hg.render_tab(rep, rep.middle)
    assert decode_text(text, rep.middle, 0) == pitches_by_onset(song(OLDMAC))
    want_b = [s.pitches[1] + rep.middle.shifts[1] for s in rep.slots]
    assert decode_text(text, rep.middle, 1) == want_b
    report = hg.format_report(hg.analyze([song(OLDMAC), song(TWINKLE)], anchor=STD,
                                         mode="middle"))
    assert "Middle     ELIGIBLE" in report and "gauge" in report


def test_report_flags_a_string_that_would_break():
    rep = hg.analyze([song(OLDMAC), song(TWINKLE)], anchor=STD)
    text = hg.format_report(rep)
    assert "! string" in text and "restring with" in text


def test_song_a_is_transposed_only_when_needed():
    # Open strings only (max_fret 0): F4 isn't an open string, but a semitone
    # down (E4, B3) both are -- so A must move to fit the instrument at all.
    cfg = MapperConfig(max_fret=0)
    rep = hg.analyze([song("F4 C4"), song("G4 E4")], anchor=cfg, max_fret=0)
    assert rep.anchored is not None and rep.anchored.shifts[0] == -1
    keep = hg.analyze([song("F4 C4"), song("G4 E4")], anchor=cfg, max_fret=0,
                      transpose_a="keep")
    assert keep.anchored is None and "out of range" in keep.anchored_reason
    easy = hg.analyze([song(MARY), song(TWINKLE7)], anchor=STD)
    assert easy.anchored.shifts[0] == 0 or easy.anchored.regauges() == 0


# -- re-rhythming ------------------------------------------------------------------------

def test_rhythm_slop_ratio():
    a, b = song("C4 D4 E4 F4"), song("E4:1.5 F4:1/2 G4 A4")
    assert not hg.analyze([a, b]).alignment.ok
    assert not hg.analyze([a, b], rhythm=1.5).alignment.ok      # 1 vs 1/2 is x2
    rep = hg.analyze([a, b], rhythm=2)
    assert rep.alignment.ok and rep.alignment.rhythm == "loose"
    assert "worst x2.00" in rep.alignment.detail


def test_subdivide_smears_repeated_notes():
    # "ta ta ta" vs "ti ti ta ta": B's repeated E4 E4 becomes one held note.
    a, b = song("C4 D4 E4"), song("E4:1/2 E4:1/2 F4 G4")
    assert not hg.analyze([a, b]).alignment.ok
    rep = hg.analyze([a, b], subdivide=2)
    assert rep.alignment.ok and len(rep.alignment.onsets) == 3
    assert any("smeared" in e for e in rep.alignment.edits)
    assert [s.pitches for s in rep.slots] == [(60, 64), (62, 65), (64, 67)]


def test_subdivide_restrikes_when_pitches_differ():
    # A's one C4 must cover B's E4 F4 -> A is re-struck (disclosed).
    rep = hg.analyze([song("C4 D4"), song("E4:1/2 F4:1/2 G4")], subdivide=2)
    assert rep.alignment.ok and len(rep.alignment.onsets) == 3
    assert any("re-struck x2" in e for e in rep.alignment.edits)
    assert [s.pitches for s in rep.slots] == [(60, 64), (60, 65), (62, 67)]


def test_subdivide_keeps_song_a_intact():
    # B's one E4 against A's C4 D4: B's note is re-struck, A untouched.
    rep = hg.analyze([song("C4:1/2 D4:1/2 E4"), song("E4 G4")], subdivide=2, anchor=STD)
    assert [s.pitches[0] for s in rep.slots] == [60, 62, 64]
    sol = rep.anchored
    text = hg.render_tab(rep, sol)
    assert decode_text(text, sol, 0) == [60, 62, 64]
    assert "Re-rhythmed:" in text


def test_unaligned_hint_mentions_subdivide():
    rep = hg.analyze([song("C4 D4 E4"), song("C4 D4")])
    assert "--homograph-subdivide" in rep.alignment.reason


# -- review regressions: solver -------------------------------------------------------------

@pytest.mark.parametrize("seed", range(20))
def test_middle_is_a_superset_of_anchored(seed):
    # review: middle required each string to hold a class's WHOLE span, so it
    # rejected (with a false "out of range") pairs anchored mode solved.
    rng = random.Random(4000 + seed)
    std = [64, 59, 55, 50, 45, 40]
    delta = [rng.randint(-3, 2) for _ in range(6)]
    a_ev, b_ev = [], []
    for t in range(rng.randint(3, 9)):
        s, f = rng.randrange(6), rng.randint(0, 12)
        a_ev.append(MusicalEvent(t, std[s] + f, 1, 100))
        b_ev.append(MusicalEvent(t, std[s] + delta[s] + f, 1, 100))
    rep = hg.analyze([Song(tracks=[Track(events=a_ev)]), Song(tracks=[Track(events=b_ev)])],
                     anchor=STD, max_fret=12)
    if rep.anchored is not None:
        assert rep.middle is not None, rep.middle_reason


def test_middle_handles_a_class_wider_than_one_string():
    rep = hg.analyze([song("E2 G3 A4"), song("E2 F#3 A4")], anchor=STD, mode="middle")
    assert rep.middle is not None
    assert "out of range" not in rep.middle_reason


def test_as_written_respects_max_fret_and_never_crashes(tmp_path):
    a = Song(tracks=[Track(events=[MusicalEvent(0, 64, 1, 100, string=0, fret=0),
                                   MusicalEvent(1, 79, 1, 100, string=0, fret=15)])])
    rep = hg.analyze([a, song("F4 G#5")], anchor=STD, max_fret=12,
                     tab_tuning=[64, 59, 55, 50, 45, 40])        # used to raise
    assert rep.as_written is None and "fret 15" in rep.as_written_reason
    assert rep.anchored is not None                               # the requested mode stands


def test_free_packing_is_fast_and_exact_for_a_wide_melody():
    # review: 11 chromatic notes at max_fret 0 took 70 s and claimed ">64 strings"
    import time
    a = song("C4 C#4 D4 D#4 E4 F4 F#4 G4 G#4 A4 A#4")
    b = song("D4 D#4 E4 F4 F#4 G4 G#4 A4 A#4 B4 C5")
    t0 = time.perf_counter()
    rep = hg.analyze([a, b], max_fret=0, max_strings=12, physical=False)
    assert time.perf_counter() - t0 < 2.0
    assert rep.free is not None and rep.free_needed == 11


# -- review regressions: alignment ------------------------------------------------------------

def _al(a, b, **kw):
    ev = lambda spec: [e for t in song(spec).tracks for e in t.events]   # noqa: E731
    return hg.align([ev(a), ev(b)], **kw)


def test_dp_finds_the_tempo_scale_when_the_split_is_at_the_end():
    # review: c was guessed from the LAST onsets, which a final split skews
    al = _al("C4 D4 E4 F4", "E4:2 F4:2 G4:2 A4:1 A4:1", subdivide=2)
    assert al.ok and al.rhythm == "proportional" and al.detail == "x2"
    assert any("smeared" in e for e in al.edits)


def test_final_restrikes_follow_the_rhythm_not_the_last_notes_length():
    # review: B's held final C5 squeezed A's re-strike into a 1/9-beat flam
    for tail in ("C5:4", "C5:1/2"):
        al = _al("C4 D4 E4 C4", f"E4 F4 G4 A4:1/2 {tail}", subdivide=2)
        assert [(o.time, o.duration) for o in al.onsets[-2:]] == [(3.0, 0.5), (3.5, 0.5)]


def test_subdivide_never_loses_a_one_to_one_alignment():
    # review: turning subdivide on made an aligned proportional pair NOT ALIGNED
    for sub in (1, 2):
        al = _al("C4 D4 E4 F4", "E4:2.125 F4:1.75 G4:2.125 A4:2", subdivide=sub)
        assert al.ok and al.rhythm == "proportional" and not al.edits


def test_strict_rejects_drifting_onsets():
    # review: strict fell into the ratio loop -> "loose ... worst x1.00 at onset 0"
    al = _al("C4 D4 E4 F4 G4", "E4:2.125 F4:2.125 G4:1.875 A4:1.875 B4:2")
    assert not al.ok and "onset 3" in al.reason
    loose = _al("C4 D4 E4 F4 G4", "E4:2.125 F4:2.125 G4:1.875 A4:1.875 B4:2", rhythm=1.2)
    assert loose.ok and "onset 0" not in loose.detail


def test_rhythm_labels_are_consistent():
    # review: sequence mode called an exact pair "rhythms differ"; x2+edits lost "x2"
    seq = _al("C4 D4 E4 F4", "E4:2.125 F4:1.875 G4:2 A4:2", rhythm="sequence", subdivide=2)
    assert seq.ok and seq.rhythm == "proportional"
    rep = hg.analyze([song("C4 D4 E4"), song("E4:1 E4:1 F4:2 G4:2")], subdivide=2)
    assert "another note value (x2)" in hg.format_report(rep)
