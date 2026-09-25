"""Tests for the event-driven Transport (replaces the old clock tests).

Driven with an injected clock + a fake driver, so timing is deterministic. The
key property: audio onsets fire at their *true* beat times, independent of the
display refresh rate (fps).
"""
import pytest

from gtrsnipe.core.types import FretPosition
from gtrsnipe.player.frame import Frame
from gtrsnipe.player.transport import Transport, metronome_timeline


def frame(time, pitch, duration=1.0):
    return Frame(time=time, duration=duration,
                 positions=(FretPosition(0, pitch % 12),), window=(1, 5),
                 pitches=(pitch,))


class FakeClock:
    def __init__(self):
        self.t = 0.0
    def now(self):
        return self.t
    def sleep(self, dt):
        self.t += max(dt, 0.0)


class FakeDriver:
    def __init__(self, clock=None, keys=None):
        self.clock = clock
        self.renders = []
        self.fires = []          # (wall_time, [pitch-tuples])
        self.silences = 0
        self._keys = list(keys or [])
        self._i = 0

    def render(self, beat):
        self.renders.append(round(beat, 6))

    def fire(self, frames):
        t = self.clock.now() if self.clock else None
        self.fires.append((t, [tuple(f.pitches) for f in frames]))

    def silence(self):
        self.silences += 1

    def read_key(self, blocking):
        if self._i < len(self._keys):
            k = self._keys[self._i]
            self._i += 1
            return k
        return None

    def show(self, text):
        self.shown = getattr(self, "shown", [])
        self.shown.append(text)

    def fired_pitches(self):
        return [pit for _, groups in self.fires for pit in groups]


# -- metronome_timeline -----------------------------------------------------

def test_metronome_timeline_regrids_times():
    tl = [frame(0, 60), frame(2.5, 62), frame(9, 64)]
    m = metronome_timeline(tl, grid_beats=0.5)
    assert [f.time for f in m] == [0.0, 0.5, 1.0]
    assert all(f.duration == 0.5 for f in m)
    assert [f.pitches for f in m] == [(60,), (62,), (64,)]  # preserved


def test_metronome_rejects_bad_grid():
    with pytest.raises(ValueError):
        metronome_timeline([frame(0, 60)], grid_beats=0)


# -- playing (tempo) --------------------------------------------------------

def test_plays_fires_every_onset_once_in_order():
    tl = [frame(0, 60), frame(1, 62), frame(2, 64)]
    clk = FakeClock()
    drv = FakeDriver(clk)
    Transport(tl, 120, fps=12, now=clk.now, sleep=clk.sleep).run(drv)
    assert drv.fired_pitches() == [(60,), (62,), (64,)]


def test_audio_onsets_fire_at_true_times_independent_of_fps():
    # Onsets at beats 0, 1, 3 (a gap). At 60 BPM, 1 beat = 1 s. Even at a very low
    # fps the fires must land at 0/1/3 s, not snapped to the redraw grid.
    tl = [frame(0, 60), frame(1, 62), frame(3, 64)]
    clk = FakeClock()
    drv = FakeDriver(clk)
    Transport(tl, 60, fps=2, now=clk.now, sleep=clk.sleep).run(drv)
    fire_times = [t for t, _ in drv.fires]
    assert fire_times == pytest.approx([0.0, 1.0, 3.0])


def test_total_wall_time_covers_last_note_duration():
    # Last note held for its duration -> total time reaches end (no cutoff).
    tl = [frame(0, 60, duration=1.0), frame(1, 62, duration=2.0)]
    clk = FakeClock()
    Transport(tl, 60, fps=4, now=clk.now, sleep=clk.sleep).run(FakeDriver(clk))
    assert clk.t == pytest.approx(3.0)  # end = 1 + 2 beats @60bpm


def test_renders_advance_and_reach_end():
    tl = [frame(0, 60), frame(1, 62)]
    clk = FakeClock()
    drv = FakeDriver(clk)
    Transport(tl, 60, fps=4, now=clk.now, sleep=clk.sleep).run(drv)
    assert drv.renders[0] == 0.0
    assert drv.renders[-1] == pytest.approx(2.0)  # end held
    assert drv.renders == sorted(drv.renders)     # monotonic


def test_empty_timeline_is_noop():
    drv = FakeDriver(FakeClock())
    Transport([], 120).run(drv)
    assert drv.renders == [] and drv.fires == []


# -- step (paused) ----------------------------------------------------------

def test_step_mode_advances_one_frame_per_dot_key():
    tl = [frame(0, 60), frame(1, 62), frame(2, 64)]
    clk = FakeClock()
    drv = FakeDriver(clk, keys=[".", ".", "q"])  # step, step, quit
    Transport(tl, 120, playing=False, now=clk.now, sleep=clk.sleep).run(drv)
    # initial frame fired + two '.' steps = frames 0,1,2
    assert drv.fired_pitches() == [(60,), (62,), (64,)]
    assert clk.t == 0.0  # step mode never sleeps


def test_space_resumes_from_pause():
    # Regression: space must RESUME continuous play (not single-step forever).
    tl = [frame(float(i), 60 + i) for i in range(4)]
    clk = FakeClock()
    drv = FakeDriver(clk, keys=[" "])  # start paused, space -> resume, plays out
    Transport(tl, 120, playing=False, now=clk.now, sleep=clk.sleep).run(drv)
    assert (63,) in drv.fired_pitches()  # reached the last onset -> resumed


