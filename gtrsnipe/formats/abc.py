from ..core.types import Song, MusicalEvent, Track
import re
from fractions import Fraction
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

        # Regex to find a note (with accidentals and octave) and its optional duration multiplier
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


class AbcGenerator:
    @staticmethod
    def _midi_pitch_to_abc(pitch: int) -> str:
        """Converts a MIDI pitch to an ABC note string."""
        note_names = ['C', '^C', 'D', '^D', 'E', 'F', '^F', 'G', '^G', 'A', '^A', 'B']
        octave = (pitch // 12) - 1
        note_in_octave = pitch % 12
        
        note_name = note_names[note_in_octave]
        
        if octave < 4:
            return note_name + ',' * (4 - octave)
        elif octave == 4:
            return note_name
        elif octave == 5:
            return note_name.lower()
        else:
            return note_name.lower() + "'" * (octave - 5)

    @staticmethod
    def _duration_to_abc(duration: float, default_length: float) -> str:
        """Converts a duration in beats to an ABC multiplier string."""
        multiplier = duration / default_length
        if multiplier == 1.0:
            return ""
        
        # Use Fraction to get a clean fractional representation (e.g., 1.5 -> 3/2)
        return str(Fraction(multiplier).limit_denominator())
        
    @staticmethod
    def _quantize_duration(duration_in_beats: float) -> float:
        """Quantizes a float duration to the nearest standard musical duration."""
        # Standard durations in beats (32nd, 16th, 8th, quarter, half, whole, and dotted versions)
        standard_durations = [
            0.125, 0.25, 0.375, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0
        ]
        
        # Find the standard duration that is closest to the actual duration
        closest_duration = min(standard_durations, key=lambda x: abs(x - duration_in_beats))
        return closest_duration

    @staticmethod
    def generate(song: Song, default_note_length: str = "1/16") -> str:
        """
        Converts a Song object into an ABC notation string, now with rest handling.
        
        Args:
            song: The Song object to convert.
            default_note_length: The default note length for the ABC 'L:' field (e.g., "1/8", "1/16").
        """
        abc_lines = []
        
        # This calculation is unchanged
        note_as_fraction_of_whole = AbcParser._abc_duration_to_beats(default_note_length)
        default_note_len_beats = note_as_fraction_of_whole * 4
        
        # Header generation is unchanged
        abc_lines.append("X:1")
        abc_lines.append("T:{song.title}")
        abc_lines.append(f"M:{song.time_signature}")
        abc_lines.append(f"L:{default_note_length}")
        abc_lines.append(f"Q:1/4={int(song.tempo)}")
        abc_lines.append("K:C")

        for track in song.tracks:
            sorted_events = sorted(track.events, key=lambda e: e.time)
            
            line = ""
            current_beat = 0.0 # Tracks the timeline position in beats

            for event in sorted_events:
                # --- NEW: Check for and insert rests ---
                # A rest is the time between the end of the last event and the start of this one.
                rest_duration = event.time - current_beat
                MIN_REST_BEATS = 0.1 # A threshold to ignore tiny, insignificant rests
                
                if rest_duration > MIN_REST_BEATS:
                    quantized_rest = AbcGenerator._quantize_duration(rest_duration)
                    if quantized_rest > 0:
                        rest_duration_str = AbcGenerator._duration_to_abc(quantized_rest, default_note_len_beats)
                        # 'z' is the standard ABC notation for a rest
                        line += f"z{rest_duration_str} "

                # --- Process the note event (existing logic) ---
                quantized_duration = AbcGenerator._quantize_duration(event.duration)
                if quantized_duration == 0:
                    # Update timeline even for zero-duration notes to avoid creating false rests
                    current_beat = max(current_beat, event.time + event.duration)
                    continue

                note_str = AbcGenerator._midi_pitch_to_abc(event.pitch)
                duration_str = AbcGenerator._duration_to_abc(quantized_duration, default_note_len_beats)
                
                line += f"{note_str}{duration_str} "
                
                # --- Update the timeline to the end of the current event ---
                current_beat = event.time + event.duration
            
            # Line wrapping logic is unchanged
            words = line.split()
            max_line_length = 70
            current_line = ""
            for word in words:
                if len(current_line) + len(word) + 1 > max_line_length:
                    abc_lines.append(current_line)
                    current_line = word
                else:
                    if current_line:
                        current_line += " "
                    current_line += word
            if current_line:
                abc_lines.append(current_line)

        return "\n".join(abc_lines)