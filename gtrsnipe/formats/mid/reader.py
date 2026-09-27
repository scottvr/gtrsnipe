import io
import logging
import os
import tempfile
from contextlib import redirect_stderr
from typing import Optional, Dict, List
import traceback
from typing import Union

import mido
from MIDI import MIDIFile, Events  

from ...core.types import Song, TimeSignature, Track, MusicalEvent

logger = logging.getLogger(__name__)

# Shortest note the reader keeps, in beats. It was 0.25 (a sixteenth), which
# stretched every shorter note -- including audio-transcription blips -- into a
# sixteenth; the old reason (tidy tab spacing) no longer applies, because the tab
# generator spaces notes by onset, not duration. This floor only keeps a
# zero-length note from vanishing.
MIN_NOTE_BEATS = 1.0 / 64

def _safe_decode(value: Optional[Union[str, bytes, float, bytearray, memoryview]]) -> Optional[str]:
    """Safely decodes a value to a string if it's bytes, otherwise returns it."""
    if isinstance(value, float):
        return None
    if isinstance(value, (bytes, bytearray, float, int, memoryview)):
        try:
            return bytes(value).decode('utf-8')
        except UnicodeDecodeError:
            return bytes(value).decode('latin-1', errors='ignore')
    return value
class MidiReader:
    """
    Parses a MIDI file into a format-agnostic Song object using a hybrid
    strategy to ensure maximum compatibility and robustness.
    """

    @staticmethod
    def _get_correct_beat_time(ticks: int, ticks_per_beat: int, 
                               midi_tempo_usec: int, song_tempo_bpm: float) -> float:
        """
        Converts a tick value to a musical beat time using the song's actual tempo.
        """
        # 1. Convert ticks to absolute seconds using the file's internal tempo
        time_in_seconds = mido.tick2second(ticks, ticks_per_beat, midi_tempo_usec)
        # 2. Convert seconds to musical beats using the song's *actual* tempo
        time_in_beats = time_in_seconds * (song_tempo_bpm / 60.0)
        return time_in_beats

    @staticmethod
    def _read_smf(midi_path: str) -> bytes:
        """The Standard MIDI File bytes in ``midi_path``: a plain SMF, the 'data'
        chunk of a RIFF 'RMID' container (.rmi, often saved as .mid), or an SMF
        after a short junk prefix (e.g. a MacBinary header). Anything else raises
        ValueError -- a non-MIDI file must not come back as an empty song."""
        with open(midi_path, "rb") as f:
            raw = f.read()
        if raw[:4] == b"MThd":
            return raw
        if raw[:4] == b"RIFF" and raw[8:12] == b"RMID":
            pos = 12
            while pos + 8 <= len(raw):
                chunk_id = raw[pos:pos + 4]
                size = int.from_bytes(raw[pos + 4:pos + 8], "little")
                if chunk_id == b"data":
                    data = raw[pos + 8:pos + 8 + size]
                    if data[:4] == b"MThd":
                        logger.info("--- RIFF/RMID container: reading its embedded MIDI data ---")
                        return data
                    break
                pos += 8 + size + (size & 1)          # RIFF chunks are word-aligned
            raise ValueError(f"{midi_path}: RIFF/RMID container without a MIDI 'data' chunk")
        k = raw.find(b"MThd", 0, 1024)
        if k > 0:
            logger.warning(f"Skipping {k} bytes of junk before the MIDI header in {midi_path}.")
            return raw[k:]
        raise ValueError(f"{midi_path} is not a MIDI file (it starts with {raw[:12]!r}).")

    @staticmethod
    def parse(midi_path: str, track_number_to_select: Optional[int]) -> Song:
        smf = MidiReader._read_smf(midi_path)        # ValueError for non-MIDI files
        try:
            logger.info("--- Attempting to parse with primary library (mido)... ---")
            return MidiReader._parse_with_mido(smf, track_number_to_select)
        except Exception as e:
            logger.warning(
                "The primary 'mido' parser failed. This can happen with rare or unusual MIDI files, "
                "or if a sanity check fails."
            )
            logger.warning(f"  └─ Details: {e}")
            
            # Attempt the fallback parser. It reads only paths, so an unwrapped
            # (RIFF / junk-prefixed) file goes to it via a temp copy of the SMF bytes.
            try:
                logger.info("--- Attempting to parse with fallback library (py-midi)... ---")
                if os.path.getsize(midi_path) == len(smf):
                    return MidiReader._parse_with_py_midi(midi_path, track_number_to_select)
                fd, tmp = tempfile.mkstemp(suffix=".mid")
                try:
                    with os.fdopen(fd, "wb") as f:
                        f.write(smf)
                    return MidiReader._parse_with_py_midi(tmp, track_number_to_select)
                finally:
                    os.remove(tmp)
            except Exception as e_fallback:
                logger.error("All MIDI parsers failed. The file may be corrupt or in an unsupported format.")
                traceback.print_exc()
                raise e_fallback 

    @staticmethod
    def _parse_with_py_midi(
        midi_path: str, track_number_to_select: Optional[int]
    ) -> Song:
        song = Song()
        time_sig_obj = TimeSignature()
        midi_file = MIDIFile(midi_path)
        midi_file.parse()

        if not midi_file.tracks:
            return song

        # Initial metadata scan from the first track
        for event in midi_file.tracks[0].events:
            if isinstance(event, Events.MetaEvent):
                if event.message == Events.meta.MetaEventKinds.Set_Tempo:
                    song.tempo = round(60_000_000 / int(event.attributes["tempo"]), 3)
                elif event.message == Events.meta.MetaEventKinds.Time_Signature:
                    num = event.attributes["numerator"]
                    den = event.attributes["denominator"]
                    song.time_signature = f"{num}/{den}"
                    time_sig_obj = TimeSignature(int(num), int(den))

        tracks_to_process = midi_file.tracks
        track_indices = range(len(midi_file.tracks))
        if track_number_to_select is not None:
            if not (1 <= track_number_to_select <= len(midi_file.tracks)):
                raise ValueError(
                    f"Invalid track number '{track_number_to_select}'. File has {len(midi_file.tracks)} tracks."
                )
            tracks_to_process = [midi_file.tracks[track_number_to_select - 1]]
            track_indices = [track_number_to_select - 1]

        ticks_per_beat = midi_file.division.ticks or 480
        if ticks_per_beat == 0:
            ticks_per_beat = 480

        for i, track_data in zip(track_indices, tracks_to_process):
            error_buffer = io.StringIO()
            with redirect_stderr(error_buffer):
                try:
                    track_data.parse()
                except Exception:
                    pass  # We check the stderr buffer to know if it really failed

            error_output = error_buffer.getvalue()
            if error_output:
                # FIX: Log the captured error directly for high visibility.
                logger.error(
                    f"The 'py-midi' library produced an error while parsing Track {i + 1}:\n"
                    f"--- Library Stderr ---\n"
                    f"{error_output.strip()}\n"
                    f"----------------------"
                )
                raise RuntimeError(f"Primary parser failed on Track {i + 1} due to stderr output.")
            
            # Process notes from the track if parsing succeeded
            track = Track()
            active_notes: Dict[int, List[Dict]] = {}
            last_event_time_ticks = 0
            temp_track_name = None
            temp_instrument_name = None

            for event in track_data.events:
                last_event_time_ticks = event.time
                if isinstance(event, Events.MetaEvent):
                    if event.message == Events.meta.MetaEventKinds.Track_Name:
                        temp_track_name = _safe_decode(event.attributes.get('text'))
                    elif event.message == Events.meta.MetaEventKinds.Instrument_Name:
                        temp_instrument_name = _safe_decode(event.attributes.get('text'))
                
                if isinstance(event, Events.MIDIEvent):
                    if len(event.data) >= 2:
                        command, note_pitch, velocity = (
                            event.command,
                            event.data[0],
                            event.data[1],
                        )
                        is_note_on = command == 0x90 and velocity > 0
                        is_note_off = command == 0x80 or (
                            command == 0x90 and velocity == 0
                        )

                        if is_note_on:
                            beat_time = event.time / ticks_per_beat
                            if note_pitch not in active_notes:
                                active_notes[note_pitch] = []
                            active_notes[note_pitch].append(
                                {"time": beat_time, "velocity": velocity}
                            )
                        elif is_note_off:
                            if note_pitch in active_notes and active_notes[note_pitch]:
                                beat_time = event.time / ticks_per_beat
                                start_event = active_notes[note_pitch].pop(0)
                                duration = beat_time - start_event["time"]
                                track.events.append(
                                    MusicalEvent(
                                        time=start_event["time"],
                                        pitch=note_pitch,
                                        velocity=start_event["velocity"],
                                        duration=duration,
                                    )
                                )

            # Handle any hanging notes
            track_end_time_beats = last_event_time_ticks / ticks_per_beat
            for pitch, hanging_notes in list(active_notes.items()):
                for start_event in hanging_notes:
                    duration = track_end_time_beats - start_event["time"]
                    track.events.append(
                        MusicalEvent(
                            time=start_event["time"],
                            pitch=pitch,
                            velocity=start_event["velocity"],
                            duration=max(MIN_NOTE_BEATS, duration),
                        )
                    )

            track.instrument_name = temp_track_name or temp_instrument_name or track.instrument_name

            if track.events:
                song.tracks.append(track)
        
        song.time_signature = str(time_sig_obj)

        # --- STAGE 2: Check for silent data corruption via timeline sanity check ---
        all_events = [event for track in song.tracks for event in track.events]
        num_notes = len(all_events)
        if num_notes > 0:
            last_event_time = max(event.time for event in all_events)
            num, den = map(int, song.time_signature.split("/"))
            beats_per_measure = (num / den) * 4
            num_measures = (
                int(last_event_time / beats_per_measure) + 1
                if beats_per_measure > 0
                else 0
            )
            if num_measures > num_notes * 3 and num_notes < (
                len(tracks_to_process) * 200
            ):  # Avoid false positives on very long, sparse songs
                raise RuntimeError(
                    f"Timeline Sanity Check Failed: Detected {num_measures} measures for only {num_notes} notes."
                )

        return song

    @staticmethod
    def _parse_with_mido(
        smf: bytes, track_number_to_select: Optional[int]
    ) -> Song:
        song = Song()
        try:
            midi_file = mido.MidiFile(file=io.BytesIO(smf))
        except Exception as e:
            try:   # common in the wild: data bytes > 127 (mido's strict mode rejects them)
                midi_file = mido.MidiFile(file=io.BytesIO(smf), clip=True)
                logger.warning(f"Clipped out-of-range MIDI data bytes to 0..127 ({e}).")
            except Exception:
                raise IOError(f"Mido could not open or parse the file: {e}") from e
        
        song.time_signature = "4/4"
        ticks_per_beat = midi_file.ticks_per_beat if midi_file.ticks_per_beat > 0 else 480
        midi_tempo_usec = 500000
    
        if midi_file.tracks:
            for event in midi_file.tracks[0]:
                if event.is_meta and event.type == "set_tempo":
                    song.tempo = mido.tempo2bpm(event.tempo)
                    midi_tempo_usec = event.tempo
                elif event.is_meta and event.type == "time_signature":
                    song.time_signature = f"{event.numerator}/{event.denominator}"
    
        tracks_to_process = midi_file.tracks
        if track_number_to_select is not None:
            if not (1 <= track_number_to_select <= len(midi_file.tracks)):
                raise ValueError(
                    f"Invalid track number '{track_number_to_select}'. File has {len(midi_file.tracks)} tracks."
                )
            tracks_to_process = [midi_file.tracks[track_number_to_select - 1]]
    
        for track_data in tracks_to_process:
            track = Track()
            active_notes: Dict[int, List[Dict]] = {}
            absolute_time_ticks = 0
            temp_track_name = None
            temp_instrument_name = None
            programs: Dict[int, int] = {}          # channel -> first program change
            first_channel: Optional[int] = None    # the channel of the first note
    
            for event in track_data:
                absolute_time_ticks += event.time
                if event.type == "program_change":
                    programs.setdefault(event.channel, event.program)
    
                if event.is_meta and event.type == "set_tempo":
                    song.tempo = mido.tempo2bpm(event.tempo)
                    midi_tempo_usec = event.tempo
                elif event.is_meta and event.type == "track_name":
                    temp_track_name = _safe_decode(event.name)
                elif event.is_meta and event.type == "instrument_name":
                    temp_instrument_name = _safe_decode(event.name)

                if event.type == "note_on" and event.velocity > 0:
                    if first_channel is None:
                        first_channel = event.channel
                    beat_time = MidiReader._get_correct_beat_time(
                        absolute_time_ticks, ticks_per_beat, midi_tempo_usec, song.tempo
                    )
                    if event.note not in active_notes:
                        active_notes[event.note] = []
                    active_notes[event.note].append({
                        "time": beat_time,
                        "velocity": event.velocity,
                    })
    
                elif event.type == "note_off" or (event.type == "note_on" and event.velocity == 0):
                    if event.note in active_notes and active_notes[event.note]:
                        beat_time = MidiReader._get_correct_beat_time(
                            absolute_time_ticks, ticks_per_beat, midi_tempo_usec, song.tempo
                        )
                        start_event = active_notes[event.note].pop(0)
                        duration = beat_time - start_event["time"]
                    
                        track.events.append(
                            MusicalEvent(
                                time=start_event["time"], 
                                pitch=event.note, 
                                duration=max(MIN_NOTE_BEATS, duration), 
                                velocity=start_event["velocity"]
                            )
                        )
            
            track_end_time_beats = MidiReader._get_correct_beat_time(
                absolute_time_ticks, ticks_per_beat, midi_tempo_usec, song.tempo
            )
            for pitch, hanging_notes_list in list(active_notes.items()):
                for start_event in hanging_notes_list:
                    duration = track_end_time_beats - start_event["time"]
                    track.events.append(
                        MusicalEvent(
                            time=start_event["time"],
                            pitch=pitch,
                            velocity=start_event["velocity"],
                            duration=max(MIN_NOTE_BEATS, duration),
                        )
                    )
    
            track.instrument_name = temp_track_name or temp_instrument_name or track.instrument_name
            track.channel = first_channel
            track.program = programs.get(first_channel) if first_channel is not None else None
            if track.events:
                song.tracks.append(track)
    
        return song