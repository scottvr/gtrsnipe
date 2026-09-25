"""Tests for the visual sink (PlainSink + terminal key fallback)."""
import io

from gtrsnipe.player.sink import PlainSink, read_terminal_key


def test_plain_sink_writes_with_clear():
    writes = []
    s = PlainSink(writer=writes.append, keys=[], clear=True)
    s.write("board")
    assert any("\033[2J" in w for w in writes)
    assert any("board" in w for w in writes)


def test_plain_sink_no_clear():
    writes = []
    s = PlainSink(writer=writes.append, keys=[], clear=False)
    s.write("board")
    assert writes == ["board\n"]


def test_plain_sink_scripted_keys_then_none():
    s = PlainSink(writer=lambda x: None, keys=["a", "q"])
    assert s.read_key(True) == "a"
    assert s.read_key(True) == "q"
    assert s.read_key(True) is None      # exhausted
    assert s.read_key(False) is None


def test_plain_sink_nonblocking_is_none_without_script():
    # No scripted keys, not interactive -> non-blocking poll yields nothing.
    s = PlainSink(writer=lambda x: None, interactive=False)
    assert s.read_key(False) is None


def test_read_terminal_key_falls_back_when_not_a_tty(monkeypatch):
    # Regression: piped/redirected stdin raises termios.error, not ImportError,
    # so the raw-mode path must be gated on isatty().
    import gtrsnipe.player.sink as sink_mod
    fake = io.StringIO("q\n")
    fake.isatty = lambda: False
    monkeypatch.setattr(sink_mod.sys, "stdin", fake)
    assert read_terminal_key() == "q"
