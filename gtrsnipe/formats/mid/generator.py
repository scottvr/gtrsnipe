from midiutil import MIDIFile as MidiUtilFile
import math

from ...core.types import MusicalEvent, Song, Track, TimeSignature

class midiGenerator:
    """
    Generates a MIDIFile object from a format-agnostic Song object.
    """
    @staticmethod
    def generate(song: Song) -> MidiUtilFile:
        """
        Takes a Song object and converts it into a MIDIFile object suitable for writing to a file.
        """
        num_tracks = len(song.tracks) if song.tracks else 1
        # Use the aliased name for clarity
        midi_file = MidiUtilFile(num_tracks, removeDuplicates=False, deinterleave=False)

        # Set tempo and time signature on the first track at time 0
        track = 0
        time = 0
        midi_file.addTempo(track, time, song.tempo)
        
        try:
            num, den = map(int, song.time_signature.split('/'))
            # For time signature, denominator is expressed as a power of 2 (e.g., 4 becomes 2)
            den_power_of_2 = int(math.log2(den))
            midi_file.addTimeSignature(track, time, num, den_power_of_2, 24)
        except (ValueError, ZeroDivisionError):
            print(f"*** WARNING: Could not parse time signature '{song.time_signature}'. Defaulting to 4/4. ***")
            midi_file.addTimeSignature(track, time, 4, 2, 24)

        # Add notes for each track
        for i, track_data in enumerate(song.tracks):
            channel = 0
            for event in track_data.events:
                midi_file.addNote(
                    track=i,
                    channel=channel,
                    pitch=event.pitch,
                    time=event.time,       # Start time in beats
                    duration=event.duration, # Duration in beats
                    volume=event.velocity
                )
        
        return midi_file