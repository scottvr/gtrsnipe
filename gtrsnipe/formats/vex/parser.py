from ...core.types import Song, MusicalEvent, Track
import re

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
        # Note: VexTab strings are 1-6 from high E to low E.
        # Our internal representation is 0-5 from high E to low E.
        # So we subtract 1 from the VexTab string number.
        open_string_pitches = [64, 59, 55, 50, 45, 40]
        if not (1 <= string_num <= 6):
            return -1 # Invalid string number
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

            note_atoms = re.findall(r'(\d+)/(\d+)', token) # Find all "fret/string" pairs
            if not note_atoms: continue

            # Check if the token represents a chord
            is_chord = token.startswith('(') and token.endswith(')')

            if is_chord:
                # For a chord, all notes start at the same time and have the same duration.
                for fret_str, string_str in note_atoms:
                    pitch = VextabParser._vextab_pos_to_midi(int(string_str), int(fret_str))
                    if pitch != -1:
                        track.events.append(MusicalEvent(
                            time=current_time_beats,
                            pitch=pitch,
                            duration=current_duration_beats,
                            velocity=90
                        ))
                # Advance the timeline once for the entire chord
                current_time_beats += current_duration_beats
            else:
                # For single notes or legato runs, subdivide the duration.
                # This correctly handles runs like ":16 5h7p5/3"
                num_events_in_token = len(note_atoms)
                duration_per_event = current_duration_beats / num_events_in_token
                
                techniques = re.findall(r'[ph]', token)

                for i, (fret_str, string_str) in enumerate(note_atoms):
                    pitch = VextabParser._vextab_pos_to_midi(int(string_str), int(fret_str))
                    if pitch == -1: continue

                    technique = None
                    # Determine technique for notes after the first one in a run
                    if i > 0 and (i - 1) < len(techniques):
                        tech_char = techniques[i-1]
                        if tech_char == 'h': technique = 'hammer-on'
                        elif tech_char == 'p': technique = 'pull-off'

                    track.events.append(MusicalEvent(
                        time=current_time_beats,
                        pitch=pitch,
                        duration=duration_per_event,
                        velocity=90,
                        technique=technique
                    ))
                    # Advance the time for each note in the run
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