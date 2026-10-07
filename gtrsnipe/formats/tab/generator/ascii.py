from typing import Dict, List, Optional
from ....core.types import FretPosition, Song, Technique, Track, Tuning
from ....core.config import MapperConfig
from ....guitar.mapper import GuitarMapper
from ....guitar.fingering import positioned
from ..tab_types import TabScore, TabMeasure, TabNote
from ..rhythm import (LAYOUTS, LETTERS_LINE, MAX_SLOTS, ODD_BARS, base_name, dashes_for, exact,
                      legend, letter_for, nearest_dashes, parse_base, pick_base)
from itertools import groupby
import logging
import math
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

class AsciiTabGenerator:
    @staticmethod
    def generate(song: Song, command_line: str, max_line_width: int = 80, default_note_length: str = "1/16", 
                 no_articulations: bool = False, 
                 single_string: Optional[int] = None, mapper_config: Optional[MapperConfig] = None,
                 premapped: bool = False, name_chords: bool = False,
                 chord_tone_threshold: Optional[float] = None, shape_names: bool = False,
                 rhythm: Optional[str] = None, base: Optional[str] = None,
                 odd_bars: str = "columns", letters: bool = False,
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
            rhythm: how a bar's columns carry time (F08, formats/tab/rhythm.py):
                'dashes' (the dashes after a note name its length), 'columns' (a
                note's column across the bar is its time) or 'loose' (spacing only
                hints). None: 'dashes', unless the song came from a tab that didn't
                state its rhythm (``song.rhythm_approximate``), which stays 'loose':
                the output shouldn't state lengths its source didn't.
            base: the dash-count base note ('1/16'); None = the tune's shortest note.
            odd_bars: a bar with a length the dash-count table lacks is written in
                'columns' (and named in the legend), with the 'nearest' lengths, or is
                an 'error'.
            letters: a line of note lengths (W H q e s t) over each row.
        """
        if rhythm is None:
            rhythm = "loose" if getattr(song, "rhythm_approximate", False) else "dashes"
        if rhythm not in LAYOUTS:
            raise ValueError(f"unknown tab rhythm {rhythm!r} ({', '.join(LAYOUTS)})")
        if odd_bars not in ODD_BARS:
            raise ValueError(f"unknown --tab-odd-bars {odd_bars!r} ({', '.join(ODD_BARS)})")
        base_beats = parse_base(base) if base and base != "auto" else None
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
                # the source tab's own fingering when it is kept as written, else the mapper's
                mapped_events = positioned(song, track.events, mapper, no_articulations=no_articulations,
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
        if getattr(song, "refingered", ""):
            banner.append(f"Fingering: gtrsnipe's, not the source tab's own ({song.refingered}).")
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
                                               chord_banner=banner, rhythm=rhythm, base=base_beats,
                                               odd_bars=odd_bars, letters=letters)

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
                               columns: Optional[list] = None, letters: Optional[list] = None) -> List[str]:
        """Formats a single measure using dynamic rhythmic spacing (the 'loose' layout).
        ``columns``, if given, collects (beat in measure, column of the fret digits)
        per onset. ``letters``, if given, collects (column, note-length letters), and
        the notes are spread just enough for the letters not to touch."""
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
        bar_beats = (measure.time_signature[0] / measure.time_signature[1]) * 4
        letter_end = 0                    # first column free for the next letter
        if letters is not None and events and events[0]['time'] > 1e-9:
            rest = letter_for(events[0]['time'])
            letters.append((0, rest))     # a letter with nothing under it: a rest
            letter_end = len(rest or "") + 1
        for k, event in enumerate(events):
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

            if letters is not None:
                start_pos = max(start_pos, letter_end)
                until = events[k + 1]['time'] if k + 1 < len(events) else bar_beats
                text = letter_for(until - time)
                letters.append((start_pos, text))
                letter_end = start_pos + len(text or "") + 1
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
        if letters is not None:
            final_len = max(final_len, letter_end - 1)   # the last letter ends inside its bar
    
        for j in range(config.num_strings):
            padding = final_len - len(measure_lines[j])
            measure_lines[j] += ('-' * padding)
        
        return measure_lines

    _SYMBOL = {"hammer-on": "h", "pull-off": "p", "tap": "t"}

    @staticmethod
    def _onsets(measure: TabMeasure, config: MapperConfig) -> List[tuple]:
        """A measure's notes grouped by onset: [(offset in beats, exact; [notes])]."""
        groups: Dict = {}
        for note in measure.notes:
            if 0 <= note.position.string < config.num_strings:
                groups.setdefault(exact(note.beat_in_measure), []).append(note)
        out = []
        for offset in sorted(groups):
            notes = groups[offset]
            if config.mono_lowest_only and len(notes) > 1:
                notes = [min(notes, key=lambda n: (-n.position.string, -n.position.fret))]
            out.append((offset, notes))
        return out

    @staticmethod
    def _place(lines: List[str], notes: List[TabNote], start: int, width: int) -> None:
        """Write one onset's fret numbers at column ``start`` (all lines are ``start``
        long), ``width`` columns wide; a technique letter takes the column before."""
        on_string = {n.position.string: n for n in notes}
        for s in range(len(lines)):
            note = on_string.get(s)
            if note is None:
                lines[s] += "-" * width
                continue
            symbol = AsciiTabGenerator._SYMBOL.get(note.technique.value, "") if note.technique else ""
            if symbol and start > 0:
                lines[s] = lines[s][:start - 1] + symbol
            lines[s] += str(note.position.fret).ljust(width, "-")

    @staticmethod
    def _bar_dashes(onsets: List[tuple], bar, n_strings: int, base, nearest: bool = False):
        """A bar in the dash-count layout: (lines, [(offset, column)], [(column, letters)]),
        or None if a length isn't in the table (``nearest``: use the closest that is)."""
        def count(length):
            dashes = dashes_for(length, base)
            return nearest_dashes(length, base) if dashes is None and nearest else dashes
        lead = onsets[0][0]
        lead_dashes = count(lead) if lead > 0 else 0
        if lead_dashes is None:
            return None
        lines = ["-" * (1 + lead_dashes)] * n_strings        # the padding dash, then any rest
        columns, letters = [], ([(0, letter_for(lead))] if lead > 0 else [])
        ends = [offset for offset, _ in onsets[1:]] + [bar]
        for (offset, notes), until in zip(onsets, ends):
            dashes = count(until - offset)
            if dashes is None:
                return None
            start = len(lines[0])
            lines = list(lines)
            AsciiTabGenerator._place(lines, notes, start, max(len(str(n.position.fret)) for n in notes))
            columns.append((float(offset), start))
            letters.append((start, letter_for(until - offset)))
            lines = [line + "-" * dashes for line in lines]
        return lines, columns, letters

    @staticmethod
    def _bar_columns(onsets: List[tuple], bar, n_strings: int, room_for_letters: bool = False):
        """A bar with columns as time: equal slots, one per the bar's shortest step, a
        note at the start of its slot, the last slot cut one column short by the bar
        line. None if the bar is on no grid worth drawing (``MAX_SLOTS``)."""
        values = [offset for offset, _ in onsets] + [bar]
        denominator = 1
        for v in values:
            denominator = denominator * v.denominator // math.gcd(denominator, v.denominator)
        step = 0
        for v in values:
            step = math.gcd(step, int(v * denominator))
        slots = int(bar * denominator) // step
        if slots > MAX_SLOTS:
            return None
        ends = values[1:]
        texts = [letter_for(until - offset) for (offset, _), until in zip(onsets, ends)]
        rest = letter_for(onsets[0][0]) if onsets[0][0] > 0 else ""
        at = [int(v * denominator) // step for v in values]          # each onset's slot; the bar's end
        slot = max([2] + [len(str(n.position.fret)) + 1 for _, notes in onsets for n in notes])
        if room_for_letters and None not in texts + [rest]:
            # a length's letters and a space must fit before the next onset
            spans = list(zip(texts, (b - a for a, b in zip(at, at[1:])))) + ([(rest, at[0])] if rest else [])
            slot = max([slot] + [-(-(len(text) + 1) // slots_long) for text, slots_long in spans])
        width = slots * slot
        lines = ["-" * width] * n_strings
        columns, letters = [], ([(1, rest)] if rest else [])
        for (offset, notes), text, k in zip(onsets, texts, at):
            start = 1 + k * slot
            head = [line[:start] for line in lines]
            AsciiTabGenerator._place(head, notes, start, max(len(str(n.position.fret)) for n in notes))
            lines = [h + line[len(h):] for h, line in zip(head, lines)]
            columns.append((float(offset), start))
            letters.append((start, text))
        return lines, columns, letters

    @staticmethod
    def _letter_line(entries: List[tuple]) -> str:
        """(column, letters) -> one line, each at its column. The layouts leave room, so
        letters never touch; a reader pairs a letter with the note it sits over."""
        line = ""
        for col, text in sorted(entries):
            line = line.ljust(col)[:col] + text
        return line

    @staticmethod
    def _format_score(score: TabScore, command_line: str, max_line_width: int, base_unit_in_beats: float,
                      config: MapperConfig, chord_labels: Optional[Dict[int, List[tuple]]] = None,
                      chord_banner: Optional[List[str]] = None, rhythm: str = "loose", base=None,
                      odd_bars: str = "columns", letters: bool = False) -> str:
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

        bars = AsciiTabGenerator._lay_out(score, base_unit_in_beats, config, rhythm, base, odd_bars, letters)
        rhythm_line = legend(rhythm, bars["base"], bars["in_columns"], bars["approximate"])

        if config.capo > 0:
            n = config.capo
            if 11 <= (n % 100) <= 13:
                suffix = "th"
            else:
                suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
            header.append(f"// Capo: {n}{suffix} Fret")

        if rhythm_line:
            header.append(f"// {rhythm_line}")
        if letters:
            header.append(f"// {LETTERS_LINE}")
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

        lengths: List[tuple] = []         # (column, note-length letters) for the current staff

        def flush():
            if names:
                body.append(AsciiTabGenerator._chord_name_line(names))
            if letters:
                body.append(AsciiTabGenerator._letter_line(lengths))
            body.extend(tab_lines)
            body.append("")

        for m_idx, measure in enumerate(score.measures):
            measure_content, columns, bar_letters = bars["bars"][m_idx]

            if len(tab_lines[0]) + len(measure_content[0]) + 1 > max_line_width:
                flush()
                tab_lines = [f"{name}|" for name in string_names]
                names = []
                lengths = []
            lengths += [(len(tab_lines[0]) + col, text) for col, text in bar_letters]

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
    def _lay_out(score: TabScore, base_unit_in_beats: float, config: MapperConfig, rhythm: str,
                 base, odd_bars: str, letters: bool) -> Dict:
        """Every bar's text in the chosen layout: ``bars`` [(lines, [(offset, column)],
        [(column, letters)])], plus what the legend must say: the ``base`` (dashes), and
        the 1-based numbers of the bars written ``in_columns`` or only ``approximate``."""
        n = config.num_strings
        num, den = score.time_signature
        bar = exact(num * 4.0 / den if den else num)
        out: Dict = {"bars": [], "base": None, "in_columns": [], "approximate": []}

        def loose(index, measure):
            columns, found = [], ([] if letters else None)
            lines = AsciiTabGenerator._format_single_measure(measure, base_unit_in_beats, config, index,
                                                             columns=columns, letters=found)
            if found and any(text is None for _, text in found):    # letters can't say this bar
                columns = []
                lines = AsciiTabGenerator._format_single_measure(measure, base_unit_in_beats, config, index,
                                                                 columns=columns)
            return lines, columns, found or []

        def lettered(drawn):
            """A bar's letters, kept only if every length has them and none touch."""
            lines, columns, found = drawn
            ends = [col for col, _ in found[1:]] + [len(lines[0]) + 1]
            if not letters or any(text is None or col + len(text) >= end
                                  for (col, text), end in zip(found, ends)):
                found = []
            return lines, columns, found

        if rhythm == "loose":
            out["bars"] = [lettered(loose(i, m)) for i, m in enumerate(score.measures)]
            return out

        onsets = [AsciiTabGenerator._onsets(m, config) for m in score.measures]
        silent = (["----"] * n, [], [])
        if rhythm == "columns":
            for i, (measure, found) in enumerate(zip(score.measures, onsets)):
                drawn = AsciiTabGenerator._bar_columns(found, bar, n, letters) if found else silent
                if drawn is None:                       # on no grid: spacing can only hint
                    drawn = loose(i, measure)
                    out["approximate"].append(i + 1)
                out["bars"].append(lettered(drawn))
            return out

        gaps = [g for found in onsets if found
                for g in [found[0][0]] + [b - a for a, b in zip([o for o, _ in found], [o for o, _ in found][1:] + [bar])]]
        out["base"] = exact(base) if base else pick_base(gaps)
        odd = []
        for i, found in enumerate(onsets):
            if not found:
                out["bars"].append(silent)
                continue
            drawn = AsciiTabGenerator._bar_dashes(found, bar, n, out["base"])
            if drawn is None:
                odd.append(i + 1)
                if odd_bars == "columns":
                    drawn = AsciiTabGenerator._bar_columns(found, bar, n, letters)
                    if drawn is not None:
                        out["in_columns"].append(i + 1)
                if drawn is None:
                    drawn = AsciiTabGenerator._bar_dashes(found, bar, n, out["base"], nearest=True)
                    out["approximate"].append(i + 1)
            out["bars"].append(lettered(drawn))
        if odd and odd_bars == "error":
            shown = ", ".join(map(str, odd[:20])) + (" ..." if len(odd) > 20 else "")
            raise ValueError(f"{len(odd)} bar(s) hold a note length the dash-count table doesn't, with "
                             f"base {base_name(out['base'])}: bars {shown}. Choose --tab-odd-bars columns or "
                             "nearest, another --tab-base, or --tab-rhythm columns.")
        return out

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
