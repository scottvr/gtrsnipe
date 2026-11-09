"""gtrsnipe-research score: a fingering scored bar by bar with the mapper's own objective."""
import copy
import json

import pytest

from gtrsnipe.core.config import MapperConfig
from gtrsnipe.core.types import MusicalEvent, Song, Track
from gtrsnipe.formats.tab.generator.ascii import AsciiTabGenerator
from gtrsnipe.guitar.mapper import GuitarMapper
from gtrsnipe.research import score as S
from gtrsnipe.research.cli import main as research_main

OPEN = [64, 59, 55, 50, 45, 40]


def song(notes, time_signature="4/4", tempo=120.0):
    """A fingered Song from (time, string, fret) triples."""
    evs = [MusicalEvent(time=t, pitch=OPEN[s] + f, duration=0.5, velocity=90, string=s, fret=f)
           for t, s, f in notes]
    return Song(tracks=[Track(events=evs)], title="t", time_signature=time_signature, tempo=tempo)


# the open-B question: B3 on the B string open, or on the G string at fret 4
EDITOR = [(0, 4, 0), (0.5, 2, 4), (1, 1, 3), (1.5, 0, 5),      # bar 1: A:0 G:4 B:3 e:5
          (4, 4, 0), (4.5, 2, 4), (5, 1, 3), (5.5, 0, 5)]      # bar 2: the same
OURS = [(0, 4, 0), (0.5, 1, 0), (1, 1, 3), (1.5, 0, 5),
        (4, 4, 0), (4.5, 1, 0), (5, 1, 3), (5.5, 0, 5)]


def test_bar_numbers_follow_the_time_signature_and_count_from_one():
    p = S.score_path(song(EDITOR))
    assert [s.bar for s in p.steps] == [1, 1, 1, 1, 2, 2, 2, 2]
    assert [s.beat for s in p.steps][:4] == [0, 0.5, 1, 1.5]
    p34 = S.score_path(song(EDITOR, time_signature="3/4"))
    assert [s.bar for s in p34.steps] == [1, 1, 1, 1, 2, 2, 2, 2]     # 4 beats = bar 2 in 3/4 too
    p68 = S.score_path(song(EDITOR, time_signature="6/8"))             # 3 quarter-beats a bar
    assert [s.bar for s in p68.steps] == [1, 1, 1, 1, 2, 2, 2, 2]
    assert S.bar_length(song([], "6/8")) == 3.0 and S.bar_length(song([], "2/2")) == 4.0


def test_parse_bars():
    assert S.parse_bars(None) == (1, None)
    assert S.parse_bars("23") == (23, 23)
    assert S.parse_bars("23-25") == (23, 25)
    assert S.parse_bars("23-") == (23, None)
    assert S.parse_bars("-3") == (1, 3)
    with pytest.raises(ValueError):
        S.parse_bars("5-2")
    with pytest.raises(ValueError):
        S.parse_bars("0")


@pytest.mark.parametrize("kw", [
    {},
    dict(prefer_open=True, sweet_spot_high=4),
    dict(let_ring_bonus=210.0, diagonal_span_penalty=True, prefer_open=True),     # second order
    dict(movement_time_base="end", prefer_open=True),                             # M08
    dict(string_switch_penalty=0, ignore_open=True, prefer_open=True, unplayable_fret_span=3,
         high_fret_penalty=50, deduplicate_pitches=True, fretted_open_penalty=10, movement_penalty=20,
         let_ring_bonus=210, diagonal_span_penalty=True),
])
def test_recomputed_path_total_is_the_viterbi_score_exactly(kw):
    s = song(EDITOR + [(8 + i * 0.5, i % 6, (i * 3) % 9) for i in range(24)])
    cfg = MapperConfig(**kw)
    cfg.tempo_bpm = 120.0
    notes = [copy.copy(e) for e in s.tracks[0].events]
    for e in notes:
        e.string = e.fret = None
    m = GuitarMapper(copy.deepcopy(cfg))
    mapped = m.map_events_to_fretboard(notes, no_articulations=True)
    p = S.score_path(s, cfg, "g", events=mapped)
    assert p.total == m.last_path_score
    assert S.mapper_path(s, cfg).total == m.last_path_score


def test_the_open_b_bar_scores_as_the_mapper_scores_it():
    cfg = MapperConfig(prefer_open=True, sweet_spot_high=4)
    ed, ours = S.score_path(song(EDITOR), cfg, "editor"), S.score_path(song(OURS), cfg, "ours")
    # G:4 pays the fretted-open penalty where B:0 does not; both bars are the same figure
    assert ed.bar_totals()[1] < ours.bar_totals()[1]
    assert ed.bar_totals()[2] < ours.bar_totals()[2]
    assert ed.bar_totals()[1] != ed.bar_totals()[2]      # bar 2's first step keeps its real predecessor
    names = ed.names
    fo = names.index("fretted_open")
    assert ed.features_in(1, 1)[fo] == 1.0 and ours.features_in(1, 1)[fo] == 0.0
    # the same notes under the mapper come out as 'ours'
    mp = S.mapper_path(song(EDITOR), cfg)
    assert [s.fingering for s in mp.steps] == [s.fingering for s in ours.steps]


def test_report_names_the_knob_that_would_tie_and_drops_impossible_ones():
    cfg = MapperConfig(prefer_open=True, sweet_spot_high=4)
    ed, ours = S.score_path(song(EDITOR), cfg, "editor"), S.score_path(song(OURS), cfg, "ours")
    text = S.format_report([ed, ours], cfg, 1, 1)
    assert "bar 1" in text and "editor minus ours over bar 1" in text
    assert "fretted_open" in text and "no fretted_open_penalty >= 0 ties it" in text
    assert "G:4" in text and "B:0" in text          # fingerings in string:fret form
    # the editor's G:4 leaves the B string ringing: let-ring is the knob that can tie it
    assert "tie: let_ring_bonus 0 ->" in text
    whole = S.format_report([ed, ours], cfg)
    assert "all bars" in whole and "piece" not in whole.split("\n")[3]


def test_cli_scores_a_tab_file_with_mapper_knobs_and_writes_json(tmp_path, capsys):
    text = AsciiTabGenerator.generate(song(EDITOR), "", premapped=True, no_articulations=True)
    f = tmp_path / "editor.tab"
    f.write_text(text)
    out = tmp_path / "s.json"
    rc = research_main(["score", str(f), "--bars", "1", "--prefer-open", "--sweet-spot-high", "4",
                        "--json", str(out)])
    assert rc == 0
    printed = capsys.readouterr().out
    assert "editor" in printed and "gtrsnipe" in printed and "fretted_open" in printed
    rep = json.loads(out.read_text())
    assert [p["label"] for p in rep[0]["paths"]] == ["editor", "gtrsnipe"]
    assert len(rep[0]["paths"][0]["steps"]) == 8 and rep[0]["bars"] == [1, 1]


def test_cli_reads_a_txt_tab_and_can_skip_the_mapper(tmp_path, capsys):
    text = AsciiTabGenerator.generate(song(EDITOR), "", premapped=True, no_articulations=True)
    f = tmp_path / "classtab.txt"
    f.write_text(text)
    assert research_main(["score", str(f), "--no-mapper"]) == 0
    printed = capsys.readouterr().out
    assert "classtab" in printed and "gtrsnipe" not in printed.split("\n")[0]
    assert research_main(["score", "C4 D4 E4", "--no-mapper"]) == 2       # nothing as written to score
    assert "no fingering" in capsys.readouterr().err
