from typing import Dict, List, Optional
from ....core.types import FretPosition, Song, Technique, Track, Tuning
from ....core.config import MapperConfig
from ....guitar.mapper import GuitarMapper
from ..tab_types import TabScore, TabMeasure, TabNote
from itertools import groupby
import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

class AsciiTabGenerator:
    @staticmethod
    def generate(song: Song, command_line: str, max_line_width: int = 40, default_note_length: str = "1/16", 
                 no_articulations: bool = False, 
                 single_string: Optional[int] = None, mapper_config: Optional[MapperConfig] = None,
                 premapped: bool = False, name_chords: bool = False,
                 chord_tone_threshold: Optional[float] = None, shape_names: bool = False,
                 **kwargs) -> str:
        """
        Generates an ASCII tab string from a Song object.
        Args:
            song: The Song object to convert.
            max_line_width: The maximum character width before breaking a line.
            default_note_length: The "base unit" for rhythmic spacing (e.g., "1/8", "1/16").
            premapped: the events already carry string/fret (e.g. a solved
                homograph tab) -- render them as-is instead of re-mapping.
            name_chords: write chord names (concert pitch) above each staff, one per
                measure, where the harmony changes and at the start of each line.
                Measures are named as in the chord charts (``chords.segment``).
        """
        if mapper_config is None:
            mapper_config = MapperConfig()

        mapper = GuitarMapper(config=mapper_config)
        mapped_song = Song(tempo=song.tempo, time_signature=song.time_signature, title=song.title, tracks=[])

        total_mapped_notes = 0
        for track in song.tracks:
            if premapped:
                mapped_events = mapper._infer_techniques_from_positions(
                    sorted(track.events, key=lambda e: e.time), no_articulations)
            else:
                mapped_events = mapper.map_events_to_fretboard(track.events, no_articulations=no_articulations,
                                                               single_string=single_string)
            total_mapped_notes += len(mapped_events)
            new_track = Track(events=mapped_events, instrument_name=track.instrument_name)
            mapped_song.tracks.append(new_track)

        logger.info(f"--- Successfully mapped {total_mapped_notes} notes for transcription. ---")
        score = AsciiTabGenerator._create_score_from_song(mapped_song)
        
        # Calculate the base unit in beats to pass to the formatter
        #try:
        #    num, den = map(int, default_note_length.split('/'))
        #    base_unit_in_beats = (num / den) * 4
        #except (ValueError, ZeroDivisionError):
        #    base_unit_in_beats = 0.25 # Default to a 16th note
        base_unit_in_beats = mapper_config.quantization_resolution

        chord_labels, banner = None, []
        if name_chords:
            from ....chords.segment import DEFAULT_CHORD_TONE_THRESHOLD
            from ....core.keys import song_key
            threshold = (DEFAULT_CHORD_TONE_THRESHOLD if chord_tone_threshold is None
                         else chord_tone_threshold)
            # names are spelled in the song's key: its own, else estimated (and said so)
            key, key_how = song_key(song)
            if key:
                banner.append(f"Chord names are spelled in {key.name} ({key_how}).")
            naming = None
            if shape_names:
                from ....chords.shape_names import shape_naming_for_config
                naming = shape_naming_for_config(mapper_config)
                banner.append(naming.banner)
            chord_labels = AsciiTabGenerator._bar_chord_names(mapped_song, threshold, naming, key)

        return AsciiTabGenerator._format_score(score, command_line, max_line_width, base_unit_in_beats,
                                               mapper_config, chord_labels=chord_labels,
                                               chord_banner=banner)

    @staticmethod
    def _bar_chord_names(song: Song, threshold: float, naming=None, key=None) -> Dict[int, List[tuple]]:
        """Bar index -> [(beat in bar, chord name)] for ``--name-chords``.

        Each bar is named whole and by halves. Two different clear chords in the
        halves give two names (a bar of C then G, which named whole reads as "G6");
        otherwise the whole bar's name, or a lone clear half's. Only plainly spelled
        chords count (``is_clear``): over a tab a doubtful name is worse than none."""
        from ....chords.segment import beats_per_measure, segment_by_measure
        from ....core.chords import is_clear

        def clear(parts):
            return {s.index: (naming.name(s.chord) if naming else s.chord.name)
                    for s in segment_by_measure(song, threshold, keep_downbeat_bass=True,
                                                parts=parts, key=key)
                    if s.chord is not None and is_clear(s.chord, s.pitches)}
        whole, halves = clear(1), clear(2)
        half = beats_per_measure(song.time_signature) / 2
        bars = set(whole) | {i // 2 for i in halves}
        names: Dict[int, List[tuple]] = {}
        for m in sorted(bars):
            h1, h2, w = halves.get(2 * m), halves.get(2 * m + 1), whole.get(m)
            if h1 and h2 and h1 != h2:
                names[m] = [(0.0, h1), (half, h2)]
            elif w:
                names[m] = [(0.0, w)]
            elif h1:
                names[m] = [(0.0, h1)]
            elif h2:
                names[m] = [(half, h2)]
        return names

    @staticmethod
    def _create_score_from_song(song: Song) -> TabScore:
        num, den = map(int, song.time_signature.split('/'))
        time_sig_tuple = (num, den)

        if song.tracks:
            main_track = song.tracks[0]
            instrument = main_track.instrument_name
            if instrument and instrument != 'Acoustic Grand Piano':
                song.title = f"{song.title} ({instrument})"

        score = TabScore(tempo=song.tempo, time_signature=time_sig_tuple, tuning_name="STANDARD", title=song.title)

        all_events = [event for track in song.tracks for event in track.events]
        if not all_events: return score
        
        # event.time is in quarter-note beats, so beats-per-measure must account
        # for the denominator: (num/den)*4. Using the numerator alone mis-sizes
        # measures for any non-quarter denominator (6/8, 3/8, 2/2).
        num_ts, den_ts = time_sig_tuple[0], time_sig_tuple[1]
        beats_per_measure = num_ts * (4.0 / den_ts) if den_ts else float(num_ts)
        # Sort all events by time to process them in chronological order
        all_events.sort(key=lambda e: e.time)

        current_measure_num = -1

        for event in all_events:
            if event.string is None or event.fret is None: continue
        
            beat_time = event.time
            measure_num = int(beat_time / beats_per_measure)
        
            if measure_num > current_measure_num:
                # Add any empty measures between the last note and this one
                for i in range(measure_num - current_measure_num):
                    score.measures.append(TabMeasure([], time_sig_tuple))
                current_measure_num = measure_num

            beat_in_measure = beat_time % beats_per_measure
            note = TabNote(
                position=FretPosition(event.string, event.fret), 
                technique=Technique(event.technique) if event.technique else None, 
                beat_in_measure=beat_in_measure, 
                duration=event.duration
            )
        
            if score.measures:
                score.measures[-1].notes.append(note)
            
        return score

    @staticmethod
    def _format_single_measure(measure: TabMeasure, base_unit_in_beats: float, config: MapperConfig, measure_index: int,
                               columns: Optional[list] = None) -> List[str]:
        """Formats a single measure using dynamic rhythmic spacing. ``columns``, if
        given, collects (beat in measure, column of the fret digits) per onset."""
        measure_lines = ["-"] * config.num_strings
        if not measure.notes:
            # Handle empty measures
            padding = measure.time_signature[0] * 4 # Default padding for empty measure
            for i in range(config.num_strings):
                measure_lines[i] = '-' * padding
            return measure_lines
            
        sorted_notes = sorted(measure.notes, key=lambda n: n.beat_in_measure)
    
        if config.mono_lowest_only:
            filtered_notes = []
            # Group notes by their precise beat in the measure
            for time, notes_in_group in groupby(sorted_notes, key=lambda n: n.beat_in_measure):
                notes = list(notes_in_group)
                if len(notes) > 1:
                    # If it's a chord, find and keep only the lowest note
                    # Negate the string number to correctly prioritize lower-pitched strings (higher string numbers).
                    lowest_note = min(notes, key=lambda note: (-note.position.string, -note.position.fret))
                    filtered_notes.append(lowest_note)
                else:
                    # If it's a single note, keep it
                    filtered_notes.append(notes[0])
            # The list of notes to render is now the filtered monophonic list
            sorted_notes = filtered_notes
    
        notes_by_time_iter = groupby(sorted_notes, key=lambda n: n.beat_in_measure)
        
        # --- 1. Find the Smallest Rhythmic Unit for this Measure ---
        events = [{'time': time, 'notes': list(notes)} for time, notes in notes_by_time_iter]
        smallest_time_delta = float('inf')
        last_event_time_for_calc = 0.0
    
        if len(events) > 1:
            for i in range(1, len(events)):
                delta = events[i]['time'] - events[i-1]['time']
                if 0 < delta < smallest_time_delta:
                    smallest_time_delta = delta
        
        # If all notes are on the same beat or only one event, use a default unit (e.g., 16th note)
        if smallest_time_delta == float('inf'):
            smallest_time_delta = base_unit_in_beats # Defaults to 16th note duration
    
        # --- 2. Build the Measure String ---
        last_event_time = 0.0
        for event in events:
            time = event['time']
            notes_in_chord = event['notes']
    
            time_delta = time - last_event_time
            
            # Calculate spacing based on the smallest unit for this measure
            # The number of dashes is the time delta divided by our quantum unit
            spacing = int(round(time_delta / smallest_time_delta)) if smallest_time_delta > 0 else 1
            
            # Get the length of the longest current string line to align notes
            max_len = max(len(s) for s in measure_lines) if any(measure_lines) else 0
            start_pos = max_len + spacing

            tech_map = {"hammer-on": "h", "pull-off": "p", "tap": "t"}

            def _symbol(n):
                return tech_map.get(n.technique.value, "") if n.technique else ""

            # A technique letter goes in the column(s) BEFORE its fret digits, so every
            # note of the event keeps its digits in the same column -- the parser times
            # a note by its digit column, so a shifted digit would split the chord.
            # If a letter has no room there, move the whole event right together.
            for note in notes_in_chord:
                sym = _symbol(note)
                if sym and 0 <= note.position.string < len(measure_lines):
                    room = start_pos - len(measure_lines[note.position.string])
                    if room < len(sym):
                        start_pos += len(sym) - room

            if columns is not None:
                columns.append((time, start_pos))
            for note in notes_in_chord:
                str_idx = note.position.string
                if not (0 <= str_idx < len(measure_lines)):
                    logger.warning(f"Note with string index {str_idx} out of bounds. Skipping.")
                    continue

                sym = _symbol(note)
                padding_needed = start_pos - len(measure_lines[str_idx]) - len(sym)
                measure_lines[str_idx] += ('-' * padding_needed) + sym + str(note.position.fret)
            
            last_event_time = time
        
        # --- 3. Final Padding to Fill the Measure ---
        # Calculate the total expected duration of the measure in beats
        total_measure_beats = (measure.time_signature[0] / measure.time_signature[1]) * 4
        
        # Calculate the total length this represents in our dynamic spacing units
        total_measure_units = int(round(total_measure_beats / smallest_time_delta)) if smallest_time_delta > 0 else 16
        
        final_max_len = max(len(s) for s in measure_lines) if measure_lines else 0
        
        # Use the greater of the rendered content or the expected total length
        final_len = max(final_max_len, total_measure_units)
    
        for j in range(config.num_strings):
            padding = final_len - len(measure_lines[j])
            measure_lines[j] += ('-' * padding)
        
        return measure_lines

    @staticmethod
    def _format_score(score: TabScore, command_line: str, max_line_width: int, base_unit_in_beats: float,
                      config: MapperConfig, chord_labels: Optional[Dict[int, List[tuple]]] = None,
                      chord_banner: Optional[List[str]] = None) -> str:
        """Formats the complete score, breaking lines based on character width.

        ``chord_labels`` (measure index -> [(beat in measure, chord name)]) adds a
        line of names above each staff: a name sits over the first note at or after
        its beat, and is written where the chord changes and again at the start of
        each staff."""
        
        # String labels are indexed 0 = highest, so we need names HIGH->low. Tuning
        # tuples (and custom_tuning) are stored low->high, so reverse them; a custom
        # tuning supplies its own names (the enum has no "CUSTOM" entry).
        if getattr(config, "custom_tuning", None):
            tuning_notes = list(reversed(config.custom_tuning))
        else:
            try:
                tuning_notes = list(reversed(Tuning[config.tuning].value))
            except KeyError:
                tuning_notes = list(reversed(Tuning.STANDARD.value))

        # --- New logic to generate conventional string names ---
        string_names = []
        is_bass_tuning = config.tuning.startswith('BASS_')
        
        for i, note in enumerate(tuning_notes):
            natural_name = note[0]  # Get the first character (e.g., "E" from "Eb4")

            if is_bass_tuning:
                # For bass, all names are uppercase
                display_name = natural_name.upper()
            else:
                # For guitars (6, 7, baritone), high string is lowercase
                display_name = natural_name.lower() if i == 0 else natural_name.upper()
                        
            string_names.append(display_name)
        # --- End of new logic ---

        header = [
            f"// Title: {score.title}",
            f"// Tempo: {int(score.tempo)} BPM",
            f"// Time: {score.time_signature[0]}/{score.time_signature[1]}",
            f"// Tuning: {','.join(reversed(tuning_notes))}",
            ""
        ]

        if config.capo > 0:
            n = config.capo
            if 11 <= (n % 100) <= 13:
                suffix = "th"
            else:
                suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
            header.append(f"// Capo: {n}{suffix} Fret")

        for line in chord_banner or []:
            header.append(f"// {line}")

        if command_line:
            # Clean up the command for display (optional, but nice)
            executable_name = Path(sys.argv[0]).name
            display_command = command_line.replace(sys.argv[0], executable_name)
            header.append(f"// Transcribed with: {display_command}")

        header.append("") # Add a blank line after the heade1r info

        body = []
        # 'ljust' is no longer needed as all names are a single character
        tab_lines = [f"{name}|" for name in string_names]
        names: List[tuple] = []           # (column, chord name) for the current staff
        last_label: Optional[str] = None

        def flush():
            if names:
                body.append(AsciiTabGenerator._chord_name_line(names))
            body.extend(tab_lines)
            body.append("")

        for m_idx, measure in enumerate(score.measures):
            columns: list = []
            measure_content = AsciiTabGenerator._format_single_measure(measure, base_unit_in_beats, config, m_idx,
                                                                       columns=columns)
            
            if len(tab_lines[0]) + len(measure_content[0]) + 1 > max_line_width:
                flush()
                tab_lines = [f"{name}|" for name in string_names]
                names = []

            for beat, label in (chord_labels.get(m_idx, []) if chord_labels else []):
                col = next((c for t, c in columns if t >= beat - 1e-6), None)
                if col is None:
                    continue                  # no note at or after this beat
                if label != last_label or not names:
                    names.append((len(tab_lines[0]) + col, label))
                last_label = label

            for i in range(config.num_strings):
                tab_lines[i] += measure_content[i] + "|"

        if len(tab_lines[0]) > 2:
            flush()

        return "\n".join(header + body)

    @staticmethod
    def _chord_name_line(names: List[tuple]) -> str:
        """Place each (column, name) on one line, nudging a name right when the one
        before it would run into it (always at least one space between names)."""
        line = ""
        for col, text in names:
            if line:
                col = max(col, len(line) + 1)
            line += " " * (col - len(line)) + text
        return line
