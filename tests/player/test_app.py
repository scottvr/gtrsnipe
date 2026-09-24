"""Tests for the player app run loop and wiring (I/O injected as fakes)."""
import pytest

from gtrsnipe.core.config import MapperConfig
from gtrsnipe.core.types import FretPosition, MusicalEvent, Song, Track
from gtrsnipe.player.app import Player, build_timeline, parse_and_map, play_file
from gtrsnipe.player.clock import MetronomeClock, RealtimeClock, StepClock
from gtrsnipe.player.frame import Frame
from gtrsnipe.player.render.ascii import AsciiFretboardRenderer


def frame(time, duration, fret=3):
    return Frame(time=time, duration=duration,
                 positions=(FretPosition(0, fret),), window=(1, 5))


def make_player(read_keys=None):
    """A Player whose I/O is captured/scripted."""
    writes, sleeps = [], []
    keys = iter(read_keys or [])
    p = Player(
        AsciiFretboardRenderer(MapperConfig()),
        writer=writes.append,
        sleep=sleeps.append,
        read_key=lambda: next(keys, "\n"),
        clear=False,
    )
    return p, writes, sleeps


TL = [frame(0, 1.0), frame(1, 0.5), frame(1.5, 2.0)]


def test_realtime_sleeps_between_frames_not_after_last():
    p, writes, sleeps = make_player()
    p.run(TL, RealtimeClock(), tempo_bpm=120)
    # 3 frames painted, 2 gaps slept (last frame has no sleep)
    assert len(sleeps) == 2
    assert sleeps == pytest.approx([0.5, 0.25])


def test_every_frame_is_painted():
    p, writes, sleeps = make_player()
    p.run(TL, RealtimeClock(), tempo_bpm=120)
    # One write per frame (clear=False -> no extra clear writes).
    assert len(writes) == 3


def test_step_clock_waits_for_a_key_per_transition():
    p, writes, sleeps = make_player(read_keys=["\n", "\n"])
    p.run(TL, StepClock(), tempo_bpm=120)
    assert sleeps == []            # step never sleeps
    assert len(writes) == 3        # all frames shown


def test_step_clock_quits_on_q():
    p, writes, sleeps = make_player(read_keys=["q"])
    p.run(TL, StepClock(), tempo_bpm=120)
    # Painted the first frame, then 'q' aborts before the rest.
    assert len(writes) == 1


def test_clear_emits_clear_sequence():
    writes = []
    p = Player(AsciiFretboardRenderer(MapperConfig()),
               writer=writes.append, sleep=lambda s: None,
               read_key=lambda: "\n", clear=True)
    p.run([frame(0, 1.0)], RealtimeClock(), tempo_bpm=120)
    assert any("\033[2J" in w for w in writes)


def test_metronome_uses_constant_interval():
    p, writes, sleeps = make_player()
    p.run(TL, MetronomeClock(grid_beats=0.5), tempo_bpm=120)
    assert sleeps == pytest.approx([0.25, 0.25])


# -- wiring: parse -> map -> timeline ---------------------------------------

def test_parse_and_map_populates_positions(tmp_path):
    # A tiny ABC file exercises the real parse+map path without audio deps.
    abc = tmp_path / "scale.abc"
    abc.write_text("X:1\nT:Scale\nM:4/4\nL:1/4\nK:C\nCDEF|GABc|\n")
    cfg = MapperConfig(tuning="STANDARD", num_strings=6)
    song = parse_and_map(str(abc), cfg)
    events = [e for t in song.tracks for e in t.events]
    assert events, "expected mapped notes"
    assert all(e.string is not None and e.fret is not None for e in events)


def test_build_timeline_from_mapped_song():
    cfg = MapperConfig()
    song = Song(tracks=[Track(events=[
        MusicalEvent(0, 60, 0.5, 100, string=0, fret=3),
        MusicalEvent(1, 62, 0.5, 100, string=0, fret=5),
    ])])
    frames = build_timeline(song, cfg)
    assert len(frames) == 2


def test_play_file_returns_1_when_nothing_maps(tmp_path, monkeypatch):
    # Force an empty timeline; play_file should report failure cleanly.
    import gtrsnipe.player.app as app
    monkeypatch.setattr(app, "parse_and_map", lambda *a, **k: Song(tracks=[]))
    rc = play_file("dummy.mid", mapper_config=MapperConfig())
    assert rc == 1


def test_default_read_key_falls_back_when_stdin_not_a_tty(monkeypatch):
    # Regression: a piped/redirected stdin raises termios.error, not
    # ImportError, so the raw-mode path must be gated on isatty().
    import io
    import gtrsnipe.player.app as app

    fake = io.StringIO("q\n")
    fake.isatty = lambda: False
    monkeypatch.setattr(app.sys, "stdin", fake)
    assert app._default_read_key() == "q"


def test_play_file_end_to_end_with_injected_player(tmp_path):
    abc = tmp_path / "scale.abc"
    abc.write_text("X:1\nT:Scale\nM:4/4\nL:1/4\nK:C\nCDEF|GABc|\n")
    p, writes, sleeps = make_player()
    rc = play_file(str(abc), clock="step", mapper_config=MapperConfig(), player=p)
    assert rc == 0
    assert writes, "expected frames to be painted"
