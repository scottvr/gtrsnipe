"""--analyze ranks tunings by playability (backlog F03)."""
import sys

import pytest

from gtrsnipe.core.config import MapperConfig
from gtrsnipe.core.types import MusicalEvent, Song, Track
from gtrsnipe.guitar.analyze import format_ranking, rank_tunings, score_tuning

RIFF = [43, 50, 55, 59, 62, 59, 55, 50] * 3        # the open strings of OPEN_G: G2 D3 G3 B3 D4


def riff_song():
    return Song(tracks=[Track(events=[MusicalEvent(i * 0.5, p, 0.5, 90)
                                      for i, p in enumerate(RIFF)])], title="riff")


def cfg(name, strings=6):
    return MapperConfig(tuning=name, num_strings=strings)


def test_open_g_riff_is_easiest_in_open_g():
    ranked = rank_tunings(riff_song(), [("STANDARD", cfg("STANDARD")), ("OPEN_G", cfg("OPEN_G")),
                                        ("OPEN_E", cfg("OPEN_E"))])
    assert ranked[0].name == "OPEN_G"
    g = ranked[0]
    assert g.placed == g.notes == len(RIFF) and g.open_share > 0.8 and g.travel == 0
    std = next(s for s in ranked if s.name == "STANDARD")
    assert std.per_note < g.per_note                  # standard is harder per note


def test_scoring_does_not_touch_the_song():
    song = riff_song()
    score_tuning(song, cfg("STANDARD"), "STANDARD")
    assert all(e.string is None and e.fret is None for e in song.tracks[0].events)


def test_format_marks_the_best_and_the_gap():
    text = format_ranking(rank_tunings(riff_song(), [("STANDARD", cfg("STANDARD")),
                                                     ("OPEN_G", cfg("OPEN_G"))]))
    first = next(l for l in text.splitlines() if l.strip().startswith("1 "))
    assert "OPEN_G" in first and "best" in first
    std_line = next(l for l in text.splitlines() if "STANDARD" in l)
    assert "+" in std_line                             # points per note harder than the best


def _cli(tmp_path, capsys, monkeypatch, *extra):
    from midiutil import MIDIFile
    from gtrsnipe.converter import main
    path = tmp_path / "riff.mid"
    m = MIDIFile(1)
    m.addTempo(0, 0, 100)
    for i, p in enumerate(RIFF):
        m.addNote(0, 0, p, i * 0.5, 0.5, 90)
    with open(path, "wb") as f:
        m.writeFile(f)
    monkeypatch.setattr(sys, "argv", ["gtrsnipe", "-i", str(path), "--analyze", *extra])
    with pytest.raises(SystemExit) as e:
        main()
    return e.value.code, capsys.readouterr().out


def test_cli_analyze_needs_no_output_and_ranks(tmp_path, capsys, monkeypatch):
    code, out = _cli(tmp_path, capsys, monkeypatch)
    assert code == 0 and "Tunings ranked by playability" in out
    first = next(l for l in out.splitlines() if l.strip().startswith("1 "))
    assert "OPEN_G" in first
    assert "BASS_" not in out                          # a guitar gets guitar tunings


def test_cli_analyze_bass_gets_bass_tunings(tmp_path, capsys, monkeypatch):
    code, out = _cli(tmp_path, capsys, monkeypatch, "--bass")
    assert code == 0
    rows = [l for l in out.splitlines() if l.strip()[:1].isdigit()]
    assert rows and all("BASS_" in r for r in rows)
