"""Tests for the chord-sheet builder and its CLI."""
import pytest

import pytest

from gtrsnipe.chords import cli
from gtrsnipe.chords.chart import (
    _canonical_positions,
    _chord_window,
    build_chord_sheet,
)
from gtrsnipe.core.chords import identify
from gtrsnipe.core.config import MapperConfig
from gtrsnipe.core.types import FretPosition, MusicalEvent, Song, Track
from gtrsnipe.guitar.mapper import GuitarMapper


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


# -- canonical voicing (regression: whole-bar union produced unplayable shapes) --

CHORD_CASES = [
    ("C", [60, 64, 67], 60),
    ("Am", [57, 60, 64], 57),
    ("E7", [64, 68, 71, 74], 64),
    ("Gmaj7", [55, 59, 62, 66], 55),
    ("Bm7", [59, 62, 66, 69], 59),
    ("C5", [60, 67], 60),
]
TUNINGS = ["STANDARD", "BARITONE_B", "DROP_D", "OPEN_G"]


@pytest.mark.parametrize("pitches,bass", [(p, b) for _, p, b in CHORD_CASES])
@pytest.mark.parametrize("tuning", TUNINGS)
def test_canonical_voicing_is_playable_and_compact(pitches, bass, tuning):
    chord = identify(pitches, bass=bass)
    mapper = GuitarMapper(MapperConfig(tuning=tuning, num_strings=6))
    positions = _canonical_positions(chord, mapper)
    # Every chord tone placed...
    assert len(positions) == len(chord.intervals), f"{chord.name} in {tuning} dropped notes"
    # ...on distinct strings...
    strings = [p.string for p in positions]
    assert len(set(strings)) == len(strings)
    # ...within a hand-sized fret span (the bug produced 9-fret spreads).
    frets = [p.fret for p in positions]
    assert max(frets) - min(frets) <= 4, f"{chord.name} in {tuning} span too wide"


def test_canonical_voicing_prefers_tighter_over_lower():
    # Regression: the octave search must not return the first *complete* voicing
    # if a higher register gives a much tighter (real) chord shape.
    chord = identify([64, 68, 71, 74], bass=64)  # E7
    mapper = GuitarMapper(MapperConfig(tuning="BARITONE_B", num_strings=6))
    positions = _canonical_positions(chord, mapper)
    frets = [p.fret for p in positions]
    assert max(frets) - min(frets) <= 4


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


def test_measures_per_line_zero_does_not_crash():
    # Regression: --measures-per-line 0 made range() raise ValueError.
    out = build_chord_sheet(cmaj_am_song(), MapperConfig(), measures_per_line=0)
    assert "## Progression" in out  # clamped to 1, no crash


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
