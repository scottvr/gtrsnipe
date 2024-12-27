from ..core.types import TimeSignature, MusicalEvent
from ..utils.guitar_mapper import GuitarPositionMapper
from typing import Tuple, List
import mido

class MidiToTabConverter:
    def __init__(self, default_tempo: float = 120.0, default_time_sig: TimeSignature = TimeSignature()):
        self.default_tempo = default_tempo
        self.default_time_sig = default_time_sig

    def convert(self, midi_path: str) -> Tuple[List[MusicalEvent], float, TimeSignature]:
        midi_file = mido.MidiFile(midi_path)
        events = []
        cumulative_time = {track_idx: 0 for track_idx in range(len(midi_file.tracks))}
        tempo = self.default_tempo
        time_sig = self.default_time_sig
        
        print("MIDI Note Sequence:")
        for track_idx, track in enumerate(midi_file.tracks):
            for msg in track:
                cumulative_time[track_idx] += msg.time
                
                if msg.type == 'set_tempo':
                    tempo = mido.tempo2bpm(msg.tempo)
                elif msg.type == 'time_signature':
                    time_sig = TimeSignature(msg.numerator, msg.denominator)
                elif msg.type == 'note_on' and msg.velocity > 0:
                    beat_time = cumulative_time[track_idx] / midi_file.ticks_per_beat
                    print(f"Note On: {msg.note} at beat {beat_time}")
                    events.append(MusicalEvent(
                        time=beat_time,
                        pitch=msg.note,
                        velocity=msg.velocity,
                        duration=0
                    ))
                elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                    beat_time = cumulative_time[track_idx] / midi_file.ticks_per_beat
                    for event in reversed(events):
                        if event.pitch == msg.note and event.duration == 0:
                            event.duration = beat_time - event.time
                            break
        
        return sorted(events, key=lambda e: e.time), tempo, time_sig