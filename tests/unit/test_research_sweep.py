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
    for k in SW.KNOBS.values():
        assert k.default in k.ladder, k.name
        assert len(set(k.ladder)) == len(k.ladder), k.name


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


def test_greedy_has_no_path_score():
    r = SW.finger(line([64, 71, 64]), MapperConfig(optimizer="greedy"))
    assert r.score is None


def test_unplayable_chosen_counts_spans_past_the_limit():
    # x-5-7-7-0-0: D3 A3 D4 with open B and E. With open strings counted in the span
    # no fingering fits 4 frets, every candidate returns the flat -1000, and the
    # mapper picks one anyway: the sentinel can't rank them.
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
    assert r.knobs["sweet_spot_bonus"].distinct == 1          # 0.17 frets decides nothing
    assert r.scale_invariant is True


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
    assert summ["sweet_spot_bonus"].verdict == "dead"
    assert summ["sweet_spot_bonus"].live_songs == 0
    assert summ["movement_penalty"].songs == 2
    assert summ["movement_penalty"].distinct_total >= 2
    text = SW.format_summary(list(summ.values()), results)
    assert "sweet_spot_bonus" in text and "dead" in text
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
