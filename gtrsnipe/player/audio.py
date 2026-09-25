"""Audio sinks — make the player emit sound as it advances through frames.

An :class:`AudioSink` turns a stream of frames into note-on/note-off events. The
base class does the bookkeeping: :meth:`update` diffs the newly-sounding pitches
against the currently-ringing ones and emits only the changes, so held notes
ring across frames and only genuinely-new notes re-strike.

Backends (all optional, imported lazily so the core stays torch-free):

* :class:`NullSink` — no sound (the default).
* :class:`MidiOutSink` — stream MIDI to a port (a DAW/VST host, or a system
  synth). Needs ``mido`` (already a core dep) plus a backend (``python-rtmidi``,
  the ``[play]`` extra). This is the recommended "make noise" path.
* :class:`FluidSynthSink` — self-contained SoundFont synthesis, no external host.
  Needs ``pyfluidsynth`` + a ``.sf2`` file (the ``[synth]`` extra).
"""
from typing import Iterable, List, Optional

DEFAULT_VELOCITY = 96
_INSTALL_HINT = ("  Install the audio backend with:  pip install 'gtrsnipe[play]'"
                 "  (MIDI out)  or  pip install 'gtrsnipe[synth]'  (SoundFont)")

# General MIDI program names, program 0-127 (index == GM program number).
GM_INSTRUMENTS = [
    "Acoustic Grand Piano", "Bright Acoustic Piano", "Electric Grand Piano",
    "Honky-tonk Piano", "Electric Piano 1", "Electric Piano 2", "Harpsichord",
    "Clavi", "Celesta", "Glockenspiel", "Music Box", "Vibraphone", "Marimba",
    "Xylophone", "Tubular Bells", "Dulcimer", "Drawbar Organ", "Percussive Organ",
    "Rock Organ", "Church Organ", "Reed Organ", "Accordion", "Harmonica",
    "Tango Accordion", "Acoustic Guitar (nylon)", "Acoustic Guitar (steel)",
    "Electric Guitar (jazz)", "Electric Guitar (clean)", "Electric Guitar (muted)",
    "Overdriven Guitar", "Distortion Guitar", "Guitar Harmonics", "Acoustic Bass",
    "Electric Bass (finger)", "Electric Bass (pick)", "Fretless Bass",
    "Slap Bass 1", "Slap Bass 2", "Synth Bass 1", "Synth Bass 2", "Violin",
    "Viola", "Cello", "Contrabass", "Tremolo Strings", "Pizzicato Strings",
    "Orchestral Harp", "Timpani", "String Ensemble 1", "String Ensemble 2",
    "Synth Strings 1", "Synth Strings 2", "Choir Aahs", "Voice Oohs",
    "Synth Voice", "Orchestra Hit", "Trumpet", "Trombone", "Tuba", "Muted Trumpet",
    "French Horn", "Brass Section", "Synth Brass 1", "Synth Brass 2", "Soprano Sax",
    "Alto Sax", "Tenor Sax", "Baritone Sax", "Oboe", "English Horn", "Bassoon",
    "Clarinet", "Piccolo", "Flute", "Recorder", "Pan Flute", "Blown Bottle",
    "Shakuhachi", "Whistle", "Ocarina", "Lead 1 (square)", "Lead 2 (sawtooth)",
    "Lead 3 (calliope)", "Lead 4 (chiff)", "Lead 5 (charang)", "Lead 6 (voice)",
    "Lead 7 (fifths)", "Lead 8 (bass + lead)", "Pad 1 (new age)", "Pad 2 (warm)",
    "Pad 3 (polysynth)", "Pad 4 (choir)", "Pad 5 (bowed)", "Pad 6 (metallic)",
    "Pad 7 (halo)", "Pad 8 (sweep)", "FX 1 (rain)", "FX 2 (soundtrack)",
    "FX 3 (crystal)", "FX 4 (atmosphere)", "FX 5 (brightness)", "FX 6 (goblins)",
    "FX 7 (echoes)", "FX 8 (sci-fi)", "Sitar", "Banjo", "Shamisen", "Koto",
    "Kalimba", "Bagpipe", "Fiddle", "Shanai", "Tinkle Bell", "Agogo",
    "Steel Drums", "Woodblock", "Taiko Drum", "Melodic Tom", "Synth Drum",
    "Reverse Cymbal", "Guitar Fret Noise", "Breath Noise", "Seashore",
    "Bird Tweet", "Telephone Ring", "Helicopter", "Applause", "Gunshot",
]


