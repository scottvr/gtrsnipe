"""Tests for custom tunings (--tuning-pitches / --drop-low-string), the tab
parser honoring a tuning, and the inverse tuning solver."""
import argparse

import pytest

from gtrsnipe.arguments import (
    add_mapper_args,
    add_tuning_args,
    build_mapper_config,
    open_string_pitches_for,
    parse_tuning_pitches,
    resolve_custom_tuning,
    resolve_num_strings,
)
from gtrsnipe.core.theory import note_name_to_pitch
from gtrsnipe.guitar.mapper import GuitarMapper
from gtrsnipe.guitar.tuning_solver import (
    format_open_string_tab,
    solve_open_string_tuning,
)


def _parser():
    p = argparse.ArgumentParser()
    add_tuning_args(p)
    add_mapper_args(p)
    return p


# -- parse_tuning_pitches ---------------------------------------------------

def test_parse_tuning_pitches_stored_low_to_high():
    assert parse_tuning_pitches("A1,E2,A2,D3,F#3,B3") == ("A1", "E2", "A2", "D3", "F#3", "B3")


def test_parse_tuning_pitches_validates():
    with pytest.raises(ValueError):
        parse_tuning_pitches("A1")           # too few
    with pytest.raises(ValueError):
        parse_tuning_pitches("A1,H9")        # bad note name


# -- custom tuning through the config ---------------------------------------

def test_build_mapper_config_custom_tuning():
    a = _parser().parse_args(["--tuning-pitches", "A1,E2,A2,D3,F#3,B3"])
    cfg = build_mapper_config(a, tuning=a.tuning,
                              num_strings=resolve_num_strings(a.tuning, a.num_strings))
    assert cfg.tuning == "CUSTOM"
    assert cfg.num_strings == 6
    assert cfg.custom_tuning == ("A1", "E2", "A2", "D3", "F#3", "B3")  # low->high
    # open pitches are string index 0 = highest (high->low), unchanged by the flip
    assert GuitarMapper(cfg).open_string_pitches == [59, 54, 50, 45, 40, 33]


def test_drop_low_string_on_named_tuning():
    # BARITONE_B with its low B dropped 2 semitones == the A1 baritone.
    a = _parser().parse_args(["--tuning", "BARITONE_B", "--drop-low-string", "2"])
    custom = resolve_custom_tuning(a)
    assert custom[0] == "A1"   # lowest string (index 0, low->high) dropped B1 -> A1


def test_no_custom_tuning_when_plain():
    a = _parser().parse_args(["--tuning", "DROP_D"])
    assert resolve_custom_tuning(a) is None


def test_renderer_labels_from_custom_tuning():
    from gtrsnipe.player.render.ascii import AsciiFretboardRenderer
    a = _parser().parse_args(["--tuning-pitches", "A1,E2,A2,D3,F#3,B3"])
    cfg = build_mapper_config(a, tuning=a.tuning,
                              num_strings=resolve_num_strings(a.tuning, a.num_strings))
    assert AsciiFretboardRenderer(cfg)._string_labels() == ["B", "F#", "D", "A", "E", "A"]


# -- tab parser honors the tuning -------------------------------------------

def test_tab_parser_uses_supplied_tuning():
    from gtrsnipe.formats.tab.parser import AsciiTabParser
    tab = "e|--0--|\nB|-----|\nG|-----|\nD|-----|\nA|-----|\nE|-----|\n"
    std = AsciiTabParser.parse(tab)
    assert [e.pitch for e in std.tracks[0].events] == [64]           # standard high e
    retuned = AsciiTabParser.parse(tab, open_string_pitches=[62, 59, 55, 50, 45, 40])
    assert [e.pitch for e in retuned.tracks[0].events] == [62]        # high string -> D4


def test_open_string_pitches_for():
    # Returns string index 0 = highest (high->low); names are low->high so reversed.
    assert open_string_pitches_for("STANDARD") == [64, 59, 55, 50, 45, 40]
    assert open_string_pitches_for("CUSTOM", ("E2", "A2")) == [45, 40]  # low->high -> [A2, E2]


# -- tuning solver ----------------------------------------------------------

def test_solver_assigns_distinct_pitches_to_open_strings():
    # Twinkle head: C C G G A A G
    tgt = [note_name_to_pitch(n) for n in ["C4", "C4", "G4", "G4", "A4", "A4", "G4"]]
    open_pitches, assignment = solve_open_string_tuning(tgt)
    assert open_pitches == sorted(set(tgt), reverse=True)   # high -> low, distinct
    # every note is playable open on its assigned string == the target pitch
    for note, s in zip(tgt, assignment):
        assert open_pitches[s] == note


def test_solver_rejects_too_many_distinct():
    tgt = list(range(60, 68))  # 8 distinct pitches
    with pytest.raises(ValueError):
        solve_open_string_tuning(tgt, max_strings=6)


def test_format_open_string_tab_shows_only_open_strings():
    tgt = [note_name_to_pitch(n) for n in ["C4", "C4", "G4"]]
    open_pitches, assignment = solve_open_string_tuning(tgt)
    from gtrsnipe.core.theory import pitch_to_note_name
    names = [pitch_to_note_name(p) for p in open_pitches]
    tab = format_open_string_tab(names, assignment)
    assert "0" in tab           # frets are all 0 (open)
    assert all(c in "0-|GACDEFB#\n " or c.isalpha() for c in tab)  # no fret >0 digits
    assert "1" not in tab and "2" not in tab
