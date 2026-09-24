from midiutil import MIDIFile as MidiUtilFile
import math
import logging
from ...core.types import Song

logger = logging.getLogger(__name__)
class MidiGenerator:
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
        if song.tempo_events:
            for event in song.tempo_events:
                # Add a tempo change at the time (in beats) specified by the event
                midi_file.addTempo(track=0, time=event.time, tempo=event.bpm)
        else:
            # Fall back to a single global tempo
            midi_file.addTempo(track=0, time=0, tempo=song.tempo)

        
        try:
            num, den = map(int, song.time_signature.split('/'))
            # MIDI expresses the denominator as a power of two (4 -> 2, 8 -> 3).
            # A non-power-of-2 denominator (e.g. 4/6) has no valid MIDI encoding;
            # int(math.log2(den)) would silently truncate it (6 -> 2 -> writes 4).
            if num <= 0 or den <= 0 or (den & (den - 1)) != 0:
                raise ValueError(f"time signature '{song.time_signature}' is not MIDI-representable")
            den_power_of_2 = den.bit_length() - 1
            midi_file.addTimeSignature(track, time, num, den_power_of_2, 24)
        except (ValueError, ZeroDivisionError) as e:
            logger.warning(f"*** WARNING: Could not use time signature '{song.time_signature}' ({e}). Defaulting to 4/4. ***")
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