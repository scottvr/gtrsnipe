"""String physics (gtrsnipe.guitar.strings): tension, breaking pitch, playable
range. Calibrated against D'Addario's published EXL110 tensions."""
import pytest

from gtrsnipe.guitar.strings import (
    Gauge, breaking_pitch_hz, default_instrument, hz, parse_gauges, restring,
    stress_fraction, tension_lb,
)

STD_HIGH_TO_LOW = [64, 59, 55, 50, 45, 40]


@pytest.mark.parametrize("gauge,wound,pitch,published", [
    (.010, False, 64, 16.2), (.013, False, 59, 15.4), (.017, False, 55, 16.6),
    (.026, True, 50, 18.4), (.036, True, 45, 19.5), (.046, True, 40, 17.5),
])
def test_tension_matches_published_exl110(gauge, wound, pitch, published):
    assert tension_lb(Gauge(gauge, wound), pitch, 25.5) == pytest.approx(published, rel=0.03)


def test_plain_steel_breaking_pitch_is_gauge_independent():
    # stress = rho (2 L f)^2 for plain steel: any gauge breaks at the same pitch
    assert stress_fraction(Gauge(.009, False), 64, 25.5) == pytest.approx(
        stress_fraction(Gauge(.012, False), 64, 25.5))
    assert 425 < breaking_pitch_hz(25.5) < 440          # 90% of UTS: just under A4 at 25.5"
    assert breaking_pitch_hz(24.75) > breaking_pitch_hz(25.5)   # shorter scale: higher


def test_high_e_limits():
    inst = default_instrument("STANDARD", STD_HIGH_TO_LOW)
    assert inst.assess(0, 66).status == "ok"             # F#4
    assert inst.assess(0, 68).status == "tight"          # G#4: snap risk
    assert inst.assess(0, 69).status == "impossible"     # A4: no steel string holds it
    assert inst.assess(0, 69).suggestion is None


def test_down_tuning_never_breaks_but_goes_slack():
    inst = default_instrument("STANDARD", STD_HIGH_TO_LOW)
    assert inst.assess(5, 35).status == "ok"             # low E down to B1 (-5)
    st = inst.assess(5, 33)                              # A1 (-7): floppy
    assert st.status == "slack" and st.suggestion is not None
    assert st.suggestion[0].inches > .046                # a heavier string


def test_the_plus_ten_a_string_is_flagged():
    inst = default_instrument("STANDARD", STD_HIGH_TO_LOW)
    st = inst.assess(4, 55)                              # A2 -> G3
    assert st.status == "breaks" and st.suggestion is not None
    assert st.suggestion[0].inches < .036                # a lighter string would hold it


def test_restring_targets_the_old_feel():
    g, t = restring(66, 16.3, 25.5)                      # F#4 at the high E's feel
    assert not g.wound and g.inches < .010 and t == pytest.approx(16.3, abs=2.0)
    # G4 is past the snap-risk line for EVERY plain gauge at 25.5": no fix exists
    assert restring(67, 16.3, 25.5) is None


def test_parse_gauges_orders_low_to_high():
    # thin->thick set notation is flipped; thick->thin is already low->high
    got = parse_gauges("10 13 17 26w 36w 46")
    assert [str(g) for g in got] == [".046w", ".036w", ".026w", ".017", ".013", ".010"]
    assert [str(g) for g in parse_gauges(".046w,.010")] == [".046w", ".010"]
    assert not parse_gauges(".010")[0].wound
    with pytest.raises(ValueError):
        parse_gauges("ten")


def test_parse_gauges_keeps_a_reentrant_set_in_order():
    # review: sorting put Nashville's .014 (B3) and .009 (G4) on the wrong strings
    nashville = parse_gauges(".023p .018 .012 .009 .014 .010")   # E3 A3 D4 G4 B3 E4
    assert [str(g) for g in nashville] == [".023", ".018", ".012", ".009", ".014", ".010"]


