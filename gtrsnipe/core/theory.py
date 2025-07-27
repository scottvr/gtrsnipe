import re

def note_name_to_pitch(name: str) -> int:
    """
    Converts a note name (e.g., "A4", "C#5", "Eb3") to its corresponding MIDI pitch number.
    """
    note_map = {
        'C': 0, 'B#': 0,
        'C#': 1, 'Db': 1,
        'D': 2,
        'D#': 3, 'Eb': 3,
        'E': 4, 'Fb': 4,
        'F': 5, 'E#': 5,
        'F#': 6, 'Gb': 6,
        'G': 7,
        'G#': 8, 'Ab': 8,
        'A': 9,
        'A#': 10, 'Bb': 10,
        'B': 11, 'Cb': 11,
    }
    
    match = re.match(r'([A-Ga-g])([#b]?)(\d+)', name)
    if not match:
        raise ValueError(f"Invalid note name format: {name}")

    note, accidental, octave = match.groups()
    note_name = note.upper() + accidental
    octave = int(octave)

    pitch_class = note_map[note_name]
    
    # MIDI pitch formula: pitch = pitch_class + (octave + 1) * 12
    return pitch_class + (octave + 1) * 12