"""Tests for the horizontally-scrolling tab renderer."""
import pytest

from gtrsnipe.core.config import MapperConfig
from gtrsnipe.core.types import FretPosition
from gtrsnipe.player.frame import Frame
from gtrsnipe.player.render.scrolltab import ScrollingTabRenderer


def frame(time, string, fret):
    return Frame(time=time, duration=0.5,
                 positions=(FretPosition(string, fret),), window=(1, 5))


def std(width=40, cols_per_beat=4):
    return ScrollingTabRenderer(MapperConfig(tuning="STANDARD", num_strings=6),
                                width=width, cols_per_beat=cols_per_beat)


# One note per beat on the high-E string: frets 0..4 at beats 0..4.
TL = [frame(float(i), 0, i) for i in range(5)]


def test_empty_timeline():
    assert std().render([], 0) == "(empty)"


def test_row_count_is_playhead_plus_strings_plus_footer():
    out = std().render(TL, 0)
    # playhead marker + 6 string rows + footer
    assert len(out.splitlines()) == 1 + 6 + 1


def test_playhead_marker_present_on_first_line():
    out = std().render(TL, 0)
    assert "v" in out.splitlines()[0]


def test_string_labels_high_to_low():
    out = std().render(TL, 0)
    body = out.splitlines()[1:7]
    assert [ln.lstrip()[0] for ln in body] == ["E", "B", "G", "D", "A", "E"]


def test_current_note_sits_at_the_playhead():
    # At index 0 (fret 0 on high E), the '0' digit should be at the playhead col.
    r = std(width=40)
    out = r.render(TL, 0)
    head = out.splitlines()[0]
    e_row = out.splitlines()[1]  # high-E row
    playhead_col = head.index("v")
    assert e_row[playhead_col] == "0"


def test_scrolling_moves_notes_left_as_index_advances():
    # A fixed note (beat 4, fret 4) should appear at a smaller column when the
    # playhead is later in the piece.
    r = std(width=60)

    def col_of_fret4(index):
        row = r.render(TL, index).splitlines()[1]  # high-E row
        return row.index("4")

    assert col_of_fret4(0) > col_of_fret4(2) > col_of_fret4(4)


def test_note_appears_on_its_own_string_row():
    tl = [Frame(0.0, 0.5, (FretPosition(3, 7),), (1, 9))]  # D string, fret 7
    out = std().render(tl, 0)
    rows = out.splitlines()
    d_row = rows[1 + 3]  # playhead + strings E,B,G,then D
    assert "7" in d_row
    # And not on the high-E row.
    assert "7" not in rows[1]


def test_paint_is_the_uniform_entry_point():
    r = std()
    assert r.paint(TL, 1) == r.render(TL, 1)


def test_index_clamped_to_valid_range():
    r = std()
    # Out-of-range index shouldn't crash; clamps to the ends.
    assert r.render(TL, 99).splitlines()[-1].startswith("[5/5]")
    assert r.render(TL, -5).splitlines()[-1].startswith("[1/5]")


def test_multidigit_fret_rendered():
    tl = [Frame(0.0, 0.5, (FretPosition(0, 12),), (10, 14))]
    out = std().render(tl, 0)
    assert "12" in out.splitlines()[1]


def test_invalid_dimensions_rejected():
    with pytest.raises(ValueError):
        std(width=2)
    with pytest.raises(ValueError):
        ScrollingTabRenderer(MapperConfig(), cols_per_beat=0)
