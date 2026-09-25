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


# -- orientation / handedness ----------------------------------------------

import pytest

from gtrsnipe.player.render.ascii import AsciiFretboardRenderer


def rend(orientation="horizontal", handed="right"):
    return AsciiFretboardRenderer(
        MapperConfig(tuning="STANDARD", num_strings=6),
        orientation=orientation, handed=handed)


def test_invalid_orientation_rejected():
    with pytest.raises(ValueError):
        rend(orientation="diagonal")


def test_invalid_hand_rejected():
    with pytest.raises(ValueError):
        rend(handed="both")


def test_horizontal_left_reverses_fret_order():
    out = rend(handed="left").render(frame([FretPosition(0, 3)], window=(1, 5)))
    header = out.splitlines()[0].split()
    assert header == ["5", "4", "3", "2", "1"]  # nut on the right, frets descend


def test_horizontal_left_puts_nut_on_the_right():
    # Open string marker sits at the end of the row, not right after the label.
    out = rend(handed="left").render(frame([FretPosition(4, 0)], window=(1, 5)))
    a_row = out.splitlines()[5]  # header + E,B,G,D, then A
    assert a_row.rstrip().endswith(ACTIVE)


def test_vertical_frets_run_top_to_bottom():
    out = rend(orientation="vertical").render(
        frame([FretPosition(0, 3)], window=(3, 7)))
    # Gutter fret numbers, in order, down the left edge below the divider.
    lines = out.splitlines()
    body = lines[3:]  # header, open row, divider, then fret rows
    fret_nums = [int(line.split()[0]) for line in body]
    assert fret_nums == [3, 4, 5, 6, 7]


def test_vertical_right_low_string_on_left():
    out = rend(orientation="vertical", handed="right").render(
        frame([FretPosition(0, 3)], window=(1, 5)))
    labels = out.splitlines()[0].split()
    assert labels == ["E", "A", "D", "G", "B", "E"]  # low E ... high e


def test_vertical_left_flips_string_order():
    out = rend(orientation="vertical", handed="left").render(
        frame([FretPosition(0, 3)], window=(1, 5)))
    labels = out.splitlines()[0].split()
    assert labels == ["E", "B", "G", "D", "A", "E"]  # high e ... low E


def test_vertical_nut_line_only_when_window_touches_fret_one():
    at_nut = rend(orientation="vertical").render(
        frame([FretPosition(0, 3)], window=(1, 5)))
    up_neck = rend(orientation="vertical").render(
        frame([FretPosition(0, 9)], window=(8, 12)))
    assert "===" in at_nut          # solid nut line
    assert "===" not in up_neck     # no nut up the neck
    assert "---" in up_neck         # light divider instead


def test_vertical_marks_active_positions():
    out = rend(orientation="vertical").render(
        frame([FretPosition(4, 0), FretPosition(3, 2)], window=(1, 5)))
    assert out.count(ACTIVE) == 2
