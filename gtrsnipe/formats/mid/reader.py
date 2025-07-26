from MIDI import MIDIFile, Events
from ...core.types import Song, TimeSignature, Track, MusicalEvent
from typing import Optional, Dict, List

class MidiReader:
    """
    Parses a MIDI file into a format-agnostic Song object using the 'midifile' library.
    """
    @staticmethod
    def parse(midi_path: str, track_number_to_select: Optional[int]) -> Song:
        song = Song()
        time_sig_obj = TimeSignature()

        try:
            midi_file = MIDIFile(midi_path)
            midi_file.parse()
        except Exception as e:
            print(f"*** ERROR: Could not read MIDI file. The 'midiutil' library raised an error: {e} ***")
            exit(1)
        if not midi_file.tracks:
            print(f"*** WARNING: MIDI file has no tracks. Returning empty Song object. ***")
            return song 
        first_track = midi_file.tracks[0]
        first_track.parse()

        for event in first_track.events:
            if isinstance(event, Events.MetaEvent):
                if event.message == Events.meta.MetaEventKinds.Set_Tempo:
                    if 'tempo' in event.attributes:
                        song.tempo = round(60000000 / int(event.attributes['tempo']), 3)
                    else:
                        print(f"*** WARNING: Set_Tempo event is missing the 'tempo' key in its attributes. Tempo may be incorrect. ***")
                elif event.message == Events.meta.MetaEventKinds.Time_Signature:
                    if 'numerator' in event.attributes and 'denominator' in event.attributes:
                        num = event.attributes['numerator']
                        den = event.attributes['denominator']
                        song.time_signature = f"{num}/{den}"
                    else:
                        print(f"*** WARNING: Time_Signature event is missing keys in its attributes. Time signature may be incorrect. ***")

        tracks_to_process = midi_file.tracks
        
        if track_number_to_select is not None:
            # Validate the selected track number
            if not (1 <= track_number_to_select <= len(midi_file.tracks)):
                raise ValueError(f"Invalid track number '{track_number_to_select}'. File has {len(midi_file.tracks)} tracks. Please select a valid track.")
            
            print(f"--- Selecting track {track_number_to_select} of {len(midi_file.tracks)} ---")
            # Create a new list containing only the selected track (1-based to 0-based index)
            tracks_to_process = [midi_file.tracks[track_number_to_select - 1]]

        # Access the integer ticks-per-beat value from the .ticks attribute.
        ticks_per_beat = midi_file.division.ticks or 480
        if not ticks_per_beat or ticks_per_beat == 0:
            print(f"*** WARNING: MIDI file has a Ticks Per Beat value of zero. Defaulting to 480. ***")
            ticks_per_beat = 480


        for track_data in tracks_to_process:
            track_data.parse()
            track = Track()
            active_notes: Dict[int, List[Dict]] = {}
            # Keep track of the time of the last event in the track
            last_event_time_ticks = 0

            for event in track_data.events:
                last_event_time_ticks = event.time
                if isinstance(event, Events.MetaEvent):
                    if event.message == Events.meta.MetaEventKinds.Set_Tempo:
                        if 'tempo' in event.attributes:
                            song.tempo = 60000000 / int(event.attributes['tempo'])
                        else:
                            print(f"*** WARNING: Set_Tempo event is missing the 'tempo' key in its attributes. Tempo may be incorrect. ***")

                    elif event.message == Events.meta.MetaEventKinds.Time_Signature:
                        if 'numerator' in event.attributes and 'denominator' in event.attributes:
                            num = event.attributes['numerator']
                            den = event.attributes['denominator']
                            time_sig_obj = TimeSignature(int(num), int(den))
                            song.time_signature = str(time_sig_obj)
                        else:
                            print(f"*** WARNING: Time_Signature event is missing keys in its attributes. Time signature may be incorrect. ***")

                elif isinstance(event, Events.MIDIEvent):
                    if len(event.data) >= 2:
                        command, note_pitch, velocity = event.command, event.data[0], event.data[1]
                        is_note_on = (command == 0x90 and velocity > 0)
                        is_note_off = (command == 0x80 or (command == 0x90 and velocity == 0))

                        if is_note_on:
                            beat_time = event.time / ticks_per_beat
                            # Ensure a list exists for this pitch, then append the new note_on event
                            if note_pitch not in active_notes:
                                active_notes[note_pitch] = []
                            active_notes[note_pitch].append({'time': beat_time, 'velocity': velocity})

                        elif is_note_off:
                            # Check if there is an active note for this pitch to turn off
                            if note_pitch in active_notes and active_notes[note_pitch]:
                                beat_time = event.time / ticks_per_beat
                                # Pop the oldest note_on event for this pitch (FIFO)
                                start_event = active_notes[note_pitch].pop(0)
                                duration = beat_time - start_event['time']

                                track.events.append(MusicalEvent(
                                    time=start_event['time'],
                                    pitch=note_pitch,
                                    velocity=start_event['velocity'],
                                    duration=duration
                                ))
            track_end_time_beats = last_event_time_ticks / ticks_per_beat
            for pitch, hanging_notes in list(active_notes.items()):
                for start_event in hanging_notes:
                    duration = track_end_time_beats - start_event['time']
                    # Ensure a small, positive duration for notes at the very end
                    if duration <= 0:
                        duration = 0.25 # Default to a 16th note duration

                    track.events.append(MusicalEvent(
                        time=start_event['time'],
                        pitch=pitch,
                        velocity=start_event['velocity'],
                        duration=duration
                    ))

            if track.events:
                song.tracks.append(track)
        
        song.time_signature = f"{time_sig_obj.numerator}/{time_sig_obj.denominator}"
        return song
