"""Tests for the player clocks (pure scheduling policy, no I/O)."""
import pytest

from gtrsnipe.core.types import FretPosition
from gtrsnipe.player.clock import (
    MetronomeClock,
    RealtimeClock,
    StepClock,
    make_clock,
)
from gtrsnipe.player.frame import Frame


def frame(time, duration, fret=3):
    return Frame(time=time, duration=duration,
                 positions=(FretPosition(0, fret),), window=(1, 5))


TL = [frame(0, 1.0), frame(1, 0.5), frame(1.5, 2.0)]


def test_realtime_uses_frame_durations_in_seconds():
    # 120 BPM -> 1 beat = 0.5 s
    sched = RealtimeClock().schedule(TL, tempo_bpm=120)
    delays = [d for _, d in sched]
    assert delays[0] == pytest.approx(0.5)   # 1.0 beat
    assert delays[1] == pytest.approx(0.25)  # 0.5 beat
    # The last frame now dwells for its OWN duration (2.0 beats @120 = 1.0 s) so
    # its note is held, not cut off when playback ends.
    assert delays[-1] == pytest.approx(1.0)


def test_realtime_scales_with_tempo():
    fast = [d for _, d in RealtimeClock().schedule(TL, 240)][0]
    slow = [d for _, d in RealtimeClock().schedule(TL, 60)][0]
    assert fast == pytest.approx(0.25)
    assert slow == pytest.approx(1.0)


def test_metronome_gives_every_frame_the_same_interval():
    sched = MetronomeClock(grid_beats=0.5).schedule(TL, tempo_bpm=120)
    delays = [d for _, d in sched]
    assert delays[0] == pytest.approx(0.25)  # 0.5 beat @120 = 0.25 s
    assert delays[1] == pytest.approx(0.25)  # same regardless of frame duration
    assert delays[-1] == pytest.approx(0.25)  # last frame dwells too


def test_step_never_auto_advances():
    sched = StepClock().schedule(TL, tempo_bpm=120)
    assert all(d is None for _, d in sched)
    assert [f for f, _ in sched] == TL


def test_schedule_preserves_frames_in_order():
    for clock in (RealtimeClock(), MetronomeClock(), StepClock()):
        sched = clock.schedule(TL, tempo_bpm=120)
        assert [f for f, _ in sched] == TL


def test_empty_timeline_is_empty_schedule():
    for clock in (RealtimeClock(), MetronomeClock(), StepClock()):
        assert clock.schedule([], tempo_bpm=120) == []


def test_invalid_tempo_raises():
    with pytest.raises(ValueError):
        RealtimeClock().schedule(TL, tempo_bpm=0)


def test_make_clock_factory():
    assert isinstance(make_clock("tempo"), RealtimeClock)
    assert isinstance(make_clock("step"), StepClock)
    m = make_clock("metronome", grid_beats=0.25)
    assert isinstance(m, MetronomeClock)
    assert m.grid_beats == 0.25


def test_make_clock_rejects_unknown():
    with pytest.raises(ValueError):
        make_clock("nope")
