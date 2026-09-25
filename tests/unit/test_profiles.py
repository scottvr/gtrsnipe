"""Tests for the .gtrsnipe profile/config system (arguments.apply_profiles).

A profile is prepended argv re-parsed by the same parser, so these use the real
converter parser and assert on the resulting namespace. --config-dir points at a
tmp dir (overriding the hermetic GTRSNIPE_HOME set by conftest)."""
import pytest

from gtrsnipe.arguments import apply_profiles, setup_parser


def parser():
    return setup_parser()


def write(dir_, name, text):
    (dir_ / name).write_text(text)
    return str(dir_)


# -- basic apply / precedence ----------------------------------------------

def test_profile_applies_options(tmp_path):
    d = write(tmp_path, "spanish",
              "sweet-spot-high = 9\nstring-switch-penalty = 0\nignore-open\nprefer-open\n")
    a = apply_profiles(parser(), ["--profile", "spanish", "--config-dir", d])
    assert a.sweet_spot_high == 9
    assert a.string_switch_penalty == 0
    assert a.ignore_open is True
    assert a.prefer_open is True


def test_cli_overrides_profile(tmp_path):
    d = write(tmp_path, "p", "sweet-spot-high = 9\n")
    a = apply_profiles(parser(), ["--profile", "p", "--config-dir", d,
                                  "--sweet-spot-high", "3"])
    assert a.sweet_spot_high == 3


def test_defaults_auto_loads(tmp_path):
    d = write(tmp_path, "defaults", "optimizer = greedy\n")
    a = apply_profiles(parser(), ["--config-dir", d])
    assert a.optimizer == "greedy"


def test_no_defaults_skips_defaults(tmp_path):
    d = write(tmp_path, "defaults", "optimizer = greedy\n")
    a = apply_profiles(parser(), ["--config-dir", d, "--no-defaults"])
    assert a.optimizer == "viterbi"  # the parser default


# -- ordering / multiple ----------------------------------------------------

def test_comma_list_applied_in_order_last_wins(tmp_path):
    write(tmp_path, "a", "capo = 2\n")
    d = write(tmp_path, "b", "capo = 5\n")
    a = apply_profiles(parser(), ["--profile", "a,b", "--config-dir", d])
    assert a.capo == 5  # b applied after a


def test_repeated_profile_flag(tmp_path):
    write(tmp_path, "a", "capo = 2\n")
    d = write(tmp_path, "b", "max-fret = 20\n")
    a = apply_profiles(parser(), ["--profile", "a", "--profile", "b", "--config-dir", d])
    assert a.capo == 2 and a.max_fret == 20


# -- format tolerance -------------------------------------------------------

def test_flag_truthy_and_falsy_values(tmp_path):
    d = write(tmp_path, "p", "ignore-open = true\nprefer-open = false\n")
    a = apply_profiles(parser(), ["--profile", "p", "--config-dir", d])
    assert a.ignore_open is True      # truthy -> flag on
    assert a.prefer_open is False     # falsy -> omitted (store_true stays default)


def test_comments_blanks_and_dashes_tolerated(tmp_path):
    d = write(tmp_path, "p", "# comment\n\n--capo = 4\nmax-fret 19\n")
    a = apply_profiles(parser(), ["--profile", "p", "--config-dir", d])
    assert a.capo == 4 and a.max_fret == 19  # leading --, and space-separated value


def test_unknown_option_warns_not_crashes(tmp_path, capsys):
    d = write(tmp_path, "p", "not-a-real-option = 5\ncapo = 3\n")
    a = apply_profiles(parser(), ["--profile", "p", "--config-dir", d])
    assert a.capo == 3
    assert "unknown option" in capsys.readouterr().err


def test_missing_profile_errors(tmp_path):
    with pytest.raises(SystemExit):
        apply_profiles(parser(), ["--profile", "nope", "--config-dir", str(tmp_path)])


# -- save-args round trip ---------------------------------------------------

def test_save_args_writes_non_defaults_and_reloads(tmp_path):
    d = str(tmp_path)
    apply_profiles(parser(), ["--config-dir", d, "--barre-bonus", "5", "--dedupe",
                              "--save-args", "mine"])
    text = (tmp_path / "mine").read_text()
    assert "barre-bonus = 5" in text and "dedupe" in text
    # per-run/meta args are not saved
    assert "config-dir" not in text and "save-args" not in text
    a = apply_profiles(parser(), ["--profile", "mine", "--config-dir", d])
    assert a.barre_bonus == 5.0 and a.dedupe is True


def test_profile_by_explicit_path(tmp_path):
    f = tmp_path / "custom.cfg"
    f.write_text("capo = 7\n")
    a = apply_profiles(parser(), ["--profile", str(f)])
    assert a.capo == 7
