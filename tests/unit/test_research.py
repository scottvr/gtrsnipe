"""Research tools (backlog R01, R02): corpus readers, the melody cache, the offset
profile and the gtrsnipe-research CLI. Everything here builds its own tiny
corpora; the real ones live outside the repo."""
import gzip
import json
import math
import random

import mido
import pytest

from gtrsnipe.research import corpus as C
from gtrsnipe.research.cli import main as research_main
from gtrsnipe.research.offsets import offset_profile, profile_of_deltas, profile_songs

Q = C.TPQ

KERN = """!!!OTL: Test Song
**kern
*M3/4
*G:
=1
{8d
8g
4g
[4a
=2
4a]
8.r}
{16B-
=3
4cc#
qd
2CC
4r
=4
2dd
[4ee
=5
4ee]}
*-
"""


def kern(body):
    return C.parse_kern("**kern\n" + body + "\n*-\n")


# -- kern -----------------------------------------------------------------------

def test_kern_pitches_durations_ties_and_phrases():
    m = C.parse_kern(KERN, "t", "x")
    assert m.title == "Test Song" and m.meter == "3/4" and m.key == "G"
    # the tied a (4 + 4) is one note; the grace note q is skipped
    assert m.pitches == [62, 67, 67, 69, 58, 73, 36, 74, 76]
    assert m.durations == [Q // 2, Q // 2, Q, 2 * Q, Q // 4, Q, 2 * Q, 2 * Q, 2 * Q]
    assert m.onsets == [0, Q // 2, Q, 2 * Q, 4 * Q + 3 * Q // 4, 5 * Q, 6 * Q, 9 * Q, 11 * Q]
    assert m.phrases == [0, 4]                  # phrase 2 starts at B-, after the rest
    held = kern("[4c\n4c_\n=\n4c]\n4d")
    assert held.pitches == [60, 62] and held.durations == [3 * Q, Q]


def test_kern_octaves_accidentals_and_rare_durations():
    m = kern("4c\n4cc\n4C\n4CC\n4c#\n4c--\n4cn\n12e\n12e\n12e\n0f\n3%2g\n4.a\n8..b")
    assert m.pitches == [60, 72, 48, 36, 61, 58, 60, 64, 64, 64, 65, 67, 69, 71]
    assert m.durations[7:] == [Q // 3] * 3 + [8 * Q, 8 * Q // 3, 3 * Q // 2, 7 * Q // 8]


def test_kern_phrase_mark_on_a_grace_note_or_rest_carries_to_the_next_note():
    assert kern("4c\n{qd\n4e\n4f").phrases == [1]
    assert kern("4c\n{4r\n4e}").phrases == [1]


def test_kern_chord_keeps_its_top_note():
    m = kern("4c 4e 4g\n4d")
    assert m.pitches == [67, 62] and m.dropped == 2


def test_kern_reads_the_first_kern_spine_only():
    text = "**text\t**kern\t**kern\n*\t*M2/4\t*\nla\t4c\t4e\n.\t4d\t.\nli\t2e\t4f\n*-\t*-\t*-\n"
    m = C.parse_kern(text)
    assert m.pitches == [60, 62, 64] and m.onsets == [0, Q, 2 * Q] and m.meter == "2/4"


# -- skyline / ABC / MIDI ---------------------------------------------------------

def test_skyline_keeps_the_top_note_and_cuts_at_the_next_onset():
    line, dropped = C.skyline([(0, 960, 60), (0, 480, 72), (240, 960, 50), (480, 1920, 55)])
    assert line == [(0, 240, 72), (240, 240, 50), (480, 1440, 55)] and dropped == 1


def test_abc_files_yield_every_tune_with_the_file_header(tmp_path):
    f = tmp_path / "set.abc"
    f.write_text("%abc-2.1\n\nX:1\nT:One\nM:6/8\nL:1/8\nK:G\n^F F|\n\n"
                 "X:2\nT:Two\nM:4/4\nL:1/4\nK:C\n[CEG] D\n\nX:2\nT:Again\nK:C\nE\n")
    mels = C.read_abc_file(str(f), "set.abc", "c")
    assert [m.id for m in mels] == ["set#1", "set#2", "set#2.2"]
    assert [m.title for m in mels] == ["One", "Two", "Again"]
    assert mels[0].pitches == [66, 66]           # %abc-2.1: the sharp carries in the bar
    assert mels[0].meter == "6/8" and mels[0].key == "G"
    assert mels[1].pitches == [67, 62] and mels[1].dropped == 2


def _midi(tmp_path, tracks, name="m.mid", tpb=480):
    mf = mido.MidiFile(ticks_per_beat=tpb)
    for tname, ch, notes in tracks:
        tr = mido.MidiTrack()
        if tname:
            tr.append(mido.MetaMessage("track_name", name=tname, time=0))
        t = 0
        evs = sorted([(on, 1, p) for on, _, p in notes] + [(off, 0, p) for _, off, p in notes])
        for tick, is_on, p in evs:
            tr.append(mido.Message("note_on" if is_on else "note_off", channel=ch, note=p,
                                   velocity=90 if is_on else 0, time=tick - t))
            t = tick
        mf.tracks.append(tr)
    path = tmp_path / name
    mf.save(path)
    return path


def test_midi_prefers_a_melody_named_part(tmp_path):
    p = _midi(tmp_path, [("Piano", 0, [(0, 960, 72), (0, 960, 76)]),
                         ("Lead Vocal", 1, [(0, 480, 60), (480, 960, 62)]),
                         ("Backing Vocals", 2, [(0, 960, 80)])])
    (m,) = C.read_midi_file(str(p), "Artist/Song.mid", "lakh-clean")
    assert m.source == "midi:track Lead Vocal" and m.pitches == [60, 62]
    assert m.onsets == [0, Q] and m.artist == "Artist" and m.title == "Song"


def test_midi_without_a_melody_part_takes_the_skyline_without_drums(tmp_path):
    p = _midi(tmp_path, [("Bass", 0, [(0, 960, 40), (960, 1920, 43)]),
                         ("Strings", 1, [(0, 1920, 64)]),
                         ("Drums", 9, [(0, 120, 90), (960, 1080, 90)])], tpb=960)
    (m,) = C.read_midi_file(str(p), "x.mid", "c")
    assert m.source == "midi:skyline" and m.pitches == [64, 43]
    assert m.durations == [Q, Q]                # the strings note is cut at the next onset


# -- the cache ------------------------------------------------------------------------

@pytest.fixture
def essen_root(tmp_path):
    d = tmp_path / "essen" / "europa"
    d.mkdir(parents=True)
    (d / "a1.krn").write_text(KERN)
    (d / "a2.krn").write_text("**kern\n{4c\n4d\n4e}\n{4f\n4g}\n*-\n")
    (d / "._a3.krn").write_bytes(b"\x00\x05\x16\x07AppleDouble junk")
    return tmp_path


def test_build_and_read_cache_round_trip(essen_root):
    h = C.build("essen", root=str(essen_root), workers=1)
    assert (h["files"], h["melodies"], h["errors"]) == (2, 2, 0)     # ._ file skipped
    path = C.default_cache("essen", str(essen_root))
    header, mels = C.read_cache(path)
    assert header["corpus"] == "essen" and header["tpq"] == Q
    assert [m.id for m in mels] == ["europa/a1", "europa/a2"]
    assert mels[1].phrase_spans() == [(0, 3), (3, 5)]
    assert C.find(mels, "a2") is mels[1]
    with gzip.open(path, "rt") as f:            # a header member, then the melodies
        assert json.loads(f.readline())["format"] == C.CACHE_FORMAT


def test_find_rejects_ambiguous_and_missing_ids():
    mels = [C.Melody(i, "c", [60], [0], [Q]) for i in ("x/a1", "y/a1", "z/b")]
    assert C.find(mels, "z/b").id == "z/b"
    with pytest.raises(ValueError, match="ambiguous"):
        C.find(mels, "a1")
    with pytest.raises(ValueError, match="no melody"):
        C.find(mels, "c9")


def test_slice_rebases_time_and_phrases():
    m = C.parse_kern("**kern\n{4c\n4d\n4e}\n{4f\n4g}\n*-\n", "essen", "t")
    s = m.slice(2, 5)
    assert s.pitches == [64, 65, 67] and s.onsets == [0, Q, 2 * Q] and s.phrases == [1]
    song = s.to_song()
    assert [e.time for e in song.tracks[0].events] == [0.0, 1.0, 2.0]


# -- offset profile (R02) -------------------------------------------------------------

@pytest.mark.parametrize("deltas,r,S,u", [          # the structure note's section 6 table
    ([5] * 8, 1, 0, 0),
    ([5, 5, 5, 5, 7, 7, 7, 7], 2, 1, 0),
    ([5, 7] * 4, 2, 7, 6),
    ([0, 6] * 4, 2, 7, 6),
])
def test_richness_switches_and_reuse(deltas, r, S, u):
    p = profile_of_deltas(deltas)
    assert (p.richness, p.switches, p.reuse) == (r, S, u)


def test_entropy_coverage_and_variation():
    p = offset_profile([60, 62, 64, 65, 67, 69, 71, 72], [60, 64, 64, 69, 67, 72, 71, 76])
    assert p.deltas == [0, 2, 0, 4, 0, 3, 0, 4]
    assert p.richness == 4 and p.coverage[:4] == [0.5, 0.75, 0.875, 1.0]
    assert p.entropy == pytest.approx(1.75) and p.ti_hamming == 0.5
    assert p.total_variation == 2 + 2 + 4 + 4 + 3 + 3 + 4 and p.switches == 7
    assert p.richness_mod12 == 4


def test_profile_is_transposition_invariant_and_agrees_with_the_solver():
    from gtrsnipe.guitar.homograph import parse_inline, richness
    a = parse_inline("C4 D4 E4 C4 E4 F4 G4:2")
    b = parse_inline("G4 A4 G4 E4 C5 A4 G4:2")
    up = parse_inline("A4 B4 A4 F#4 D5 B4 A4:2")
    p, _ = profile_songs(a, b)
    q, _ = profile_songs(a, up)
    assert p.richness == richness(a, b) == q.richness
    assert (p.entropy, p.switches, p.total_variation) == (q.entropy, q.switches, q.total_variation)


def test_profile_songs_reports_why_melodies_do_not_align():
    from gtrsnipe.guitar.homograph import parse_inline
    p, why = profile_songs(parse_inline("C4 D4"), parse_inline("C4 D4 E4"))
    assert p is None and "onsets" in why


def test_log_richness_and_entropy_obey_the_triangle_inequality():
    rng = random.Random(7)
    for _ in range(300):
        n = rng.randint(2, 12)
        a, b, c = ([rng.randint(55, 70) for _ in range(n)] for _ in range(3))
        ab, bc, ac = offset_profile(a, b), offset_profile(b, c), offset_profile(a, c)
        assert ac.log_richness <= ab.log_richness + bc.log_richness + 1e-9
        assert ac.entropy <= ab.entropy + bc.entropy + 1e-9
        assert ac.ti_hamming <= ab.ti_hamming + bc.ti_hamming + 1e-9
        assert ac.switches <= ab.switches + bc.switches


# -- CLI ------------------------------------------------------------------------------

def test_cli_profile_inline(capsys):
    assert research_main(["profile", "C4 D4 E4 F4", "C4 E4 E4 A4"]) == 0
    out = capsys.readouterr().out
    assert "Richness       3" in out and "Sequence       +0, +2, +0, +4" in out


def test_cli_profile_corpus_refs_phrases_and_json(essen_root, capsys):
    C.build("essen", root=str(essen_root), workers=1)
    data = ["--data", str(essen_root)]
    assert research_main(data + ["profile", "essen:a2#p1", "essen:a2@1-3", "--json"]) == 0
    d = json.loads(capsys.readouterr().out)
    assert d["richness"] == 1 and d["a"] == "essen:europa/a2#p1"
    assert research_main(data + ["corpus", "show", "essen:a2"]) == 0
    assert "C4 D4 E4 | F4 G4" in capsys.readouterr().out
    assert research_main(data + ["corpus", "info", "essen"]) == 0
    assert "2 melodies" in capsys.readouterr().out


def test_cli_explains_a_missing_cache(tmp_path, capsys):
    assert research_main(["--data", str(tmp_path), "profile", "essen:x", "C4"]) == 2
    assert "corpus build essen" in capsys.readouterr().err
