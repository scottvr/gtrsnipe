"""Technique letters (h/p/t) in ASCII tabs sit BEFORE the fret digits, so a
chord's digits share one column and the parser (which times a note by its digit
column) reads the tab back with the same onsets. Backlog B02."""
import logging
from itertools import groupby

import pytest

from gtrsnipe.core.config import MapperConfig
from gtrsnipe.formats.tab.generator.ascii import AsciiTabGenerator
from gtrsnipe.formats.tab.parser import AsciiTabParser
from gtrsnipe.guitar.homograph import parse_inline


def _groups(song):
    ev = sorted((e for t in song.tracks for e in t.events), key=lambda e: (e.time, e.pitch))
    return [(t, tuple(e.pitch for e in g)) for t, g in groupby(ev, key=lambda e: e.time)]


def _round_trip(spec):
    logging.disable(logging.INFO)
    try:
        text = AsciiTabGenerator.generate(parse_inline(spec), command_line="",
                                          mapper_config=MapperConfig())
    finally:
        logging.disable(logging.NOTSET)
    return text, _groups(AsciiTabParser.parse(text))


@pytest.mark.parametrize("spec", [
    "E3:0.5 F3+A3:1",                 # review repro: a chord whose low note is hammered
    "A3:0.5 C4+E4:0.5 B3+D4:1",       # hammer, then pull-off, inside chords
    "r:3.5 C4:0.5 D4+F4:1",           # hammered chord note on beat 1 of a new measure
])
def test_chords_with_a_technique_stay_chords(spec):
    text, back = _round_trip(spec)
    assert any(c in text for c in "hp"), "the case must actually render a technique"
    assert [p for _, p in back] == [p for _, p in _groups(parse_inline(spec))]


def test_hammered_notes_are_not_read_late():
    # Equal gaps, but the 2nd note is picked and the 3rd hammered: the old layout put
    # the hammered digit one column late, so its gap read longer than the picked one.
    text, back = _round_trip("G3:0.5 C4:0.5 D4:0.5 C4:1")
    assert "h" in text
    times = [t for t, _ in back]
    gaps = [round(b - a, 6) for a, b in zip(times, times[1:])]
    assert gaps[0] == gaps[1] == gaps[2], (gaps, text)
