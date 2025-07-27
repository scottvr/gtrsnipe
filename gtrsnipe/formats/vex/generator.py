from itertools import groupby
from ...core.types import Song
from ...core.config import MapperConfig
from ...guitar.mapper import GuitarMapper
from typing import Optional
class VextabGenerator:
    @staticmethod
    def generate(song: Song, default_note_length: str = "1/16", no_articulations=False,
                 single_string: Optional[int] = None, mapper_config: Optional[MapperConfig] = None, **kwargs) -> str:
        """
        Converts a Song object into a complete VexTab notation string.
        """
        if mapper_config is None:
            mapper_config = MapperConfig()
        try:
            denominator = int(default_note_length.split('/')[1])
        except (ValueError, IndexError):
            denominator = 16

        measures_per_line = 4
        if denominator >= 16:
            measures_per_line = 2
        elif denominator >= 8:
            measures_per_line = 3

        output_parts = [f"options tempo={int(song.tempo)}",
                        "text Title: {song.title}",
                        ""]
        
        mapper = GuitarMapper(config=mapper_config)
        all_mapped_events = []
        for track in song.tracks:
            if not track.events: continue
            mapped_events = mapper.map_events_to_fretboard(track.events, no_articulations=no_articulations,
                                                           single_string=single_string)
            all_mapped_events.extend(mapped_events)

        # Sort all events by time to process them chronologically
        sorted_events = sorted(all_mapped_events, key=lambda e: e.time)
        if not sorted_events: return "\n".join(output_parts)

        # Group notes by time to form chords
        time_events = []
        for time, notes_in_group_iter in groupby(sorted_events, key=lambda e: e.time):
            notes = list(notes_in_group_iter)
            time_events.append({'time': time, 'notes': notes})
        
        try:
            num, den = map(int, song.time_signature.split('/'))
            beats_per_measure = num * (4 / den)
        except (ValueError, ZeroDivisionError): beats_per_measure = 4

        # Group notes by which line they will appear on
        events_by_line = groupby(time_events, key=lambda e: int(e['time'] / beats_per_measure) // measures_per_line)

        for line_number, line_events_iter in events_by_line:
            notes_for_current_line = []
            for event in line_events_iter:
                # Use the duration from the first note of the event (chord or single note)
                duration_in_beats = max(n.duration for n in event['notes'])
                duration_str = VextabGenerator._duration_to_vextab(duration_in_beats)


                # Format the notes (handles single notes and chords)
                if len(event['notes']) == 1:
                    note = event['notes'][0]
                    note_str = f"{note.fret}/{note.string + 1}"
                else:
                    chord_parts = [f"{n.fret}/{n.string + 1}" for n in event['notes']]
                    note_str = f"({'.'.join(chord_parts)})"
                
                notes_for_current_line.append(f"{duration_str} {note_str}")

            if notes_for_current_line:
                tabstave_header = f"\ntabstave notation=true time={song.time_signature}" if line_number > 0 else f"tabstave notation=true time={song.time_signature}"
                output_parts.append(tabstave_header)
                output_parts.append(f"notes {' '.join(notes_for_current_line)}")

        return "\n".join(output_parts)
    
    @staticmethod
    def _duration_to_vextab(duration_in_beats: float) -> str:
        """
        Quantizes the given duration in beats to the nearest standard VexTab duration string.
        """
        duration_map = {
            ":w": 4.0, ":hd": 3.0, ":h": 2.0, ":qd": 1.5, ":q": 1.0,
            ":8d": 0.75, ":8": 0.5, ":16": 0.25, ":32": 0.125
        }

        if duration_in_beats <= 0:
            return ":q" 

        closest_duration_str = min(
            duration_map.keys(),
            key=lambda k: abs(duration_map[k] - duration_in_beats)
        )
        return closest_duration_str
