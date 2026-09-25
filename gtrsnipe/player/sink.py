"""Visual sinks — where rendered frames are written, and where control keys come
from. The Transport talks only to a sink's ``write`` / ``read_key`` (plus
``setup``/``teardown`` lifecycle), so the interactive terminal handling is
swappable and testable.

* :class:`PlainSink` — writes to a stream (stdout, or a recorder in tests) with
  ANSI clear-between-frames; blocking key reads via the terminal for step mode.
  Non-blocking polling is a no-op here (live transport controls arrive with the
  curses sink in a later phase).
* ``CursesSink`` (later phase) will add the alternate screen, non-blocking poll,
  resize, and guaranteed restore.
"""
import sys
from typing import Callable, List, Optional

CLEAR = "\033[2J\033[H"  # clear screen + cursor home


def read_terminal_key() -> str:
    """Read a single keypress from a real terminal, else fall back to a line read.

    Raw single-char reads need a TTY; piped/redirected stdin (tests, `printf |`)
    falls back to line-buffered input.
    """
    try:
        import termios
        import tty
    except ImportError:  # non-POSIX
        termios = None

    if termios is None or not sys.stdin.isatty():
        return (sys.stdin.readline()[:1] or "\n").lower()

    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
    return ch.lower()


class Sink:
    """Visual output + control-input surface for the Transport."""
    width: Optional[int] = None  # renderer viewport width hint (None = unset)

    def setup(self) -> None: ...
    def write(self, text: str) -> None: ...
    def read_key(self, blocking: bool) -> Optional[str]: return None
    def teardown(self) -> None: ...


class PlainSink(Sink):
    """Writes to a stream; blocking key reads from the terminal (or a script)."""

    def __init__(self, *, writer: Optional[Callable[[str], object]] = None,
                 keys: Optional[List[str]] = None, clear: bool = True,
                 interactive: bool = False):
        self._writer = writer or sys.stdout.write
        self._scripted = list(keys) if keys is not None else None
        self._i = 0
        self.clear = clear
        self.interactive = interactive  # read real keys when not scripted

    def write(self, text: str) -> None:
        if self.clear:
            self._writer(CLEAR)
        self._writer(text + "\n")

    def read_key(self, blocking: bool) -> Optional[str]:
        if self._scripted is not None:            # tests / piped input
            if self._i < len(self._scripted):
                k = self._scripted[self._i]
                self._i += 1
                return k
            return None
        if not blocking:
            return None                            # no live polling in the plain sink
        if self.interactive:
            return read_terminal_key()
        return None
