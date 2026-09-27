"""P01: playback honors note lengths and rests; the MIDI reader keeps short notes;
tab input can let notes ring until their string is restruck (--sustain string)."""
import pytest

from gtrsnipe.core.config import MapperConfig
from gtrsnipe.core.types import FretPosition, MusicalEvent
from gtrsnipe.player.audio import AudioSink
from gtrsnipe.player.frame import Frame
from gtrsnipe.player.timeline import TimelineBuilder
from gtrsnipe.player.transport import Transport, metronome_timeline


class Clock:
    def __init__(self):
        self.t = 0.0
    def now(self):
        return self.t
    def sleep(self, dt):
        self.t += max(dt, 0.0)


class Driver:
    """Records (beat-in-seconds-at-60bpm, event, pitches)."""
    def __init__(self, clock):
        self.clock, self.log = clock, []
    def render(self, beat): pass
    def fire(self, frames):
        self.log.append((round(self.clock.now(), 6), "on", sorted(p for f in frames for p in f.pitches)))
    def release(self, pitches):
        self.log.append((round(self.clock.now(), 6), "off", sorted(pitches)))
    def silence(self): pass
    def read_key(self, blocking): return None


def ev(t, p, d, s=0, f=1):
    return MusicalEvent(t, p, d, 90, string=s, fret=f)


def play(frames):
    clk = Clock()
    drv = Driver(clk)
    Transport(frames, 60.0, fps=4, now=clk.now, sleep=clk.sleep).run(drv)   # 1 beat = 1 s
    return drv.log


# -- timeline ---------------------------------------------------------------------

def test_frames_carry_each_notes_own_end():
    events = [ev(0, 48, 4.0, s=5), ev(0, 64, 0.5), ev(1, 65, 0.5), ev(2, 67, 1.0)]
    tl = TimelineBuilder(MapperConfig()).build(events)
    assert tl[0].pitches == (48, 64) and tl[0].ends == (4.0, 0.5)   # bass holds, melody short
    legato = TimelineBuilder(MapperConfig()).build(events, legato=True)
    assert legato[0].ends == (1.0, 1.0)                              # the old behavior


def test_metronome_keeps_notes_legato_on_its_grid():
    tl = TimelineBuilder(MapperConfig()).build([ev(0, 60, 0.1), ev(3, 62, 0.1)])
    assert [f.ends for f in metronome_timeline(tl, 0.5)] == [(0.5,), (1.0,)]


# -- transport -------------------------------------------------------------------------

def test_a_rest_is_silent_and_a_held_note_rings_through_later_onsets():
    tl = TimelineBuilder(MapperConfig()).build(
        [ev(0, 48, 3.0, s=5), ev(0, 64, 0.5), ev(1, 65, 0.5), ev(2, 67, 1.0)])
    log = play(tl)
    assert (0.5, "off", [64]) in log                 # melody note stops: a rest until beat 1
    assert (1.0, "on", [65]) in log and (3.0, "off", [48, 67]) in log
    assert not any(e == "off" and 48 in p and t < 3.0 for t, e, p in log)   # bass held


def test_a_restruck_pitch_is_not_cut_by_its_earlier_release():
    tl = TimelineBuilder(MapperConfig()).build([ev(0, 60, 2.0), ev(1, 60, 1.5)])
    log = play(tl)
    offs = [t for t, e, p in log if e == "off" and p == [60]]
    assert offs == [2.5]                              # not 2.0 (the first note's end)


def test_legacy_frames_without_ends_schedule_no_releases():
    tl = [Frame(0, 1.0, (FretPosition(0, 1),), (1, 5), pitches=(60,)),
          Frame(1, 1.0, (FretPosition(0, 2),), (1, 5), pitches=(61,))]
    assert [e for _, e, _ in play(tl)] == ["on", "on"]


# -- audio sink ---------------------------------------------------------------------

class Rec(AudioSink):
    def __init__(self):
        super().__init__()
        self.msgs = []
    def _note_on(self, p, v): self.msgs.append(("on", p))
    def _note_off(self, p): self.msgs.append(("off", p))
    def _teardown(self): pass


def test_strike_leaves_other_notes_ringing_and_rearticulates_repeats():
    a = Rec()
    a.strike([48, 64])
    a.strike([65])
    assert sorted(a.msgs) == [("on", 48), ("on", 64), ("on", 65)]      # nothing released
    a.msgs.clear()
    a.strike([48])
    assert a.msgs == [("off", 48), ("on", 48)]
    a.msgs.clear()
    a.release([64, 99])
    assert a.msgs == [("off", 64)]


# -- MIDI reader: short notes stay short ----------------------------------------------

def test_midi_reader_keeps_notes_shorter_than_a_sixteenth(tmp_path):
    from midiutil import MIDIFile
    from gtrsnipe.formats.mid.reader import MidiReader
    m = MIDIFile(1)
    m.addTempo(0, 0, 120)
    m.addNote(0, 0, 60, 0, 0.125, 90)        # a 32nd note
    m.addNote(0, 0, 62, 1, 1.0, 90)
    path = tmp_path / "short.mid"
    with open(path, "wb") as f:
        m.writeFile(f)
    evs = sorted(MidiReader.parse(str(path), None).tracks[0].events, key=lambda e: e.time)
    assert evs[0].duration == pytest.approx(0.125) and evs[1].duration == pytest.approx(1.0)


# -- tab input: --sustain string ------------------------------------------------------

ARPEGGIO = """// Time: 4/4
// Tuning: E2,A2,D3,G3,B3,E4

e|-----------0-----------|
B|--------1--------1-----|
G|-----0--------0--------|
D|--2--------2--------2--|
A|-----------------------|
E|-----------------------|
"""


def test_tab_sustain_string_rings_until_the_same_string_again():
    from gtrsnipe.formats.tab.parser import AsciiTabParser
    leg = sorted(AsciiTabParser.parse(ARPEGGIO).tracks[0].events, key=lambda e: e.time)
    ring = sorted(AsciiTabParser.parse(ARPEGGIO, sustain="string").tracks[0].events,
                  key=lambda e: e.time)
    gap = leg[1].time - leg[0].time
    assert all(e.duration == pytest.approx(gap) for e in leg[:-1])   # legato: next onset
    d = ring[0]                                                      # the first D-string note
    next_d = next(e for e in ring[1:] if e.string == d.string)
    assert d.duration == pytest.approx(next_d.time - d.time) and d.duration > gap
    assert max(e.duration for e in ring) <= 4.0                      # capped at one bar


def test_sustain_option_is_on_both_clis():
    from gtrsnipe.arguments import setup_parser
    from gtrsnipe.player.app import _build_arg_parser
    assert setup_parser().parse_args(["--sustain", "string"]).sustain == "string"
    a = _build_arg_parser().parse_args(["x.tab", "--sustain", "string", "--legato"])
    assert a.sustain == "string" and a.legato
