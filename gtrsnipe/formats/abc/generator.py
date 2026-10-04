from ...core.keys import ESTIMATED, Key, accidental, note_name, song_key
from ...core.types import Song
from .parser import AbcParser
from fractions import Fraction
from itertools import groupby

_LETTER_PC = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
_ACCIDENTAL = {-2: "__", -1: "_", 0: "=", 1: "^", 2: "^^"}


class AbcGenerator:
    @staticmethod
    def _midi_pitch_to_abc(pitch: int, key: Key = Key("C"), signature=None, bar=None) -> str:
        """A MIDI pitch as an ABC note, spelled in ``key`` (F02).

        An accidental is written when the note differs from the key signature, and
        again (or a natural) when an earlier note on the same letter in this bar was
        written differently. ABC readers disagree on whether an accidental carries
        through the bar; written this way the tune reads the same under every rule.
        ``bar`` holds the bar's accidentals so far (letter -> accidental)."""
        signature = key.signature() if signature is None else signature
        bar = {} if bar is None else bar
        pos = key.position_of(pitch % 12)
        letter, acc = note_name(pos)[0], accidental(pos)
        # the octave belongs to the letter: Cb4 is the pitch B3, B#3 the pitch C4
        octave = (pitch - acc - _LETTER_PC[letter]) // 12 - 1
        mark = ""
        if acc != signature.get(letter, 0) or bar.get(letter, acc) != acc:
            mark = _ACCIDENTAL[acc]
            bar[letter] = acc

        if octave < 4:
            return mark + letter + ',' * (4 - octave)
        elif octave == 4:
            return mark + letter
        elif octave == 5:
            return mark + letter.lower()
        else:
            return mark + letter.lower() + "'" * (octave - 5)

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
        
        # ABC header field order matters: T: (title) must come after X: and
        # before K:, which terminates the header. Anything after K: is tune body.
        abc_lines.append("X:1")
        abc_lines.append(f"T:{song.title}")
        abc_lines.append(f"M:{song.time_signature}")
        abc_lines.append(f"L:{default_note_length}")
        abc_lines.append(f"Q:1/4={int(song.tempo)}")
        # The key: the song's own, else an estimate from the notes (and say so).
        key, how = song_key(song)
        key = key or Key("C")
        if how.startswith(ESTIMATED):
            abc_lines.append("% key estimated from the notes (set it with --key)")
        abc_lines.append(f"K:{key.abc}")
        signature = key.signature()

        try:
            num, den = map(int, song.time_signature.split('/'))
            beats_per_measure = num * (4.0 / den)
        except (ValueError, ZeroDivisionError):
            beats_per_measure = 4.0 # Default to 4/4 if parsing fails

        for track in song.tracks:
            if not track.events: continue
            
            # Instrument annotation as an ABC comment (a body T: would be invalid
            # after K:, and multiple tracks share one tune body here).
            if track.instrument_name and track.instrument_name != 'Acoustic Grand Piano':
                abc_lines.append(f"% {track.instrument_name}")

            sorted_events = sorted(track.events, key=lambda e: e.time)
            line = ""
            current_beat = 0.0
            beats_in_current_measure = 0.0 # Tracks beats to know when to place a bar line
            bar = {}                       # accidentals written so far in this bar

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
                            bar.clear()
                            beats_in_current_measure %= beats_per_measure


                # --- Note/Chord Handling ---
                longest_duration = max(n.duration for n in notes_in_group)
                quantized_duration = AbcGenerator._quantize_duration(longest_duration)
                duration_str = AbcGenerator._duration_to_abc(quantized_duration, default_note_len_beats)

                if len(notes_in_group) == 1:
                    note_str = AbcGenerator._midi_pitch_to_abc(notes_in_group[0].pitch, key, signature, bar)
                    line += f"{note_str}{duration_str} "
                else:
                    chord_notes_str = "".join([AbcGenerator._midi_pitch_to_abc(n.pitch, key, signature, bar)
                                               for n in notes_in_group])
                    line += f"[{chord_notes_str}]{duration_str} "
                
                beats_in_current_measure += quantized_duration
                current_beat = start_time + longest_duration

                if beats_in_current_measure >= beats_per_measure - 0.01: # Use a small tolerance
                    line += "| "
                    bar.clear()
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