def test_space_pause_then_resume_round_trip():
    tl = [frame(float(i), 60 + i) for i in range(6)]
    clk = FakeClock()
    # playing -> space pauses -> space resumes -> plays to end
    drv = FakeDriver(clk, keys=[" ", " "])
    Transport(tl, 120, playing=True, now=clk.now, sleep=clk.sleep).run(drv)
    assert drv.silences >= 1                 # paused at least once
    assert (65,) in drv.fired_pitches()      # but still reached the end


def test_step_quit_on_q_stops_early():
    tl = [frame(0, 60), frame(1, 62), frame(2, 64)]
    drv = FakeDriver(FakeClock(), keys=["q"])
    Transport(tl, 120, playing=False).run(drv)
    assert drv.fired_pitches() == [(60,)]  # only the initial frame


def test_step_exhausted_keys_stops():
    tl = [frame(0, 60), frame(1, 62)]
    drv = FakeDriver(FakeClock(), keys=[])  # blocking read returns None -> stop
    Transport(tl, 120, playing=False).run(drv)
    assert drv.fired_pitches() == [(60,)]


# -- pause during playback --------------------------------------------------

def test_space_pauses_then_quits():
    tl = [frame(0, 60), frame(1, 62), frame(2, 64)]
    clk = FakeClock()
    # While playing, a space arrives (non-blocking) -> pause + silence; then the
    # paused blocking read returns 'q' -> quit.
    drv = FakeDriver(clk, keys=[" ", "q"])
    Transport(tl, 120, playing=True, now=clk.now, sleep=clk.sleep).run(drv)
    assert drv.silences >= 1  # pause silenced audio


def test_quit_while_playing_stops():
    tl = [frame(0, 60), frame(1, 62), frame(2, 64)]
    clk = FakeClock()
    drv = FakeDriver(clk, keys=["q"])
    Transport(tl, 120, playing=True, now=clk.now, sleep=clk.sleep).run(drv)
    assert drv.fired_pitches() == [(60,)]  # quit before later onsets


def test_invalid_tempo_rejected():
    tl = [frame(0, 60), frame(1, 62)]
    with pytest.raises(ValueError):
        Transport(tl, 0, now=FakeClock().now, sleep=FakeClock().sleep).run(FakeDriver())


# -- transport controls (P4) ------------------------------------------------

def _paused_transport(n=8, bpm4=4.0):
    tl = [frame(float(i), 60 + i) for i in range(n)]
    clk = FakeClock()
    t = Transport(tl, 120, playing=False, beats_per_measure=bpm4,
                  now=clk.now, sleep=clk.sleep)
    return t, FakeDriver(clk)


def test_seek_right_advances_one_bar():
    t, drv = _paused_transport()
    t._handle_key("right", drv)
    assert t.beat_time == 4.0
    assert drv.silences >= 1  # seek resyncs audio


def test_seek_left_clamps_to_start():
    t, drv = _paused_transport()
    t.beat_time = 2.0
    t._handle_key("left", drv)   # 2 - 4 -> clamp to start (0)
    assert t.beat_time == 0.0


def test_jump_to_end_and_start():
    t, drv = _paused_transport()
    t._handle_key("end", drv)
    assert t.beat_time == t.end
    t._handle_key("g", drv)
    assert t.beat_time == t.start


def test_tempo_up_and_down():
    t, drv = _paused_transport()
    base = t.tempo
    t._handle_key("]", drv)
    assert t.tempo > base
    up = t.tempo
    t._handle_key("[", drv)
    assert t.tempo < up


def test_tempo_clamped():
    t, drv = _paused_transport()
    for _ in range(50):
        t._handle_key("]", drv)
    assert t.tempo <= 400.0
    for _ in range(100):
        t._handle_key("[", drv)
    assert t.tempo >= 20.0


def test_step_back_moves_to_previous_onset():
    t, drv = _paused_transport()
    t._fire_due(drv)          # run() fires frame 0 at start (onset_i -> 1)
    t._handle_key(".", drv)   # -> frame 1 (beat 1)
    t._handle_key(".", drv)   # -> frame 2 (beat 2)
    assert t.beat_time == 2.0
    t._handle_key(",", drv)   # back to beat 1
    assert t.beat_time == 1.0


def test_help_overlay_shown():
    t, drv = _paused_transport()
    t._handle_key("h", drv)
    assert getattr(drv, "shown", []) and "keys" in drv.shown[0].lower()


def test_seek_while_playing_is_not_clobbered():
    # Regression: seeking during playback must move the playhead, not be reverted
    # by the loop's `self.beat_time = t` (computed before the key).
    tl = [frame(float(i), 60 + i) for i in range(8)]
    clk = FakeClock()
    drv = FakeDriver(clk, keys=["right", "q"])  # seek +1 bar early, then quit
    t = Transport(tl, 120, playing=True, beats_per_measure=4.0,
                  now=clk.now, sleep=clk.sleep)
    t.run(drv)
    assert t.beat_time >= 4.0  # jumped a bar forward, not reverted toward 0


def test_help_pauses_and_persists_during_play():
    # Regression: 'h' while playing must pause (so the overlay isn't repainted
    # over within the same iteration) and actually show the help.
    tl = [frame(float(i), 60 + i) for i in range(4)]
    clk = FakeClock()
    drv = FakeDriver(clk, keys=["h", "q"])
    Transport(tl, 120, playing=True, now=clk.now, sleep=clk.sleep).run(drv)
    assert getattr(drv, "shown", []) and drv.silences >= 1


def test_resize_rerenders():
    t, drv = _paused_transport()
    before = len(drv.renders)
    t._handle_key("<resize>", drv)
    assert len(drv.renders) == before + 1
