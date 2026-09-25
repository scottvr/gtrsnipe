"""Tests for the player TimelineBuilder (frames + auto-follow viewport).

The timeline is the load-bearing pure layer: mapped events in, ordered Frames
out, with an auto-follow window that tracks the fretted notes. These tests pin
grouping, duration tiling, and the window hysteresis on known inputs.
"""
import pytest

from gtrsnipe.core.config import MapperConfig
from gtrsnipe.core.types import FretPosition, MusicalEvent, Song, Track
from gtrsnipe.guitar.mapper import GuitarMapper
from gtrsnipe.player.timeline import DEFAULT_WINDOW_SIZE, TimelineBuilder


def mev(time, string, fret, duration=0.5, pitch=60):
    return MusicalEvent(time=time, pitch=pitch, duration=duration,
                        velocity=100, string=string, fret=fret)


def make_builder(window_size=DEFAULT_WINDOW_SIZE, **cfg):
    return TimelineBuilder(MapperConfig(**cfg), window_size=window_size)


# -- basic shape ------------------------------------------------------------

def test_empty_input_returns_no_frames():
    assert make_builder().build([]) == []


def test_unmapped_events_are_skipped():
    builder = make_builder()
    events = [MusicalEvent(time=0, pitch=60, duration=0.5, velocity=100)]  # no str/fret
    assert builder.build(events) == []


def test_one_note_one_frame():
    frames = make_builder().build([mev(0, 0, 3)])
    assert len(frames) == 1
    assert frames[0].positions == (FretPosition(0, 3),)


def test_notes_at_same_onset_group_into_one_frame():
    frames = make_builder().build([mev(0, 0, 3), mev(0, 1, 5), mev(0, 2, 2)])
    assert len(frames) == 1
    assert frames[0].positions == (
        FretPosition(0, 3), FretPosition(1, 5), FretPosition(2, 2),
    )


def test_positions_are_deduplicated_and_sorted():
    frames = make_builder().build([mev(0, 2, 2), mev(0, 0, 3), mev(0, 2, 2)])
    # sorted by (string, fret); duplicate collapsed
    assert frames[0].positions == (FretPosition(0, 3), FretPosition(2, 2))


def test_distinct_onsets_make_distinct_frames_in_time_order():
    frames = make_builder().build([mev(2, 0, 5), mev(0, 0, 3), mev(1, 0, 4)])
    assert [f.time for f in frames] == [0.0, 1.0, 2.0]
    assert [f.positions[0].fret for f in frames] == [3, 4, 5]


def test_onsets_within_quantization_grid_merge():
    builder = make_builder(quantization_resolution=0.25)
    # 0.0 and 0.05 both round to 0.0 -> one frame
    frames = builder.build([mev(0.0, 0, 3), mev(0.05, 1, 5)])
    assert len(frames) == 1


# -- duration tiling --------------------------------------------------------

def test_frame_durations_tile_to_next_onset():
    frames = make_builder().build([mev(0, 0, 3, duration=0.1),
                                   mev(1, 0, 4, duration=0.1),
                                   mev(3, 0, 5, duration=0.1)])
    assert frames[0].duration == pytest.approx(1.0)   # gap 0 -> 1
    assert frames[1].duration == pytest.approx(2.0)   # gap 1 -> 3


def test_last_frame_uses_its_note_duration():
    frames = make_builder().build([mev(0, 0, 3, duration=0.5),
                                   mev(1, 0, 4, duration=2.5)])
    assert frames[-1].duration == pytest.approx(2.5)


def test_last_frame_duration_never_below_grid():
    builder = make_builder(quantization_resolution=0.25)
    frames = builder.build([mev(0, 0, 3, duration=0.0)])
    assert frames[-1].duration == pytest.approx(0.25)


# -- auto-follow window -----------------------------------------------------

def test_window_default_span_is_window_size():
    frames = make_builder(window_size=5).build([mev(0, 0, 3)])
    lo, hi = frames[0].window
    assert hi - lo + 1 == 5


def test_window_holds_still_while_notes_stay_inside():
    frames = make_builder(window_size=5).build([
        mev(0, 0, 2), mev(1, 0, 3), mev(2, 0, 5),  # all within 1..5
    ])
    assert all(f.window == (1, 5) for f in frames)


def test_window_follows_up_when_a_note_climbs_out():
    frames = make_builder(window_size=5).build([
        mev(0, 0, 3),   # window 1..5
        mev(1, 0, 7),   # 7 > 5 -> shift up so 7 is the top: 3..7
    ])
    assert frames[0].window == (1, 5)
    assert frames[1].window == (3, 7)


def test_window_follows_down_when_a_note_drops_out():
    frames = make_builder(window_size=5).build([
        mev(0, 0, 12),  # minimal-shift up so 12 is the top: 8..12
        mev(1, 0, 3),   # 3 < 8 -> follow down to 3: 3..7
    ])
    assert frames[0].window == (8, 12)
    assert frames[1].window == (3, 7)


def test_window_minimal_shift_is_hysteretic():
    # Once shifted up to see fret 7, a return to fret 5 stays in the 3..7 window
    # rather than snapping back to 1..5.
    frames = make_builder(window_size=5).build([
        mev(0, 0, 3),   # 1..5
        mev(1, 0, 7),   # 3..7
        mev(2, 0, 5),   # still inside 3..7 -> no move
    ])
    assert frames[2].window == (3, 7)


def test_open_strings_never_move_the_window():
    frames = make_builder(window_size=5).build([
        mev(0, 0, 3),   # 1..5
        mev(1, 0, 0),   # open string: window unchanged
    ])
    assert frames[1].window == (1, 5)


def test_note_wider_than_window_anchors_low():
    # A single group spanning more than the window width can't fit; anchor at
    # the lowest fret so the window is deterministic.
    frames = make_builder(window_size=5).build([
        mev(0, 0, 2), mev(0, 5, 9),  # span 2..9 = 8 > 5
    ])
    assert frames[0].window == (2, 6)


# -- Song / integration -----------------------------------------------------

def test_build_from_song_merges_all_tracks():
    builder = make_builder()
    song = Song(tracks=[
        Track(events=[mev(0, 0, 3)]),
        Track(events=[mev(0, 1, 5)]),
    ])
    frames = builder.build_from_song(song)
    assert len(frames) == 1
    assert frames[0].positions == (FretPosition(0, 3), FretPosition(1, 5))


def test_end_to_end_with_real_mapper():
    # A real melody through the real mapper -> timeline. Sanity: frames are in
    # order, tile the timeline, and every position is on a valid string.
    cfg = MapperConfig(tuning="STANDARD", num_strings=6)
    mapper = GuitarMapper(cfg)
    events = [MusicalEvent(time=float(i), pitch=p, duration=0.5, velocity=100)
              for i, p in enumerate([64, 65, 67, 69, 71])]
    mapped = mapper.map_events_to_fretboard(events, no_articulations=True)
    frames = TimelineBuilder(cfg).build(mapped)
    assert frames
    assert [f.time for f in frames] == sorted(f.time for f in frames)
    for f in frames:
        for p in f.positions:
            assert 0 <= p.string < 6
            assert p.fret >= 0
            lo, hi = f.window
            if p.fret > 0:
                assert lo <= p.fret <= hi
