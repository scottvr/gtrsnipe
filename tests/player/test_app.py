"""Tests for the player wiring: parse -> map -> timeline -> transport, plus the
_Driver that binds a renderer + sink + audio. I/O is injected (sink, audio,
clock) so these run headless."""
import pytest

from gtrsnipe.core.config import MapperConfig
from gtrsnipe.core.types import FretPosition, MusicalEvent, Song, Track
from gtrsnipe.player.app import (
    _Driver,
    build_renderer,
    build_timeline,
    parse_and_map,
    play_file,
)
from gtrsnipe.player.audio import AudioSink
from gtrsnipe.player.frame import Frame
from gtrsnipe.player.render.ascii import AsciiFretboardRenderer
from gtrsnipe.player.sink import PlainSink


class FakeClock:
    def __init__(self):
        self.t = 0.0
    def now(self):
        return self.t
    def sleep(self, dt):
        self.t += max(dt, 0.0)


class RecordingAudio(AudioSink):
    def __init__(self):
        super().__init__()
        self.attacks = []
        self.offs = 0
        self.closed = False
    def attack(self, pitches, velocity=96):
        self.attacks.append(tuple(pitches))
    def all_off(self):
        self.offs += 1
    def close(self):
        self.closed = True


def abc_scale(tmp_path):
    p = tmp_path / "scale.abc"
    p.write_text("X:1\nT:Scale\nM:4/4\nL:1/4\nK:C\nCDEF|GABc|\n")
    return str(p)


# -- _Driver ----------------------------------------------------------------

def test_driver_render_fire_silence():
    tl = [Frame(0, 1.0, (FretPosition(0, 3),), (1, 5), pitches=(60,))]
    writes = []
    sink = PlainSink(writer=writes.append, keys=[], clear=False)
    audio = RecordingAudio()
    d = _Driver(tl, AsciiFretboardRenderer(MapperConfig()), sink, audio)
    d.render(0.0)
    d.fire(tl)
    d.silence()
    assert writes and "beat" in writes[-1]
    assert audio.attacks == [(60,)]
    assert audio.offs == 1


# -- parse/map/timeline -----------------------------------------------------

def test_run_player_restores_sink_even_if_audio_close_raises():
    # Regression: a raising audio.close() must not skip sink.teardown() (terminal
    # restore), so the nested finally in run_player is required.
    from gtrsnipe.player.app import map_song, run_player
    from gtrsnipe.player.sink import Sink

    class BoomAudio(AudioSink):
        def close(self):
            raise RuntimeError("midi port died")

    class RecSink(Sink):
        def __init__(self):
            self.torn = False
        def setup(self):
            pass
        def write(self, t):
            pass
        def read_key(self, blocking):
            return None
        def teardown(self):
            self.torn = True

    cfg = MapperConfig()
    song = map_song(Song(tracks=[Track(events=[
        MusicalEvent(0, 60, 0.5, 100, string=0, fret=3)])]), cfg)
    rec = RecSink()
    clk = FakeClock()
    with pytest.raises(RuntimeError):
        run_player(song, cfg, clock="tempo", audio=BoomAudio(), sink=rec,
                   now=clk.now, sleep=clk.sleep)
    assert rec.torn, "sink.teardown() must run even when audio.close() raises"


def test_parse_and_map_populates_positions(tmp_path):
    cfg = MapperConfig(tuning="STANDARD", num_strings=6)
    song = parse_and_map(abc_scale(tmp_path), cfg)
    events = [e for t in song.tracks for e in t.events]
    assert events and all(e.string is not None and e.fret is not None for e in events)


def test_build_timeline_from_mapped_song():
    cfg = MapperConfig()
    song = Song(tracks=[Track(events=[
        MusicalEvent(0, 60, 0.5, 100, string=0, fret=3),
        MusicalEvent(1, 62, 0.5, 100, string=0, fret=5),
    ])])
    assert len(build_timeline(song, cfg)) == 2


# -- play_file integration --------------------------------------------------

def test_play_file_tempo_plays_and_closes(tmp_path):
    clk = FakeClock()
    audio = RecordingAudio()
    writes = []
    sink = PlainSink(writer=writes.append, keys=[], clear=False)
    rc = play_file(abc_scale(tmp_path), clock="tempo", mapper_config=MapperConfig(),
                   audio=audio, sink=sink, now=clk.now, sleep=clk.sleep)
    assert rc == 0
    assert audio.attacks, "expected notes to sound"
    assert audio.closed, "audio must be closed on exit"
    assert writes, "expected frames painted"


def test_play_file_step_mode_steps_then_quits(tmp_path):
    audio = RecordingAudio()
    sink = PlainSink(writer=lambda s: None, keys=[".", ".", "q"], clear=False)
    rc = play_file(abc_scale(tmp_path), clock="step", mapper_config=MapperConfig(),
                   audio=audio, sink=sink)
    assert rc == 0
    # initial frame + 2 '.' steps = 3 attacks before quit (space now resumes, not steps)
    assert len(audio.attacks) == 3


def test_play_file_scrolling_tab_view(tmp_path):
    clk = FakeClock()
    writes = []
    sink = PlainSink(writer=writes.append, keys=[], clear=False)
    rc = play_file(abc_scale(tmp_path), clock="tempo", view="tab",
                   mapper_config=MapperConfig(), sink=sink,
                   now=clk.now, sleep=clk.sleep)
    assert rc == 0
    assert any("v" in w for w in writes)  # playhead marker


def test_play_file_returns_1_when_nothing_maps(monkeypatch):
    import gtrsnipe.player.app as app
    audio = RecordingAudio()
    monkeypatch.setattr(app, "parse_and_map", lambda *a, **k: Song(tracks=[]))
    rc = play_file("dummy.mid", mapper_config=MapperConfig(), audio=audio,
                   sink=PlainSink(writer=lambda s: None, keys=[]))
    assert rc == 1
    assert audio.closed  # still cleaned up on the early return


def test_track_is_threaded_to_parser(monkeypatch):
    import gtrsnipe.player.app as app
    captured = {}

    def fake_parse_and_map(path, cfg, *, track=None, no_articulations=True):
        captured["track"] = track
        return Song(tracks=[Track(events=[
            MusicalEvent(0, 60, 0.5, 100, string=0, fret=3)])])

    monkeypatch.setattr(app, "parse_and_map", fake_parse_and_map)
    rc = play_file("song.mid", clock="step", track=2, mapper_config=MapperConfig(),
                   sink=PlainSink(writer=lambda s: None, keys=["q"]))
    assert rc == 0
    assert captured["track"] == 2


def test_metronome_regrids(tmp_path):
    # Metronome mode should still play to completion (re-timed timeline).
    clk = FakeClock()
    audio = RecordingAudio()
    rc = play_file(abc_scale(tmp_path), clock="metronome", grid_beats=0.5,
                   mapper_config=MapperConfig(), audio=audio,
                   sink=PlainSink(writer=lambda s: None, keys=[]),
                   now=clk.now, sleep=clk.sleep)
    assert rc == 0 and audio.attacks


# -- main() CLI helpers -----------------------------------------------------

def test_main_list_instruments(capsys):
    from gtrsnipe.player.app import main
    rc = main(["--list-instruments"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Acoustic Guitar (nylon)" in out


def test_main_requires_input():
    from gtrsnipe.player.app import main
    with pytest.raises(SystemExit):
        main([])  # no input, no --list-instruments