def resolve_instrument(spec) -> int:
    """Resolve a GM program number from an int (0-127) or a name substring.

    Accepts ``"24"``, ``24``, ``"nylon"``, ``"Distortion Guitar"`` (case-
    insensitive substring; first match wins). Raises ValueError on no match.
    """
    if spec is None:
        return 0
    s = str(spec).strip()
    if s.lstrip("+-").isdigit():
        n = int(s)
        if not (0 <= n <= 127):
            raise ValueError(f"instrument number {n} out of range 0-127")
        return n
    low = s.lower()
    for i, name in enumerate(GM_INSTRUMENTS):
        if low in name.lower():
            return i
    raise ValueError(
        f"no GM instrument matches {spec!r}; try a number 0-127 or a name "
        "like 'nylon', 'distortion guitar', 'fretless bass'")


class AudioSink:
    """Base sink: diffs pitch sets into note-on/off; subclasses emit the events."""

    def __init__(self):
        self._active = set()

    def update(self, pitches: Iterable[int], velocity: int = DEFAULT_VELOCITY) -> None:
        """Sound exactly ``pitches``: release notes that stopped, strike new ones.

        Diff semantics — a pitch already ringing is left untouched (held). Use
        this when consecutive calls represent a continuously-evolving sonority.
        """
        new = set(pitches)
        for p in self._active - new:
            self._note_off(p)
        for p in new - self._active:
            self._note_on(p, velocity)
        self._active = new

    def attack(self, pitches: Iterable[int], velocity: int = DEFAULT_VELOCITY) -> None:
        """Re-articulate: release everything ringing, then strike ``pitches``.

        The player calls this once per frame. In the timeline model each frame is
        a fresh onset group, so a pitch repeated in the next frame is a genuine
        re-attack (e.g. four repeated quarter-notes) and must sound again — the
        diff in :meth:`update` would wrongly merge them into one held note.
        """
        new = set(pitches)
        for p in self._active:
            self._note_off(p)
        for p in new:
            self._note_on(p, velocity)
        self._active = new

    def all_off(self) -> None:
        """Release every ringing note but keep the backend open (pause/seek)."""
        for p in list(self._active):
            self._note_off(p)
        self._active.clear()

    def close(self) -> None:
        """Release every ringing note and tear down the backend."""
        self.all_off()
        self._teardown()

    # Subclass hooks -------------------------------------------------------
    def _note_on(self, pitch: int, velocity: int) -> None: ...
    def _note_off(self, pitch: int) -> None: ...
    def _teardown(self) -> None: ...


class NullSink(AudioSink):
    """No audio (default)."""


