"""The scoring-weights sweep (backlog M01): knobs, one run's metrics, distinct-tab
counts and breakpoints, the scale-invariance check, the probes and the CLI."""
import json

import pytest

from gtrsnipe.core.config import MapperConfig
from gtrsnipe.core.types import MusicalEvent, Song, Track
from gtrsnipe.research import sweep as SW
from gtrsnipe.research.cli import main as research_main


def line(pitches, beat=0.5):
    return Song(tracks=[Track(events=[MusicalEvent(i * beat, p, beat, 90)
                                      for i, p in enumerate(pitches)])])


def test_knob_ladders_contain_the_default():
    for key, k in SW.KNOBS.items():
        assert k.default in k.ladder, key
        assert len(set(k.ladder)) == len(k.ladder), key
        assert key == (k.alias or k.name)
    assert SW.KNOBS["sweet_spot_bonus@low4"].settings(2.0) == {"sweet_spot_low": 4, "sweet_spot_bonus": 2.0}


def test_fretted_open_penalty_needs_prefer_open():
    s = SW.KNOBS["fretted_open_penalty"].settings(40.0)
    assert s == {"prefer_open": True, "fretted_open_penalty": 40.0}


def test_configured_rejects_unknown_field():
    with pytest.raises(ValueError):
        SW.configured(MapperConfig(), no_such_knob=1)


def test_finger_counts_what_the_scorer_counts():
    # E4 then B4 then E4: a single-note string change counts 2 (symmetric difference)
    r = SW.finger(line([64, 71, 64]), MapperConfig())
    assert r.notes == r.placed == 3
    assert len(r.signature) == 3
    assert all(isinstance(s, int) and isinstance(f, int) for s, f in r.signature)
    assert r.score is not None
    assert r.switches % 2 == 0


def test_greedy_path_score_is_reported():
    r = SW.finger(line([64, 71, 64]), MapperConfig(optimizer="greedy"))
    assert r.score is not None


def test_unplayable_chosen_counts_spans_past_the_limit():
    # x-5-7-7-0-0: D3 A3 D4 with open B and E. With open strings counted in the span
    # no fingering fits 4 frets; the mapper places the chord anyway (the least bad of
    # them, ranked on the other terms) and the run counts it.
    chord = Song(tracks=[Track(events=[MusicalEvent(0, p, 2, 90) for p in (50, 57, 62, 59, 64)])])
    r = SW.finger(chord, MapperConfig())
    assert r.unplayable_chosen == 1
    assert r.max_span > 4
    r2 = SW.finger(chord, MapperConfig(ignore_open=True))
    assert r2.unplayable_chosen == 0
    assert r2.max_span <= 4


def test_sweep_song_breakpoints_and_dead_knobs():
    r = SW.sweep_song(line([64, 71, 64, 69, 64, 71]), "t",
                      knobs=["movement_penalty", "sweet_spot_bonus"])
    mv = r.knobs["movement_penalty"]
    assert mv.values[mv.default_index] == 3.0
    assert mv.runs[mv.default_index].signature == r.base.signature
    assert mv.distinct >= 1
    assert set(mv.breakpoints) <= set(mv.values[1:])
    assert 3.0 not in mv.differs_from_default
    assert r.knobs["sweet_spot_bonus"].distinct == 1          # idle: no lower edge, no case
    assert r.scale_invariant is True


def test_sweet_spot_bonus_in_its_context_is_live():
    song = line([45, 48, 50, 52, 55, 57, 60, 62, 64, 67, 64, 62, 60, 57, 55, 52, 50, 48, 45])
    r = SW.sweep_song(song, "run", knobs=["sweet_spot_bonus", "sweet_spot_bonus@low4"], check_scale=False)
    assert r.knobs["sweet_spot_bonus"].distinct == 1
    assert r.knobs["sweet_spot_bonus@low4"].distinct > 1


def test_scale_invariance_holds_on_the_probes():
    for label, song in SW.probes():
        if label == "probe:sus-slide":
            continue                                           # slow (5-note chords)
        r = SW.sweep_song(song, label, knobs=["prefer_open"])
        assert r.scale_invariant is True, label


