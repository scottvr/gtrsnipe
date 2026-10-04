"""C03: shape-relative chord names (--shape-names), the "generalized capo"."""
import sys

import pytest

from gtrsnipe.chords.chart import build_chord_sheet
from gtrsnipe.chords.shape_names import shape_naming, shape_naming_for_config, transpose
from gtrsnipe.core.chords import identify
from gtrsnipe.core.config import MapperConfig
from gtrsnipe.core.theory import note_name_to_pitch as n
from gtrsnipe.core.types import MusicalEvent, Song, Track
from gtrsnipe.formats.tab.generator.ascii import AsciiTabGenerator

G_MAJOR = identify([n(x) for x in ("G2", "B2", "D3", "G3")], bass=n("G2"))


@pytest.mark.parametrize("tuning, capo, strings, shape", [
    ("STANDARD", 0, 6, "G"),          # standard, no capo: shape = concert
    ("STANDARD", 2, 6, "F"),          # a capo: the classic capo reading
    ("BARITONE_B", 0, 6, "C"),        # -5: a sounding G is a C shape
    ("E_FLAT", 0, 6, "Ab"),           # no key given: a root is spelled in its own key
    ("BARITONE_A", 0, 6, "D"),
    ("BASS_E_FLAT", 0, 4, "Ab"),      # compared with BASS_STANDARD
])
def test_uniform_tunings_name_shapes(tuning, capo, strings, shape):
    naming = shape_naming_for_config(MapperConfig(tuning=tuning, capo=capo, num_strings=strings))
    assert naming.active and naming.name(G_MAJOR) == shape and naming.banner


@pytest.mark.parametrize("tuning, strings", [("DROP_D", 6), ("OPEN_G", 6), ("DADGAD", 6),
                                             ("SEVEN_STRING_DROP_A", 7)])
def test_drop_and_open_tunings_fall_back_to_concert_pitch_and_say_so(tuning, strings):
    naming = shape_naming_for_config(MapperConfig(tuning=tuning, num_strings=strings))
    assert not naming.active and naming.name(G_MAJOR) == "G"
    assert "concert pitch" in naming.banner and "shifted evenly" in naming.banner


def test_a_custom_tuning_that_is_a_uniform_shift_counts():
    naming = shape_naming(["C#2", "F#2", "B2", "E3", "G#3", "C#4"], 0, "this tuning")
    assert naming.active and naming.name(G_MAJOR) == "Bb"            # sounds 3 lower
    assert not shape_naming(["D2", "A2", "D3"], 0).active             # no 3-string standard


def test_transpose_moves_root_and_bass():
    c_over_e = identify([n("E2"), n("C3"), n("G3")], bass=n("E2"))
    assert transpose(c_over_e, 2).name == "D/F#"


def block(t, names):
    return [MusicalEvent(t, n(x), 4.0, 90) for x in names.split()]


def progression():
    events = block(0, "G2 B2 D3 G3") + block(4, "C3 E3 G3 C4")
    return Song(tracks=[Track(events=events)], title="p")


def test_chart_labels_change_but_diagrams_do_not():
    cfg = MapperConfig(tuning="BARITONE_B")
    concert = build_chord_sheet(progression(), cfg)
    shaped = build_chord_sheet(progression(), cfg, shape_names=True)
    assert "| G " in concert and "| C " in shaped and "Shape names:" in shaped
    diagrams = lambda sheet: sheet.split("## Chords used", 1)[1].split("```")[1::2]
    assert diagrams(concert) == diagrams(shaped)                    # the same notes to play


def test_tab_names_and_header_banner():
    cfg = MapperConfig(tuning="BARITONE_B")
    text = AsciiTabGenerator.generate(progression(), "", max_line_width=200, mapper_config=cfg,
                                      name_chords=True, shape_names=True)
    names = [l for l in text.splitlines() if l.strip() and "|" not in l and not l.startswith("//")]
    assert names[0].split() == ["C", "F"]
    assert any(l.startswith("// Shape names:") for l in text.splitlines())


def test_cli_name_chord_shows_the_shape(monkeypatch, capsys):
    from gtrsnipe.converter import main
    monkeypatch.setattr(sys, "argv", ["gtrsnipe", "--tuning", "BARITONE_B", "--shape-names",
                                      "--name-chord", "x,3,2,0,1,0"])
    with pytest.raises(SystemExit):
        main()
    out = capsys.readouterr().out
    assert "shape: C" in out and " G " in out and "Shape names:" in out