class MidiOutSink(AudioSink):
    """Stream MIDI note-on/off to an output port."""

    def __init__(self, port_name: Optional[str] = None, channel: int = 0,
                 program: int = 0):
        super().__init__()
        try:
            import mido
        except ImportError as e:  # pragma: no cover - mido is a core dep
            raise RuntimeError(f"MIDI output needs 'mido'.\n{_INSTALL_HINT}") from e
        self._mido = mido
        self.channel = channel
        self._port = self._open_port(port_name)
        if program:
            self._port.send(mido.Message(
                "program_change", program=int(program), channel=channel))

    def _open_port(self, port_name: Optional[str]):
        mido = self._mido
        try:
            if port_name:
                return mido.open_output(port_name)
            names = mido.get_output_names()
            if names:
                return mido.open_output(names[0])
            # No hardware/software port available: expose a virtual one a DAW
            # or system synth can connect to.
            return mido.open_output("gtrsnipe", virtual=True)
        except (OSError, IOError, ImportError) as e:
            available = ""
            try:
                available = ", ".join(self._mido.get_output_names())
            except Exception:
                pass
            raise RuntimeError(
                f"Could not open a MIDI output port ({e}).\n"
                f"  Available ports: [{available}]\n{_INSTALL_HINT}"
            ) from e

    def _note_on(self, pitch, velocity):
        self._port.send(self._mido.Message(
            "note_on", note=int(pitch), velocity=int(velocity), channel=self.channel))

    def _note_off(self, pitch):
        self._port.send(self._mido.Message(
            "note_off", note=int(pitch), velocity=0, channel=self.channel))

    def _teardown(self):
        if getattr(self, "_port", None) is not None:
            try:
                self._port.reset()
            finally:
                self._port.close()
                self._port = None


class FluidSynthSink(AudioSink):
    """Self-contained SoundFont synthesis via pyfluidsynth."""

    def __init__(self, soundfont: str, channel: int = 0, program: int = 0):
        super().__init__()
        if not soundfont:
            raise RuntimeError("FluidSynth needs a SoundFont: pass --soundfont PATH.")
        try:
            import fluidsynth
        except ImportError as e:
            import importlib.util
            if importlib.util.find_spec("fluidsynth") is not None:
                # The Python binding IS installed; it's the native C library
                # (libfluidsynth) that ctypes couldn't load.
                raise RuntimeError(
                    "pyfluidsynth is installed, but the native FluidSynth library "
                    "was not found. Install the C library (not the Python package):\n"
                    "  macOS (MacPorts): sudo port install fluidsynth\n"
                    "  macOS (Homebrew): brew install fluid-synth\n"
                    "  Debian/Ubuntu:    sudo apt install libfluidsynth3\n"
                    "  If installed but still not found (e.g. MacPorts in /opt/local),"
                    " set DYLD_FALLBACK_LIBRARY_PATH=/opt/local/lib\n"
                    f"  (underlying error: {e})") from e
            raise RuntimeError(
                f"SoundFont synthesis needs 'pyfluidsynth'.\n{_INSTALL_HINT}") from e
        self.channel = channel
        self._fs = fluidsynth.Synth()
        self._fs.start()
        try:
            sfid = self._fs.sfload(soundfont)
            if sfid == -1:
                raise RuntimeError(f"Could not load SoundFont: {soundfont}")
            self._fs.program_select(channel, sfid, 0, int(program))
        except Exception:
            # start() already allocated the native synth/driver; release it so a
            # failed construction doesn't leak it (no close() can run — we raise).
            self._fs.delete()
            self._fs = None
            raise

    def _note_on(self, pitch, velocity):
        self._fs.noteon(self.channel, int(pitch), int(velocity))

    def _note_off(self, pitch):
        self._fs.noteoff(self.channel, int(pitch))

    def _teardown(self):
        if getattr(self, "_fs", None) is not None:
            self._fs.delete()
            self._fs = None


def make_audio_sink(kind: str, *, midi_port: Optional[str] = None,
                    soundfont: Optional[str] = None,
                    instrument=None) -> AudioSink:
    """Factory used by the CLI: map an ``--audio`` choice to a sink instance."""
    if kind == "none":
        return NullSink()
    program = resolve_instrument(instrument)  # validates even for 'none'? only used below
    if kind == "midi":
        return MidiOutSink(port_name=midi_port, program=program)
    if kind == "fluidsynth":
        return FluidSynthSink(soundfont=soundfont, program=program)
    raise ValueError(f"unknown audio backend {kind!r}; "
                     "choose from none, midi, fluidsynth")
