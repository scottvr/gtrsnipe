"""B24: string lines in the forms tabs in the wild use (classtab.org among them)."""
from gtrsnipe.formats import tab

STD = [64, 59, 55, 50, 45, 40]


def _pitches(text):
    song = tab.AsciiTabParser.parse(text, open_string_pitches=STD, quantization_resolution=0.125)
    return [e.pitch for t in song.tracks for e in sorted(t.events, key=lambda e: (e.time, e.pitch))]


LABELED = """e|--0--3--|
B|--------|
G|--------|
D|--------|
A|--------|
E|--------|
"""


def test_the_three_label_free_forms_read_like_the_labeled_one():
    want = _pitches(LABELED)
    assert want == [64, 67]
    unlabeled = "".join(l.split("|", 1)[1] and ("|" + l.split("|", 1)[1]) + "\n" for l in LABELED.splitlines())
    assert _pitches(unlabeled) == want
    double = unlabeled.replace("|--", "||--", 6)
    assert _pitches(double) == want
    no_bar = "".join(l[0] + l[1:].replace("|", "") + "\n" for l in LABELED.splitlines())      # E--0--3--
    assert _pitches(no_bar) == want
    bare = "".join(l[1:].replace("|", "") + "\n" for l in LABELED.splitlines())             # --0--3--
    assert _pitches(bare) == want


def test_a_rule_of_dashes_is_not_a_string():
    text = "Some title\n------------------------\n\n" + LABELED
    assert _pitches(text) == [64, 67]


def test_label_with_a_space_before_the_bar():
    text = "".join(l[0] + " " + l[1:] + "\n" for l in LABELED.splitlines())                 # e |--0--3--|
    assert _pitches(text) == [64, 67]


def test_classtab_sustain_marks_are_not_notes():
    text = LABELED.replace("--0--3--", "--0==3==")
    assert _pitches(text) == [64, 67]


def test_a_beat_line_with_a_bar_is_not_a_string():
    text = "5  |   .   |   .   |\n" + LABELED
    assert _pitches(text) == [64, 67]


def test_a_repeat_mark_after_the_bar_is_still_a_string():
    text = LABELED.replace("G|--", "G|*-").replace("D|--", "D|*-")
    assert _pitches(text) == [64, 67]
