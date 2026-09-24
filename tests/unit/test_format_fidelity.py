"""Regression tests for the Sprint 2 output-fidelity fixes (Epic C)."""
import logging

import pytest

from gtrsnipe.core.config import MapperConfig
from gtrsnipe.core.types import MusicalEvent, Song, Track
from gtrsnipe.formats.abc.generator import AbcGenerator
from gtrsnipe.formats.mid.generator import MidiGenerator
from gtrsnipe.formats.tab.generator.ascii import AsciiTabGenerator


def _song(ts="4/4", events=None, instrument="Acoustic Grand Piano", title="MySong"):
    return Song(
        tracks=[Track(events=events or [], instrument_name=instrument)],
        tempo=120.0,
        time_signature=ts,
        title=title,
    )


def _note(pitch=60):
    return MusicalEvent(time=0.0, pitch=pitch, duration=1.0, velocity=100)


# --- ABC header ordering (abc/generator.py) ---

def test_abc_title_precedes_key_in_header():
    lines = AbcGenerator.generate(_song(events=[_note()])).splitlines()
    t_idx = next(i for i, l in enumerate(lines) if l.startswith("T:"))
    k_idx = next(i for i, l in enumerate(lines) if l.startswith("K:"))
    assert t_idx < k_idx, "T: (title) must appear before K: in the ABC header"
    # No stray title in the tune body (after K:).
    assert not any(l.startswith("T:") for l in lines[k_idx + 1:])


def test_abc_instrument_is_body_comment_not_title():
    lines = AbcGenerator.generate(
        _song(events=[_note()], instrument="Electric Bass")
    ).splitlines()
    k_idx = next(i for i, l in enumerate(lines) if l.startswith("K:"))
    body = lines[k_idx + 1:]
    assert any(l.startswith("% Electric Bass") for l in body)
    assert not any(l.startswith("T:") for l in body)


# --- MIDI time-signature validation (mid/generator.py) ---

@pytest.mark.parametrize(
    "ts,should_warn",
    [("4/4", False), ("6/8", False), ("3/4", False), ("4/6", True), ("5/3", True)],
)
def test_mid_rejects_non_power_of_two_denominator(ts, should_warn, caplog):
    song = _song(ts=ts, events=[_note()])
    with caplog.at_level(logging.WARNING):
        MidiGenerator.generate(song)  # must never silently truncate the denominator
    warned = any("time signature" in r.getMessage() for r in caplog.records)
    assert warned is should_warn


# --- Capo ordinal suffix (tab/generator/ascii.py) ---

@pytest.mark.parametrize(
    "capo,expected",
    [(1, "1st"), (2, "2nd"), (3, "3rd"), (4, "4th"),
     (11, "11th"), (12, "12th"), (13, "13th"),
     (21, "21st"), (22, "22nd"), (23, "23rd")],
)
def test_capo_ordinal_suffix(capo, expected):
    cfg = MapperConfig(tuning="STANDARD", capo=capo)
    out = AsciiTabGenerator.generate(_song(events=[_note(64)]), command_line="", mapper_config=cfg)
    assert f"Capo: {expected} Fret" in out
