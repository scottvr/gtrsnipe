class MidiToABC:
    def __init__(self, quantize_to: str = "1/16"):
        """
        Initialize converter with quantization settings

        Args:
            quantize_to: String representing the note duration to quantize to (e.g., "1/16" for sixteenth notes)
        """
        self.quantize_to = Fraction(quantize_to)
        self.ticks_per_beat = 480  # Standard MIDI resolution
        self.quantize_ticks = int(self.ticks_per_beat * 4 * self.quantize_to)

        # ABC notation constants
        self.KEY_SIGNATURES = {
            0: "C", 1: "G", 2: "D", 3: "A", 4: "E", 5: "B",
            6: "F#", -1: "F", -2: "Bb", -3: "Eb", -4: "Ab", -5: "Db", -6: "Gb"
        }

        self.MIDI_TO_ABC_NOTE = {}
        for octave in range(-1, 9):  # MIDI covers ~10 octaves
            base_offset = (octave + 1) * 12  # Each octave is 12 semitones
            # Lower octaves get more commas, higher octaves get more apostrophes
            octave_marker = ',' * abs(octave) if octave < 4 else "'" * (octave - 4)

            self.MIDI_TO_ABC_NOTE.update({
                base_offset + 0:  f"C{octave_marker}",
                base_offset + 1:  f"^C{octave_marker}",
                base_offset + 2:  f"D{octave_marker}",
                base_offset + 3:  f"^D{octave_marker}",
                base_offset + 4:  f"E{octave_marker}",
                base_offset + 5:  f"F{octave_marker}",
                base_offset + 6:  f"^F{octave_marker}",
                base_offset + 7:  f"G{octave_marker}",
                base_offset + 8:  f"^G{octave_marker}",
                base_offset + 9:  f"A{octave_marker}",
                base_offset + 10: f"^A{octave_marker}",
                base_offset + 11: f"B{octave_marker}"
            })


    def quantize_time(self, time_in_ticks: int) -> int:
        """Quantize time to nearest grid point"""
        return round(time_in_ticks / self.quantize_ticks) * self.quantize_ticks





        # Adjust octave
        if octave > 0:
            note = note.lower() + "'" * octave
        elif octave < 0:
            note = note.lower() + "," * abs(octave)
        else:
            note = note.lower()

        logging.info(f'note_to_abc: {note}')

        return note

    def duration_to_abc(self, duration_ticks: int) -> str:
        """Convert duration in ticks to ABC notation fraction"""
        duration = Fraction(duration_ticks, self.ticks_per_beat * 4)

        if duration == 1:
            return ""
        elif duration.denominator == 1:
            return str(duration.numerator)
        else:
            return f"{duration.numerator}/{duration.denominator}"

    def convert_file(self, midi_path: str, target_bpm: int = 90) -> str:
        """
        Convert MIDI file to ABC notation with quantization

        Args:
            midi_path: Path to MIDI file
            target_bpm: Target tempo in BPM

        Returns:
            ABC notation string
        """
        if isinstance(midi_path, str):
            midi = mido.MidiFile(midi_path)
        else:
            midi = midi_path


        # Initialize ABC header
        abc = [
            "X:1",
            "T:Converted from MIDI",
            f"M:4/4",  # Assuming 4/4 time signature
            f"L:{self.quantize_to}",  # Base note length
            f"Q:1/4={target_bpm}",
            "K:C",  # Default to C major
            ""
        ]

        # Track note events
        notes = []
        current_time = 0

        for track in midi.tracks:
            for msg in track:
                current_time += msg.time

                if msg.type == 'note_on' and msg.velocity > 0:
                    quantized_time = self.quantize_time(current_time)
                    notes.append((quantized_time, msg.note, 'on'))
                elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                    quantized_time = self.quantize_time(current_time)
                    notes.append((quantized_time, msg.note, 'off'))

        # Sort notes by time
        notes.sort()

        # Convert to ABC notation
        current_measure = []
        last_time = 0

        for time, note, event_type in notes:
            # Add rests if needed
            if time > last_time:
                rest_duration = self.duration_to_abc(time - last_time)
                if rest_duration:
                    current_measure.append(f"z{rest_duration}")

            if event_type == 'on':
                # Find corresponding note off event
                end_time = next(t for t, n, e in notes if n == note and e == 'off' and t > time)
#                end_time = next(t for t, n, e in notes if n == note and (e == 'off' or (e == 'on' and msg.velocity == 0)) and  t > time)
                duration = end_time - time
                abc_note = self.note_to_abc(note)
                abc_duration = self.duration_to_abc(duration)
                current_measure.append(f"{abc_note}{abc_duration}")

            last_time = time

        # Join measures into final ABC notation
        abc.append(" ".join(current_measure))

        return "\n".join(abc)

    def abc_to_midi(self, abc_string: str, output_path: str):
        """
        Convert ABC notation back to MIDI

        Args:
            abc_string: ABC notation string
            output_path: Path to save MIDI file
        """
        midi = MIDIFile(1)  # One track
        track = 0
        time = 0
        midi.addTempo(track, time, 90)

        # Parse ABC header
        header_pattern = r"([A-Z]):(.+)"
        headers = dict(re.findall(header_pattern, abc_string))

        # Parse notes
        note_pattern = r"([a-gA-G][\',]*(?:\d+(?:/\d+)?)?)|z(?:\d+(?:/\d+)?)?|\|"
        notes = re.findall(note_pattern, abc_string)

        for note in notes:
            if note == '|':
                continue

            # Parse duration
            duration_match = re.search(r'\d+(/\d+)?', note)
            if duration_match:
                duration = eval(duration_match.group())
            else:
                duration = 1

            # Parse pitch
            if note.startswith('z'):
                time += duration
                continue

            base_note = note[0].upper()
            octave_up = note.count("'")
            octave_down = note.count(",")

            # Convert to MIDI note number
            midi_note = {
                'C': 60, 'D': 62, 'E': 64, 'F': 65,
                'G': 67, 'A': 69, 'B': 71
            }[base_note]

            midi_note += octave_up * 12 - octave_down * 12

            # Add note to MIDI file
            midi.addNote(track, 0, midi_note, time, duration, 100)
            time += duration

        # Save MIDI file
        with open(output_path, 'wb') as output_file:
            midi.writeFile(output_file)
