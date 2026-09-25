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


def map_curses_key(ch: int, curses_mod) -> Optional[str]:
    """Map a curses ``getch`` code to a Transport key token (pure/testable).

    ``-1`` (no key) -> None; arrows -> named tokens; resize -> ``"<resize>"``;
    printable ASCII -> its lowercased character.
    """
    if ch == -1:
        return None
    if ch == curses_mod.KEY_RESIZE:
        return "<resize>"
    named = {
        curses_mod.KEY_LEFT: "left", curses_mod.KEY_RIGHT: "right",
        curses_mod.KEY_UP: "up", curses_mod.KEY_DOWN: "down",
    }
    if ch in named:
        return named[ch]
    if 0 <= ch < 256:
        return chr(ch).lower()
    return None


class CursesSink(Sink):
    """Interactive TTY sink: alternate screen, non-blocking poll, resize, restore.

    Confined here and only instantiated in ``main()`` for a real terminal; tests
    use :class:`PlainSink`. Gets alt-screen scrollback preservation, cbreak (so
    Ctrl-C still raises for a clean quit), hidden cursor, and ``KEY_RESIZE``
    re-layout for free from stdlib ``curses``.
    """

    def __init__(self, clear: bool = True):
        self._scr = None
        self._curses = None
        self.width = None
        self._rows = None

    def setup(self) -> None:
        import curses
        self._curses = curses
        self._scr = curses.initscr()
        curses.noecho()
        curses.cbreak()
        self._scr.keypad(True)
        try:
            curses.curs_set(0)
        except curses.error:  # some terminals can't hide the cursor
            pass
        self._update_size()

    def _update_size(self) -> None:
        if self._scr is None:
            return
        rows, cols = self._scr.getmaxyx()
        self._rows = rows
        self.width = max(4, cols - 2)  # leave a margin; drives the tab viewport

    def write(self, text: str) -> None:
        scr = self._scr
        if scr is None:
            return
        scr.erase()
        rows, cols = scr.getmaxyx()
        for row, line in enumerate(text.split("\n")):
            if row >= rows:
                break
            try:
                scr.addnstr(row, 0, line, max(0, cols - 1))
            except self._curses.error:
                pass  # writing the last cell can raise; ignore
        scr.refresh()

    def read_key(self, blocking: bool) -> Optional[str]:
        scr = self._scr
        if scr is None:
            return None
        scr.nodelay(not blocking)
        scr.timeout(-1 if blocking else 0)
        return map_curses_key(scr.getch(), self._curses)

    def teardown(self) -> None:
        if self._scr is not None and self._curses is not None:
            try:
                self._curses.nocbreak()
                self._scr.keypad(False)
                self._curses.echo()
                self._curses.endwin()
            finally:
                self._scr = None
