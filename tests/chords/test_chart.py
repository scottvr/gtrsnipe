"""Tests for the chord-sheet builder and its CLI."""
import pytest

from gtrsnipe.chords import cli
from gtrsnipe.chords.chart import _chord_window, build_chord_sheet
from gtrsnipe.core.config import MapperConfig
from gtrsnipe.core.types import FretPosition, MusicalEvent, Song, Track


def ev(t, p, d=4):
    return MusicalEvent(t, p, d, 100)


def cmaj_am_song():
    C = [ev(0, 60), ev(0, 64), ev(0, 67)]
    Am = [ev(4, 57), ev(4, 60), ev(4, 64)]
    return Song(tracks=[Track(events=C + Am)], title="T", tempo=120)


def sheet():
    return build_chord_sheet(cmaj_am_song(),
                             MapperConfig(tuning="STANDARD", num_strings=6))


# -- _chord_window ----------------------------------------------------------

def test_chord_window_all_open_shows_nut():
    assert _chord_window([FretPosition(0, 0), FretPosition(1, 0)]) == (1, 5)


def test_chord_window_contains_fretted_notes():
    lo, hi = _chord_window([FretPosition(0, 5), FretPosition(1, 7)])
    assert lo <= 5 and hi >= 7


def test_chord_window_wide_chord_expands():
    lo, hi = _chord_window([FretPosition(0, 3), FretPosition(5, 10)])
    assert lo <= 3 and hi >= 10


# -- build_chord_sheet ------------------------------------------------------

def test_sheet_has_title_and_meta():
    out = sheet()
    assert "# T" in out
    assert "120 BPM" in out


def test_sheet_progression_lists_bar_chords():
    out = sheet()
    assert "## Progression" in out
    assert "C" in out and "Am" in out


def test_sheet_has_a_diagram_per_unique_chord():
    out = sheet()
    assert "## Chords used" in out
    assert "**C**" in out
    assert "**Am**" in out
    # One vertical diagram block per unique chord (2 here) plus the progression
    # block = 3 fenced code blocks.
    assert out.count("```") == 3 * 2  # opening+closing per block


def test_empty_song_sheet_is_graceful():
    out = build_chord_sheet(Song(tracks=[], title="Empty"), MapperConfig())
    assert "# Empty" in out
    assert "No notes" in out


def test_measures_per_line_controls_grid_rows():
    C = [ev(i * 4, 60) for i in range(4)] + [ev(i * 4, 64) for i in range(4)] \
        + [ev(i * 4, 67) for i in range(4)]
    song = Song(tracks=[Track(events=C)], title="Four", tempo=120)
    out = build_chord_sheet(song, MapperConfig(), measures_per_line=2)
    grid = out.split("## Progression")[1].split("```")[1]
    assert len([ln for ln in grid.splitlines() if ln.strip()]) == 2  # 4 bars / 2


# -- CLI --------------------------------------------------------------------

def test_cli_writes_to_stdout(tmp_path, capsys):
    abc = tmp_path / "s.abc"
    abc.write_text("X:1\nT:S\nM:4/4\nL:1/4\nK:C\n[CEG]4|[FAc]4|\n")
    rc = cli.main([str(abc)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "## Progression" in out
    assert "## Chords used" in out


def test_cli_writes_to_file(tmp_path):
    abc = tmp_path / "s.abc"
    abc.write_text("X:1\nT:S\nM:4/4\nL:1/4\nK:C\n[CEG]4|[FAc]4|\n")
    out_file = tmp_path / "chords.md"
    rc = cli.main([str(abc), "-o", str(out_file)])
    assert rc == 0
    assert out_file.exists()
    assert "# " in out_file.read_text()
