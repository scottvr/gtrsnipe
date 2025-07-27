from ...core.types import Song, MusicalEvent, Track
import re
from typing import Optional

class AbcParser:
    @staticmethod
    def parse(abc_string: str) -> Song:
        """
        Parses an ABC notation string into a Song object.
        """
        song = Song()
        track = Track()

        header_pattern = re.compile(r"^[A-Z]:\s*(.*)$", re.MULTILINE)
        
        # ABC standard specifies default note length based on time signature.
        # If M < 0.75, L=1/16. If M >= 0.75, L=1/8.
        # We'll start with a common default (L:1/8 -> 0.5 beats) and adjust if needed.
        default_length_in_beats = 0.5
        
        # First, parse headers to establish the musical context (tempo, time signature, default note length)
        for match in header_pattern.finditer(abc_string):
            key = match.group(0)[0]
            value = match.group(1).strip()
            if key == 'Q':
                if '=' in value:
                    song.tempo = float(value.split('=')[-1])
                else:
                    song.tempo = float(value)
            elif key == 'M':
                song.time_signature = value
                # Adjust default note length based on time signature, per ABC spec
                try:
                    num, den = map(int, value.split('/'))
                    if (num / den) < 0.75:
                        default_length_in_beats = 0.25  # 1/16 note
                    else:
                        default_length_in_beats = 0.5   # 1/8 note
                except (ValueError, ZeroDivisionError):
                    # Keep the existing default if time signature is invalid
                    pass
            elif key == 'L':
                # If L: is explicitly provided, it overrides the default.
                # The L: value is a fraction of a whole note. Multiply by 4 to get beats (quarter notes).
                fraction_of_whole = AbcParser._abc_duration_to_beats(value)
                default_length_in_beats = fraction_of_whole * 4.0

        note_pattern = re.compile(r"([_^\=]?[A-Ga-g][,']*)([\d\/]*)")
        
        # Find the start of the music body (after the Key signature)
        key_field_match = re.search(r"K:.*", abc_string)
        body_start = key_field_match.end() if key_field_match else 0
        
        current_time = 0.0 # Keep track of time in beats

        for match in note_pattern.finditer(abc_string, body_start):
            note_str, duration_str = match.groups()
            
            pitch = AbcParser._abc_note_to_midi(note_str)
            
            # The duration string is a multiplier of the default note length.
            multiplier = AbcParser._abc_duration_to_beats(duration_str)
            duration_in_beats = multiplier * default_length_in_beats

            if pitch is not None:
                event = MusicalEvent(
                    pitch=pitch, 
                    duration=duration_in_beats,
                    time=current_time,
                    velocity=90 # ABC has no velocity, so use a default
                )
                track.events.append(event)
            
            # Advance the timeline by the duration of the current note
            current_time += duration_in_beats
            
        song.tracks.append(track)
        return song

    @staticmethod
    def _abc_note_to_midi(note_str: str) -> Optional[int]:
        """Converts an ABC note string (e.g., ^C, or g') to a MIDI pitch."""
        note_map = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
        
        accidental = 0
        if note_str.startswith(('^', '_', '=')):
            if note_str[0] == '^': accidental = 1
            if note_str[0] == '_': accidental = -1
            note_str = note_str[1:]
            
        base_char = note_str[0]
        base_pitch = note_map.get(base_char.upper())
        if base_pitch is None: return None

        # Set base octave: lowercase is one octave above uppercase
        octave_offset = 72 if base_char.islower() else 60

        # Adjust for octave markers
        apostrophes = note_str.count("'")
        commas = note_str.count(",")
        octave_adjust = (apostrophes - commas) * 12
        
        return base_pitch + octave_offset + accidental + octave_adjust

    @staticmethod
    def _abc_duration_to_beats(duration_str: str) -> float:
        """Converts an ABC duration string (e.g., 2, /2, 3/2) to a float multiplier."""
        if not duration_str:
            return 1.0 # A note with no duration string has a multiplier of 1.
        
        try:
            if '/' in duration_str:
                if duration_str.startswith('/'):
                    return 1 / float(duration_str[1:])
                num, den = duration_str.split('/')
                return float(num) / float(den)
            return float(duration_str)
        except (ValueError, ZeroDivisionError):
            return 1.0
