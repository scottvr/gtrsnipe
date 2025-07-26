from fractions import Fraction
from itertools import groupby
from ..core.types import Song, MusicalEvent, Track
from ..guitar.mapper import GuitarMapper
import re

class VextabGenerator:
    @staticmethod
    def generate(song: Song, default_note_length: str = "1/16", no_articulataions=False) -> str:
        """
        Converts a Song object into a complete Vextab notation string.
        """
        # --- Dynamically set measures per line based on visual density ---
        try:
            denominator = int(default_note_length.split('/')[1])
        except (ValueError, IndexError):
            denominator = 16

        measures_per_line = 4
        if denominator >= 16:
            measures_per_line = 2
        elif denominator >= 8:
            measures_per_line = 3

        output_parts = [f"//Title: {song.title}, options tempo={int(song.tempo)}"]
        
        mapper = GuitarMapper()
        all_mapped_events = []
        for track in song.tracks:
            if not track.events: continue
            mapped_events = mapper.map_events_to_fretboard(track.events, no_articulataions=no_articulataions)
            all_mapped_events.extend(mapped_events)

        sorted_events = sorted(all_mapped_events, key=lambda e: e.time)
        if not sorted_events: return "\n".join(output_parts)

        # Group notes by time, with chord playability check ---
        QUANTIZATION_RESOLUTION = 0.125
        def quantize_time(beat): return round(beat / QUANTIZATION_RESOLUTION) * QUANTIZATION_RESOLUTION
        
        time_events = []
        MAX_CHORD_FRET_SPAN = 3
        for time, notes_in_group_iter in groupby(sorted_events, key=lambda e: quantize_time(e.time)):
            notes = list(notes_in_group_iter)
            if len(notes) > 1:
                frets = [n.fret for n in notes if n.fret is not None]
                if frets and (max(frets) - min(frets)) > MAX_CHORD_FRET_SPAN:
                    for note in notes:
                        time_events.append({'time': time, 'notes': [note], 'technique': note.technique})
                    continue
            time_events.append({'time': time, 'notes': notes, 'technique': notes[0].technique})

        # Group "time events" into legato phrases ---
        phrases = []
        current_phrase = []
        for te in time_events:
            is_new_phrase = (not current_phrase or 
                             te['technique'] == 'pick' or 
                             te['notes'][0].string != current_phrase[-1]['notes'][0].string)
            if is_new_phrase:
                if current_phrase: phrases.append(current_phrase)
                current_phrase = [te]
            else:
                current_phrase.append(te)
        if current_phrase: phrases.append(current_phrase)
        
        try:
            num, den = map(int, song.time_signature.split('/'))
            beats_per_measure = num * (4 / den)
        except (ValueError, ZeroDivisionError): beats_per_measure = 4

        phrases_by_line = groupby(phrases, key=lambda p: int(p[0]['time'] / beats_per_measure) // measures_per_line)

        for line_number, line_phrases_iter in phrases_by_line:
            notes_for_current_line = []
            for phrase in line_phrases_iter:
                # Each 'phrase' is a list of 'time_event' dictionaries.
                first_time_event = phrase[0]
                duration_str = VextabGenerator._duration_to_vextab(first_time_event['notes'][0].duration)
                
                # Format the first note/chord in the phrase
                first_notes = first_time_event['notes']
                if len(first_notes) == 1:
                    phrase_parts = [f"{first_notes[0].fret}/{first_notes[0].string + 1}"]
                else:
                    chord_parts = [f"{n.fret}/{n.string + 1}" for n in first_notes]
                    phrase_parts = [f"({'.'.join(chord_parts)})"]
                
                # Append subsequent legato notes in the phrase
                for i in range(1, len(phrase)):
                    note = phrase[i]['notes'][0] # Legato is to a single note
                    technique_char = 'h' if note.technique == 'hammer-on' else 'p'
                    phrase_parts.append(f"{technique_char}{note.fret}/{note.string + 1}")
                
                notes_for_current_line.append(f"{duration_str} {''.join(phrase_parts)}")

            if notes_for_current_line:
                tabstave_header = f"\ntabstave notation=true time={song.time_signature}" if line_number > 0 else f"tabstave notation=true time={song.time_signature}"
                output_parts.append(tabstave_header)
                output_parts.append(f"notes {' '.join(notes_for_current_line)}")

        return "\n".join(output_parts)
    
    @staticmethod
    def _duration_to_vextab(duration_in_beats: float) -> str:
        if duration_in_beats >= 4.0: return ":w"; 
        if duration_in_beats >= 3.0: return ":hd"; 
        if duration_in_beats >= 2.0: return ":h"; 
        if duration_in_beats >= 1.5: return ":qd"; 
        if duration_in_beats >= 1.0: return ":q"; 
        if duration_in_beats >= 0.75: return ":8d"; 
        if duration_in_beats >= 0.5: return ":8"; 
        if duration_in_beats >= 0.25: return ":16"; 
        if duration_in_beats >= 0.125: return ":32"; 
        return ":q"


class VextabParser:
    """Parses a VexTab notation string into a Song object."""

    @staticmethod
    def _vextab_duration_to_beats(s: str) -> float:
        """Converts a VexTab duration token (e.g., :q, :8) to beats."""
        d_map = {
            ":w": 4.0, ":hd": 3.0, ":h": 2.0, ":qd": 1.5, ":q": 1.0,
            ":8d": 0.75, ":8": 0.5, ":16": 0.25, ":32": 0.125
        }
        return d_map.get(s, 1.0)

    @staticmethod
    def _vextab_pos_to_midi(string_num: int, fret: int) -> int:
        """Converts a VexTab 1-based string and fret to a MIDI pitch."""
        open_string_pitches = [64, 59, 55, 50, 45, 40]
        return open_string_pitches[string_num - 1] + fret

    @staticmethod
    def parse(vex_string: str) -> Song:
        song = Song()
        track = Track()

        # 1. Header Parsing
        tempo_match = re.search(r"tempo=(\d+)", vex_string)
        if tempo_match:
            song.tempo = float(tempo_match.group(1))
        time_sig_match = re.search(r"time=(\d+/\d+)", vex_string)
        if time_sig_match:
            song.time_signature = time_sig_match.group(1)

        # 2. Token Processing
        all_notes_str = " ".join(re.findall(r"notes\s+(.*)", vex_string))
        tokens = all_notes_str.split()
        
        # 3. Rhythmic Parsing
        current_time_beats = 0.0
        current_duration_beats = 1.0  # VexTab default is a quarter note

        for token in tokens:
            if token.startswith(':'):
                current_duration_beats = VextabParser._vextab_duration_to_beats(token)
                continue

            note_atoms = re.findall(r'\d+/\d+', token)
            if not note_atoms: continue
            
            # --- DURATION FIX ---
            # The current duration applies to EACH note event within the token, not subdivided.
            duration_per_event = current_duration_beats

            # --- TECHNIQUE FIX ---
            # Process the first note and its optional PREFIX technique
            fret, string_num = map(int, note_atoms[0].split('/'))
            pitch = VextabParser._vextab_pos_to_midi(string_num, fret)
            prefix_technique = 'hammer-on' if token.startswith('h') else 'pull-off' if token.startswith('p') else None
            track.events.append(MusicalEvent(time=current_time_beats, pitch=pitch, duration=duration_per_event, velocity=90, technique=prefix_technique))
            current_time_beats += duration_per_event

            # Process subsequent notes and their CONNECTING techniques
            connecting_parts = re.split(r'\d+/\d+', token)[1:-1]

            for i in range(1, len(note_atoms)):
                fret, string_num = map(int, note_atoms[i].split('/'))
                pitch = VextabParser._vextab_pos_to_midi(string_num, fret)
                
                tech_char = None
                if (i-1) < len(connecting_parts):
                    tech_part = connecting_parts[i-1]
                    if 'h' in tech_part: tech_char = 'h'
                    elif 'p' in tech_part: tech_char = 'p'
                
                legato_technique = 'hammer-on' if tech_char == 'h' else 'pull-off' if tech_char == 'p' else None
                track.events.append(MusicalEvent(time=current_time_beats, pitch=pitch, duration=duration_per_event, velocity=90, technique=legato_technique))
                current_time_beats += duration_per_event
        
        song.tracks.append(track)
        return song
    

### this is the accidentally beautiful one that takes legato runs of hammer-ons and pull-offs and squeezes them to fit in a single note duration. Sounds aweesome.
# 
## class VextabParser:
##     """Parses a VexTab notation string into a Song object."""
## 
##     @staticmethod
##     def _vextab_duration_to_beats(s: str) -> float:
##         """Converts a VexTab duration token (e.g., :q, :8) to beats."""
##         d_map = {
##             ":w": 4.0, ":hd": 3.0, ":h": 2.0, ":qd": 1.5, ":q": 1.0,
##             ":8d": 0.75, ":8": 0.5, ":16": 0.25, ":32": 0.125
##         }
##         return d_map.get(s, 1.0)
## 
##     @staticmethod
##     def _vextab_pos_to_midi(string_num: int, fret: int) -> int:
##         """Converts a VexTab 1-based string and fret to a MIDI pitch."""
##         open_string_pitches = [64, 59, 55, 50, 45, 40]
##         return open_string_pitches[string_num - 1] + fret
## 
##     @staticmethod
##     def parse(vex_string: str) -> Song:
##         song = Song()
##         track = Track()
## 
##         # --- Section 1: Header Parsing (Unchanged) ---
##         tempo_match = re.search(r"tempo=(\d+)", vex_string)
##         if tempo_match:
##             song.tempo = float(tempo_match.group(1))
##         
##         time_sig_match = re.search(r"time=(\d+/\d+)", vex_string)
##         if time_sig_match:
##             song.time_signature = time_sig_match.group(1)
## 
##         # --- Section 2: Token Processing (Unchanged) ---
##         all_notes_str = " ".join(re.findall(r"notes\s+(.*)", vex_string))
##         tokens = all_notes_str.split()
##         
##         processed_tokens = []
##         for token in tokens:
##             tech_char = 'p' if 'p' in token else 'h' if 'h' in token else None
##             if tech_char and token.count('/') == 2:
##                 parts = token.split(tech_char)
##                 processed_tokens.append(parts[0])
##                 processed_tokens.append(tech_char + parts[1])
##             else:
##                 processed_tokens.append(token)
## 
##         # --- Section 3: Rhythmic Parsing (NEW LOGIC) ---
##         current_time_beats = 0.0
##         # VexTab's default duration is a quarter note if not specified
##         current_duration_beats = 1.0 
## 
##         for token in processed_tokens:
##             # First, check if the token is a duration specifier
##             if token.startswith(':'):
##                 current_duration_beats = VextabParser._vextab_duration_to_beats(token)
##                 continue
## 
##             # If it's not a duration, it's a note/chord/run that uses the current duration
##             note_atoms = re.findall(r'\d+/\d+', token)
##             if not note_atoms: continue
##             
##             techniques = re.findall(r'[ph]', token)
##             num_events_in_token = len(note_atoms)
##             duration_per_event = current_duration_beats / num_events_in_token
## 
##             # Process the first note atom in the token
##             fret, string_num = map(int, note_atoms[0].split('/'))
##             pitch = VextabParser._vextab_pos_to_midi(string_num, fret)
##             # A note is a pull-off/hammer-on only if it's prefixed
##             technique = 'hammer-on' if token.startswith('h') else 'pull-off' if token.startswith('p') else None
##             track.events.append(MusicalEvent(time=current_time_beats, pitch=pitch, duration=duration_per_event, velocity=90, technique=technique))
##             current_time_beats += duration_per_event
## 
##             # Process subsequent notes in the same compound token
##             for i in range(1, len(note_atoms)):
##                 fret, string_num = map(int, note_atoms[i].split('/'))
##                 pitch = VextabParser._vextab_pos_to_midi(string_num, fret)
##                 tech_char = techniques[i-1] if (i-1) < len(techniques) else None
##                 legato_technique = 'hammer-on' if tech_char == 'h' else 'pull-off' if tech_char == 'p' else None
##                 track.events.append(MusicalEvent(time=current_time_beats, pitch=pitch, duration=duration_per_event, velocity=90, technique=legato_technique))
##                 current_time_beats += duration_per_event
##         
##         song.tracks.append(track)
##         return song