def test_summary_verdicts():
    songs = [line([64, 71, 64, 69, 64, 71]), line([40, 64, 40, 64])]
    results = [SW.sweep_song(s, f"s{i}", knobs=["movement_penalty", "sweet_spot_bonus"])
               for i, s in enumerate(songs)]
    summ = {s.knob: s for s in SW.summarize(results)}
    assert summ["sweet_spot_bonus"].verdict == "idle"
    assert summ["sweet_spot_bonus"].live_songs == 0
    assert summ["movement_penalty"].songs == 2
    assert summ["movement_penalty"].distinct_total >= 2
    text = SW.format_summary(list(summ.values()), results)
    assert "sweet_spot_bonus" in text and "idle" in text
    assert "only ratios matter" in text


def test_probes_are_songs_with_notes():
    for label, song in SW.probes():
        assert label.startswith("probe:")
        assert song.tracks and song.tracks[0].events


def test_cli_sweep_writes_json_and_tabs(tmp_path, capsys):
    out = tmp_path / "r.json"
    tabs = tmp_path / "tabs"
    rc = research_main(["sweep", "C4 D4 E4 C4 G4", "--knobs", "movement_penalty,prefer_open",
                        "--json", str(out), "--tabs", str(tabs), "-v"])
    assert rc == 0
    rep = json.loads(out.read_text())
    assert [s["knob"] for s in rep["summary"]] == ["movement_penalty", "prefer_open"]
    assert rep["songs"][0]["scale_invariant"] is True
    assert any(p.name.endswith(".default.tab") for p in tabs.iterdir())
    text = capsys.readouterr().out
    assert "distinct tabs per knob" in text


def test_cli_sweep_rejects_unknown_knob(capsys):
    assert research_main(["sweep", "C4 D4", "--knobs", "nope"]) == 2
    assert "unknown knob" in capsys.readouterr().err


def test_pair_sweep_revives_the_sweet_spot_bonus():
    # dead at sweet_spot_low = 0 (no fingering can be below the window), live with an edge
    song = line([45, 48, 50, 52, 55, 57, 60, 62, 64, 67, 64, 62, 60, 57, 55, 52, 50, 48, 45])
    pr = SW.sweep_pair(song, "run", "sweet_spot_low", "sweet_spot_bonus")
    assert pr.a_values[0] == 0 and pr.distinct_b_at(0) == 1
    assert max(pr.distinct_b_at(i) for i in range(len(pr.a_values))) > 1
    d = pr.to_dict()
    assert d["distinct"] == pr.distinct and len(d["distinct_b_at_a"]) == len(pr.a_values)
    assert "distinct sweet_spot_bonus" in SW.format_pair(pr)


def test_cli_pair(tmp_path, capsys):
    out = tmp_path / "p.json"
    assert research_main(["sweep", "C4 D4 E4 C4 G4", "--pair", "sweet_spot_low,sweet_spot_bonus",
                          "--json", str(out)]) == 0
    assert json.loads(out.read_text())["pairs"][0]["a"] == "sweet_spot_low"
    assert "at each sweet_spot_low" in capsys.readouterr().out
    assert research_main(["sweep", "C4 D4", "--pair", "sweet_spot_low,sweet_spot_low"]) == 2


def test_groups_follow_the_mapper_quantization():
    # two notes 0.01 beats apart are one chord to the mapper (resolution 0.125), two to exact time
    evs = [MusicalEvent(1.0, 60, 1, 90), MusicalEvent(1.01, 64, 1, 90), MusicalEvent(2.0, 67, 1, 90)]
    assert [len(g) for g in SW._groups(evs)] == [1, 1, 1]
    assert [len(g) for g in SW._groups(evs, 0.125)] == [2, 1]


def test_compare_optimizers_same_objective():
    song = line([64, 71, 64, 69, 64, 71, 67, 62, 60, 64])
    p = SW.compare_optimizers(song, "probe:x")
    assert p.group == "probe" and p.viterbi.score is not None and p.greedy.score is not None
    assert p.viterbi.score >= p.greedy.score - 1e-9           # the global optimum never loses
    assert p.gain_per_note >= 0
    s = SW.summarize_optimizers([p])
    assert s["tunes"] == 1 and s["viterbi_worse"] == 0.0
    assert "Viterbi vs greedy" in SW.format_optimizers([p])


def test_cli_optimizers(tmp_path, capsys):
    out = tmp_path / "o.json"
    assert research_main(["optimizers", "C4 D4 E4 C4 G4 E4 C4", "--json", str(out), "-v"]) == 0
    rep = json.loads(out.read_text())
    assert rep["summary"]["tunes"] == 1 and rep["pairs"][0]["viterbi"]["score"] is not None
    assert "gain/note" in capsys.readouterr().out
    assert research_main(["optimizers"]) == 2
