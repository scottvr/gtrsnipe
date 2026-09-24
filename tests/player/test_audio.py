"""Tests for the audio sinks (note-diffing logic; backends gated/optional)."""
import pytest

from gtrsnipe.player.audio import (
    AudioSink,
    NullSink,
    make_audio_sink,
)


class FakeSink(AudioSink):
    """Records the note-on/off events the base class emits."""
    def __init__(self):
        super().__init__()
        self.events = []

    def _note_on(self, pitch, velocity):
        self.events.append(("on", pitch, velocity))

    def _note_off(self, pitch):
        self.events.append(("off", pitch))

    def _teardown(self):
        self.events.append(("teardown",))


# -- diffing ---------------------------------------------------------------

def test_first_update_strikes_all_notes():
    s = FakeSink()
    s.update([60, 64, 67], velocity=100)
    ons = {e for e in s.events if e[0] == "on"}
    assert ons == {("on", 60, 100), ("on", 64, 100), ("on", 67, 100)}


def test_held_notes_do_not_restrike():
    s = FakeSink()
    s.update([60, 64])
    s.events.clear()
    s.update([60, 64])  # identical -> nothing happens
    assert s.events == []


def test_only_changed_notes_move():
    s = FakeSink()
    s.update([60, 64])       # C, E
    s.events.clear()
    s.update([64, 67])       # E held, C off, G on
    assert ("off", 60) in s.events
    assert ("on", 67, pytest.approx(96)) in [(e[0], e[1], e[2]) for e in s.events if e[0] == "on"]
    assert ("off", 64) not in s.events  # E was held


def test_update_to_empty_releases_all():
    s = FakeSink()
    s.update([60, 64])
    s.events.clear()
    s.update([])
    assert set(s.events) == {("off", 60), ("off", 64)}


def test_close_releases_ringing_notes_then_tears_down():
    s = FakeSink()
    s.update([60, 64])
    s.events.clear()
    s.close()
    assert ("off", 60) in s.events and ("off", 64) in s.events
    assert s.events[-1] == ("teardown",)


def test_close_when_silent_still_tears_down():
    s = FakeSink()
    s.close()
    assert s.events == [("teardown",)]


# -- NullSink / factory ----------------------------------------------------

def test_null_sink_is_silent_and_safe():
    s = NullSink()
    s.update([60, 64])   # no error, no output
    s.close()


def test_make_audio_sink_none():
    assert isinstance(make_audio_sink("none"), NullSink)


def test_make_audio_sink_unknown_raises():
    with pytest.raises(ValueError):
        make_audio_sink("kazoo")


def test_make_audio_sink_fluidsynth_requires_soundfont():
    # No soundfont -> clean RuntimeError before any backend import.
    with pytest.raises(RuntimeError):
        make_audio_sink("fluidsynth", soundfont=None)


def test_midi_sink_reports_missing_backend_clearly(monkeypatch):
    # Simulate the rtmidi backend being unavailable: mido can't open a port.
    import gtrsnipe.player.audio as audio_mod

    class FakeMido:
        class Message:  # pragma: no cover - not reached
            def __init__(self, *a, **k): ...
        @staticmethod
        def get_output_names():
            return []
        @staticmethod
        def open_output(*a, **k):
            raise OSError("no backend")

    import sys
    monkeypatch.setitem(sys.modules, "mido", FakeMido)
    with pytest.raises(RuntimeError) as ei:
        audio_mod.MidiOutSink()
    assert "gtrsnipe[play]" in str(ei.value)
