from ...core.types import Song
from .parser import AbcParser
from fractions import Fraction
from itertools import groupby

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
        if default_length == 0: return ""
        multiplier = duration / default_length
        if abs(multiplier - 1.0) < 0.01:
            return ""
        
        return str(Fraction(multiplier).limit_denominator())
        
    @staticmethod
    def _quantize_duration(duration_in_beats: float) -> float:
        """Quantizes a float duration to the nearest standard musical duration."""
        standard_durations = [
            0.125, 0.25, 0.375, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0
        ]
        
        if duration_in_beats <= 0: return 0.125
        
        closest_duration = min(standard_durations, key=lambda x: abs(x - duration_in_beats))
        return closest_duration

    @staticmethod
    def generate(song: Song, default_note_length: str = "1/16") -> str:
        """
        Converts a Song object into an ABC notation string, correctly handling chords, rests, and measure bars.
        """
        abc_lines = []
        
        note_as_fraction_of_whole = AbcParser._abc_duration_to_beats(default_note_length)
        default_note_len_beats = note_as_fraction_of_whole * 4.0
        
        abc_lines.append("X:1")
        abc_lines.append(f"M:{song.time_signature}")
        abc_lines.append(f"L:{default_note_length}")
        abc_lines.append(f"Q:1/4={int(song.tempo)}")
        abc_lines.append("K:C")

        try:
            num, den = map(int, song.time_signature.split('/'))
            beats_per_measure = num * (4.0 / den)
        except (ValueError, ZeroDivisionError):
            beats_per_measure = 4.0 # Default to 4/4 if parsing fails

        for track in song.tracks:
            if not track.events: continue
            
            abc_lines.append(f"T:{song.title} {'(track.instrument_name)' if track.instrument_name and track.instrument_name != 'Acoustic Grand Piano' else ''}")

            sorted_events = sorted(track.events, key=lambda e: e.time)
            line = ""
            current_beat = 0.0
            beats_in_current_measure = 0.0 # Tracks beats to know when to place a bar line

            time_groups = groupby(sorted_events, key=lambda e: e.time)

            for start_time, group_iter in time_groups:
                notes_in_group = list(group_iter)
                
                # --- Rest Handling ---
                rest_duration = start_time - current_beat
                if rest_duration > 0.1:
                    quantized_rest = AbcGenerator._quantize_duration(rest_duration)
                    if quantized_rest > 0:
                        rest_str = AbcGenerator._duration_to_abc(quantized_rest, default_note_len_beats)
                        line += f"z{rest_str} "
                        beats_in_current_measure += quantized_rest
                        # Check for bar line after adding a rest
                        if beats_in_current_measure >= beats_per_measure - 0.01:
                            line += "| "
                            beats_in_current_measure %= beats_per_measure


                # --- Note/Chord Handling ---
                longest_duration = max(n.duration for n in notes_in_group)
                quantized_duration = AbcGenerator._quantize_duration(longest_duration)
                duration_str = AbcGenerator._duration_to_abc(quantized_duration, default_note_len_beats)

                if len(notes_in_group) == 1:
                    note_str = AbcGenerator._midi_pitch_to_abc(notes_in_group[0].pitch)
                    line += f"{note_str}{duration_str} "
                else:
                    chord_notes_str = "".join([AbcGenerator._midi_pitch_to_abc(n.pitch) for n in notes_in_group])
                    line += f"[{chord_notes_str}]{duration_str} "
                
                beats_in_current_measure += quantized_duration
                current_beat = start_time + longest_duration

                if beats_in_current_measure >= beats_per_measure - 0.01: # Use a small tolerance
                    line += "| "
                    beats_in_current_measure %= beats_per_measure # Use modulo to carry over remainder

            # Line wrapping
            words = line.split()
            max_line_length = 70
            current_line = ""
            for word in words:
                if len(current_line) + len(word) + 1 > max_line_length:
                    abc_lines.append(current_line)
                    current_line = word
                else:
                    if current_line: current_line += " "
                    current_line += word
            if current_line:
                abc_lines.append(current_line)

        return "\n".join(abc_lines)