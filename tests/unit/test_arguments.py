"""Tests for the shared arg/config layer (P0 of the unified-IO refactor).

The player and chord CLIs used to build an amputated MapperConfig from ~6 args;
now they compose the same arg groups and the same build_mapper_config as the
converter, so every mapper knob reaches every mode.
"""
import argparse

import pytest

from gtrsnipe.arguments import (
    add_mapper_args,
    add_tuning_args,
    build_mapper_config,
    resolve_num_strings,
    setup_parser,
)


def _full_parser():
    p = argparse.ArgumentParser()
    add_tuning_args(p)
    add_mapper_args(p)
    return p


# -- build_mapper_config ----------------------------------------------------

def test_build_mapper_config_threads_all_knobs():
    p = _full_parser()
    args = p.parse_args([
        "--sweet-spot-high", "7", "--let-ring-bonus", "2.5",
        "--fret-span-penalty", "42", "--prefer-open", "--dedupe",
        "--diagonal-span-penalty", "--barre-bonus", "1.5",
    ])
    cfg = build_mapper_config(args, tuning="DROP_D", num_strings=6)
    assert cfg.tuning == "DROP_D"
    assert cfg.sweet_spot_high == 7
    assert cfg.let_ring_bonus == 2.5
    assert cfg.fret_span_penalty == 42
    assert cfg.prefer_open is True
    assert cfg.deduplicate_pitches is True
    assert cfg.diagonal_span_penalty is True
    assert cfg.barre_bonus == 1.5


def test_build_mapper_config_defaults_match_bare_config():
    from gtrsnipe.core.config import MapperConfig
    p = _full_parser()
    cfg = build_mapper_config(p.parse_args([]), tuning="STANDARD", num_strings=6)
    d = MapperConfig()
    for field in ("fret_span_penalty", "movement_penalty", "sweet_spot_low",
                  "sweet_spot_high", "optimizer", "prefer_open", "let_ring_bonus"):
        assert getattr(cfg, field) == getattr(d, field)


# -- resolve_num_strings ----------------------------------------------------

@pytest.mark.parametrize("tuning,given,expected", [
    ("STANDARD", None, 6),
    ("BASS_STANDARD", None, 4),
    ("SEVEN_STRING_STANDARD", None, 7),
    ("STANDARD", 7, 7),      # explicit wins
    ("PIANO", None, 6),      # not a fretboard tuning -> fallback
    ("NONSENSE", None, 6),   # unknown -> fallback
])
def test_resolve_num_strings(tuning, given, expected):
    assert resolve_num_strings(tuning, given) == expected


# -- un-amputation regression ----------------------------------------------

def test_player_parser_exposes_advanced_mapper_knobs():
    from gtrsnipe.player.app import _build_arg_parser
    args = _build_arg_parser().parse_args(
        ["x.mid", "--sweet-spot-high", "9", "--let-ring-bonus", "3"])
    assert args.sweet_spot_high == 9 and args.let_ring_bonus == 3


def test_chords_parser_exposes_advanced_mapper_knobs():
    from gtrsnipe.chords.cli import _build_arg_parser
    args = _build_arg_parser().parse_args(
        ["x.mid", "--fret-span-penalty", "10", "--barre-bonus", "2"])
    assert args.fret_span_penalty == 10 and args.barre_bonus == 2


def test_converter_parser_still_has_everything():
    # Back-compat: the converter's flat parser is unchanged in capability.
    args = setup_parser().parse_args(
        ["-i", "x.mid", "-o", "y.tab", "--optimizer", "greedy", "--capo", "2"])
    assert args.optimizer == "greedy" and args.capo == 2 and args.output == ["y.tab"]