@pytest.mark.parametrize("tuning,pitches,gauges", [
    ("STANDARD", STD_HIGH_TO_LOW, None),
    ("STANDARD", STD_HIGH_TO_LOW, "12 16 24w 32w 42w 53w"),      # acoustic, wound G
    ("STANDARD", STD_HIGH_TO_LOW, "11 15 22w 30w 42w 52w"),
    ("STANDARD", STD_HIGH_TO_LOW, "12 16 24w 32w 42w 52w"),      # jazz
    ("BASS_STANDARD", [43, 38, 33, 28], None),
    ("SEVEN_STRING_STANDARD", [64, 59, 55, 50, 45, 40, 35], None),
    ("BARITONE_B", [59, 54, 50, 45, 40, 35], None),
    ("DROP_C", [62, 57, 53, 48, 43, 36], None),
    ("C_SHARP_STANDARD", [61, 56, 52, 47, 42, 37], None),
    ("CUSTOM", [64, 59, 55, 50, 45, 40, 35, 30], None),           # 8-string F#1..E4
    ("CUSTOM", [48, 43, 38, 33, 28, 23], None),                   # 6-string bass B0..C3
    ("CUSTOM", [59, 54, 50, 45, 40, 33], None),                   # A1 baritone
])
def test_every_default_or_common_set_is_ok_at_its_own_tuning(tuning, pitches, gauges):
    # review: a wound G at G3 was "past its breaking point"; an 8-string's high E
    # was "impossible" (given a 34" bass scale); a bass C3 was "tight".
    inst = default_instrument(tuning, pitches,
                              gauges_low_to_high=parse_gauges(gauges) if gauges else None)
    for s, p in enumerate(pitches):
        st = inst.assess(s, p)
        assert st.status == "ok", (tuning, s, p, st)


def test_extended_range_guitar_gets_a_guitar_scale():
    assert default_instrument("CUSTOM", [64, 59, 55, 50, 45, 40, 35, 30]).scale_in == 27.0
    assert default_instrument("CUSTOM", [48, 43, 38, 33, 28, 23]).scale_in == 34.0


def test_same_string_same_pitch_same_verdict_across_named_tunings():
    # review: under DROP_C a 10-46 set's .046w at E2 was "too tight" (its "normal"
    # was the dropped C2). Now a non-design tuning gets a set designed for it.
    dropc = default_instrument("DROP_C", [62, 57, 53, 48, 43, 36])
    assert dropc.name == "balanced"
    assert all(15 < dropc.normal_tension(s) < 19 for s in range(6))


def test_wound_strings_judged_by_tension():
    inst = default_instrument("STANDARD", STD_HIGH_TO_LOW)
    assert inst.assess(3, 55).status == "tight"          # D string up a fourth: 178% tension
    assert inst.assess(3, 57).status == "breaks"         # up a fifth: over 2x tension
    assert inst.assess(3, 55).stress is None             # wound: no fake stress figure
    assert inst.assess(2, 59).stress is not None         # plain: real stress


def test_default_instruments():
    assert default_instrument("STANDARD", STD_HIGH_TO_LOW).scale_in == 25.5
    assert default_instrument("BASS_STANDARD", [43, 38, 33, 28]).scale_in == 34.0
    bari = default_instrument("BARITONE_B", [59, 54, 50, 45, 40, 35])
    assert bari.scale_in == 27.0 and str(bari.gauges[-1]) == ".062w"
    custom = default_instrument("CUSTOM", [59, 54, 50, 45, 40, 33])   # A1 baritone
    tensions = [custom.normal_tension(s) for s in range(6)]
    assert all(12 < t < 23 for t in tensions)            # a balanced set
    with pytest.raises(ValueError):
        default_instrument("STANDARD", STD_HIGH_TO_LOW, gauges_low_to_high=parse_gauges(".010"))
