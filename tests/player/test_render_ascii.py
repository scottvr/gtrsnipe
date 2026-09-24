"""Tests for the ASCII fretboard renderer."""
from gtrsnipe.core.config import MapperConfig
from gtrsnipe.core.types import FretPosition
from gtrsnipe.player.frame import Frame
from gtrsnipe.player.render.ascii import ACTIVE, AsciiFretboardRenderer


def frame(positions, window=(1, 5), time=0.0, duration=0.5):
    return Frame(time=time, duration=duration, positions=tuple(positions),
                 window=window)


def std_renderer(**cfg):
    return AsciiFretboardRenderer(MapperConfig(tuning="STANDARD", num_strings=6, **cfg))


def test_row_count_is_strings_plus_header():
    out = std_renderer().render(frame([FretPosition(1, 3)]))
    lines = out.splitlines()
    assert len(lines) == 6 + 1  # 6 strings + header


def test_standard_tuning_string_labels_high_to_low():
    out = std_renderer().render(frame([FretPosition(0, 3)]))
    body = out.splitlines()[1:]  # skip header
    first_letters = [line.lstrip()[0] for line in body]
    assert first_letters == ["E", "B", "G", "D", "A", "E"]


def test_header_shows_window_fret_numbers():
    out = std_renderer().render(frame([FretPosition(0, 3)], window=(3, 7)))
    header = out.splitlines()[0]
    for f in (3, 4, 5, 6, 7):
        assert str(f) in header


def test_active_fretted_note_shows_marker():
    # String 1 (B), fret 4, window 1..5 -> the B row has a marker.
    out = std_renderer().render(frame([FretPosition(1, 4)], window=(1, 5)))
    b_row = out.splitlines()[2]  # header, then E(0), then B(1)
    assert ACTIVE in b_row


def test_open_string_marks_the_nut():
    out = std_renderer().render(frame([FretPosition(4, 0)], window=(1, 5)))
    # String 4 = A (row index 5 counting header). Its nut cell is the marker.
    a_row = out.splitlines()[5]
    assert a_row.count(ACTIVE) == 1  # only the nut, no fretted cell


def test_silent_string_has_no_marker():
    out = std_renderer().render(frame([FretPosition(0, 3)], window=(1, 5)))
    # The low-E row (last) is silent.
    e_row = out.splitlines()[-1]
    assert ACTIVE not in e_row


def test_unknown_tuning_falls_back_to_numeric_labels():
    r = AsciiFretboardRenderer(MapperConfig(tuning="NONEXISTENT", num_strings=6))
    out = r.render(frame([FretPosition(0, 3)]))
    body = out.splitlines()[1:]
    first_chars = [line.lstrip()[0] for line in body]
    assert first_chars == ["1", "2", "3", "4", "5", "6"]


def test_render_with_status_appends_footer():
    out = std_renderer().render_with_status(
        frame([FretPosition(0, 3)], window=(1, 5), time=2.5), index=0, total=4)
    last = out.splitlines()[-1]
    assert "1/4" in last
    assert "2.5" in last
    assert "1-5" in last


def test_chord_marks_multiple_strings():
    positions = [FretPosition(0, 3), FretPosition(1, 5), FretPosition(2, 5)]
    out = std_renderer().render(frame(positions, window=(1, 5)))
    assert out.count(ACTIVE) == 3
