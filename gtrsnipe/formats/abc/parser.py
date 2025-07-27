from ...core.types import Song, MusicalEvent, Track
import re
from typing import Optional

class AbcParser:
    @staticmethod
    def parse(abc_string: str) -> Song:
        """
        Parses an ABC notation string into a Song object, correctly handling chords.
        """
        song = Song()
        track = Track()

        header_pattern = re.compile(r"^[A-Z]:\s*(.*)$", re.MULTILINE)
        
        default_length_in_beats = 0.5
        
        for match in header_pattern.finditer(abc_string):
            key = match.group(0)[0]
            value = match.group(1).strip()
            if key == 'Q':
                if '=' in value: song.tempo = float(value.split('=')[-1])
                else: song.tempo = float(value)
            elif key == 'M':
                song.time_signature = value
                try:
                    num, den = map(int, value.split('/'))
                    if (num / den) < 0.75: default_length_in_beats = 0.25
                    else: default_length_in_beats = 0.5
                except (ValueError, ZeroDivisionError): pass
            elif key == 'L':
                fraction_of_whole = AbcParser._abc_duration_to_beats(value)
                default_length_in_beats = fraction_of_whole * 4.0

        # identify chords "[...]", single notes, or rests "z" as tokens ---
        token_pattern = re.compile(r"(\[[A-Ga-g,^=_']*\]|[_^\=]?[A-Ga-g][,']*|z)([\d\/]*)")
        
        key_field_match = re.search(r"K:.*", abc_string)
        body_start = key_field_match.end() if key_field_match else 0
        
        current_time = 0.0

        for match in token_pattern.finditer(abc_string, body_start):
            token, duration_str = match.groups()
            
            # Calculate the duration for the entire token (note, chord, or rest)
            multiplier = AbcParser._abc_duration_to_beats(duration_str)
            duration_in_beats = multiplier * default_length_in_beats

            # --- FIX: Handle chords and single notes differently ---
            if token.startswith('['):
                # It's a chord: create multiple events at the same start time
                note_strings = re.findall(r"[_^\=]?[A-Ga-g][,']*", token)
                for note_str in note_strings:
                    pitch = AbcParser._abc_note_to_midi(note_str)
                    if pitch is not None:
                        event = MusicalEvent(
                            pitch=pitch, 
                            duration=duration_in_beats,
                            time=current_time,
                            velocity=90
                        )
                        track.events.append(event)
            elif token != 'z':
                # It's a single note
                pitch = AbcParser._abc_note_to_midi(token)
                if pitch is not None:
                    event = MusicalEvent(
                        pitch=pitch, 
                        duration=duration_in_beats,
                        time=current_time,
                        velocity=90
                    )
                    track.events.append(event)
            
            # Advance the timeline by the duration of the token
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

        octave_offset = 72 if base_char.islower() else 60

        apostrophes = note_str.count("'")
        commas = note_str.count(",")
        octave_adjust = (apostrophes - commas) * 12
        
        return base_pitch + octave_offset + accidental + octave_adjust

    @staticmethod
    def _abc_duration_to_beats(duration_str: str) -> float:
        """Converts an ABC duration string (e.g., 2, /2, 3/2) to a float multiplier."""
        if not duration_str:
            return 1.0
        
        try:
            if '/' in duration_str:
                if duration_str.startswith('/'):
                    return 1 / float(duration_str[1:])
                num, den = duration_str.split('/')
                return float(num) / float(den)
            return float(duration_str)
        except (ValueError, ZeroDivisionError):
            return 1.0