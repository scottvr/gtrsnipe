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


class AudioSink:
    """Base sink: diffs pitch sets into note-on/off; subclasses emit the events."""

    def __init__(self):
        self._active = set()

    def update(self, pitches: Iterable[int], velocity: int = DEFAULT_VELOCITY) -> None:
        """Sound exactly ``pitches``: release notes that stopped, strike new ones."""
        new = set(pitches)
        for p in self._active - new:
            self._note_off(p)
        for p in new - self._active:
            self._note_on(p, velocity)
        self._active = new

    def close(self) -> None:
        """Release every ringing note and tear down the backend."""
        for p in list(self._active):
            self._note_off(p)
        self._active.clear()
        self._teardown()

    # Subclass hooks -------------------------------------------------------
    def _note_on(self, pitch: int, velocity: int) -> None: ...
    def _note_off(self, pitch: int) -> None: ...
    def _teardown(self) -> None: ...


class NullSink(AudioSink):
    """No audio (default)."""


class MidiOutSink(AudioSink):
    """Stream MIDI note-on/off to an output port."""

    def __init__(self, port_name: Optional[str] = None, channel: int = 0):
        super().__init__()
        try:
            import mido
        except ImportError as e:  # pragma: no cover - mido is a core dep
            raise RuntimeError(f"MIDI output needs 'mido'.\n{_INSTALL_HINT}") from e
        self._mido = mido
        self.channel = channel
        self._port = self._open_port(port_name)

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

    def __init__(self, soundfont: str, channel: int = 0):
        super().__init__()
        if not soundfont:
            raise RuntimeError("FluidSynth needs a SoundFont: pass --soundfont PATH.")
        try:
            import fluidsynth
        except ImportError as e:
            raise RuntimeError(
                f"SoundFont synthesis needs 'pyfluidsynth'.\n{_INSTALL_HINT}") from e
        self.channel = channel
        self._fs = fluidsynth.Synth()
        self._fs.start()
        sfid = self._fs.sfload(soundfont)
        if sfid == -1:
            raise RuntimeError(f"Could not load SoundFont: {soundfont}")
        self._fs.program_select(channel, sfid, 0, 0)

    def _note_on(self, pitch, velocity):
        self._fs.noteon(self.channel, int(pitch), int(velocity))

    def _note_off(self, pitch):
        self._fs.noteoff(self.channel, int(pitch))

    def _teardown(self):
        if getattr(self, "_fs", None) is not None:
            self._fs.delete()
            self._fs = None


def make_audio_sink(kind: str, *, midi_port: Optional[str] = None,
                    soundfont: Optional[str] = None) -> AudioSink:
    """Factory used by the CLI: map an ``--audio`` choice to a sink instance."""
    if kind == "none":
        return NullSink()
    if kind == "midi":
        return MidiOutSink(port_name=midi_port)
    if kind == "fluidsynth":
        return FluidSynthSink(soundfont=soundfont)
    raise ValueError(f"unknown audio backend {kind!r}; "
                     "choose from none, midi, fluidsynth")
