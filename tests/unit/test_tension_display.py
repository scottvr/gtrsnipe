"""F04: --show-tuning shows each string's tension on your guitar; custom tunings that
overload a string warn; gauges for a re-entrant tuning are read as written."""
import sys

import pytest

from gtrsnipe.core.theory import note_name_to_pitch as n
from gtrsnipe.guitar.strings import (default_instrument, is_reentrant, parse_gauges,
                                     retune_report)

NASHVILLE = ["E3", "A3", "D4", "G4", "B3", "E4"]        # low string first


def test_reentrant_detection():
    assert is_reentrant([n(x) for x in NASHVILLE])
    assert not is_reentrant([n(x) for x in ("E2", "A2", "D3", "G3", "B3", "E4")])


def test_an_ascending_set_is_flipped_only_for_an_ordinary_tuning():
    assert [g.inches for g in parse_gauges("9 10 11 12 14 16")][0] == pytest.approx(0.016)
    as_written = parse_gauges("9 10 11 12 14 16", reentrant=True)
    assert [g.inches for g in as_written][0] == pytest.approx(0.009)     # low string first


def test_plain_and_wound_suffixes():
    g = parse_gauges("13 17 22 30 42 56")
    assert [x.wound for x in g] == [True, True, True, True, False, False]    # low first
    assert not parse_gauges("13 17 22p 30 42 56")[3].wound
    assert parse_gauges("10 13 18w 26 36 46")[3].wound


def test_retune_report_flags_a_raised_high_string_and_suggests_nothing_impossible():
    std = [n(x) for x in ("E4", "B3", "G3", "D3", "A2", "E2")]            # high -> low
    inst = default_instrument("STANDARD", std)
    target = [n("G4")] + std[1:]
    rows, warnings = retune_report(inst, target)
    assert len(warnings) == 1 and "string 1" in warnings[0] and "snap risk" in warnings[0]
    assert rows[1].split()[0] == "6"                                      # low string first
    ok_rows, ok_warnings = retune_report(inst, std)
    assert not ok_warnings


def run(monkeypatch, capsys, *argv):
    from gtrsnipe.converter import main
    monkeypatch.setattr(sys, "argv", ["gtrsnipe", *argv])
    with pytest.raises(SystemExit) as e:
        main()
    return e.value.code, capsys.readouterr().out


def test_show_tuning_by_name_and_custom(monkeypatch, capsys):
    code, out = run(monkeypatch, capsys, "--show-tuning", "DROP_C")
    assert code == 0 and "Notes:  C2 G2 C3 F3 A3 D4" in out and "strung for STANDARD" in out
    assert "Every string within safe tension." in out
    code, out = run(monkeypatch, capsys, "--tuning-pitches", "E2,A2,D3,G3,B3,G4", "--show-tuning")
    assert code == 0 and "Tuning: custom" in out and "1 of 6 strings outside safe tension" in out


def test_show_tuning_with_nashville_gauges_keeps_their_order(monkeypatch, capsys):
    code, out = run(monkeypatch, capsys, "--tuning-pitches", ",".join(NASHVILLE),
                    "--string-gauges", "10 14 8p 12 16 11", "--show-tuning")
    rows = {l.split()[0]: l.split() for l in out.splitlines()
            if l.strip()[:1].isdigit() and " lb " in l}                    # table rows only
    assert rows["6"][3] == ".010" and rows["1"][3] == ".011"             # as written, low first
    assert "8-16 set" in out


def test_show_tuning_unknown_name(monkeypatch, capsys):
    code, out = run(monkeypatch, capsys, "--show-tuning", "NOPE")
    assert code == 1 and "not found" in out


def test_solve_tuning_reports_pitches_past_steel(monkeypatch, capsys):
    code, out = run(monkeypatch, capsys, "--solve-tuning", "C4,C4,G4,G4,A4,A4,G4")
    assert "String physics" in out and "A4" in out and "past the breaking point" in out
