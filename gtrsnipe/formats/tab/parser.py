from dataclasses import dataclass
from fractions import Fraction
from typing import List, Optional
import re
from ...core.types import MusicalEvent, Song, Track
from .rhythm import exact, length_for, letters_length, read_legend
from ...core.theory import note_name_to_pitch
from itertools import groupby
import logging

logger = logging.getLogger(__name__)

@dataclass
class _TabEvent:
    """A temporary data structure to hold note info before final timing is calculated."""
    char_idx: int
    string_idx: int
    fret: int
    technique: Optional[str] = None

class AsciiTabParser:
    """
    Parses an ASCII tablature string into a format-agnostic Song object,
    inferring rhythm from note spacing.
    """
    @staticmethod
    def _string_sustain(events, tab_string: str) -> None:
        """Let each note ring until the next note on the same string (the last one
        on a string: until the piece ends), never longer than one bar."""
        m = re.search(r"Time:\s*(\d+)\s*/\s*(\d+)", tab_string, re.IGNORECASE)
        bar = int(m.group(1)) * 4.0 / int(m.group(2)) if m and int(m.group(2)) else 4.0
        end = max(e.time + e.duration for e in events)
        by_string = {}
        for e in events:
            by_string.setdefault(e.string, []).append(e)
        for evs in by_string.values():
            evs.sort(key=lambda e: e.time)
            for a, b in zip(evs, evs[1:]):
                if b.time > a.time:
                    a.duration = min(b.time - a.time, bar)
            last = evs[-1]
            last.duration = min(max(end - last.time, last.duration), bar)

    @staticmethod
    def parse(tab_string: str, staccato: bool = False, quantization_resolution: float = 0.125,
              open_string_pitches: Optional[List[int]] = None, sustain: str = "legato",
              capo: Optional[int] = None) -> Song:
        """Read what the tab states: each note's string, fret and technique mark (h, p,
        t), its bar, and the header's tempo, time signature, tuning and capo.

        Timing: **each bar is one measure**, and a note sits in it in proportion to its
        column. A tab's columns say little about rhythm, but its bar lines say exactly
        where the measures are.

        ``open_string_pitches`` / ``capo``: how to read the frets; by default the tab's
        own ``// Tuning`` and ``// Capo`` lines (frets count from the capo).
        ``sustain`` (ignored with ``staccato``): how long a note lasts, since a tab
        only says when to strike. 'legato' (default): until the next onset.
        'string': until the same string is struck again -- how a guitar actually
        rings (arpeggios and pedal notes keep sounding) -- capped at one bar."""
        logger.debug("Starting ASCII Tab parsing.")
        song = Song()
        track = Track()

        tempo_match = re.search(r"Tempo:\s*([\d\.]+)", tab_string, re.IGNORECASE)
        if tempo_match:
            song.tempo = float(tempo_match.group(1))
        beats_per_bar = 4.0
        time_match = re.search(r"//\s*Time:\s*(\d+)\s*/\s*(\d+)", tab_string, re.IGNORECASE)
        if time_match and int(time_match.group(1)) and int(time_match.group(2)):
            song.time_signature = f"{int(time_match.group(1))}/{int(time_match.group(2))}"
            beats_per_bar = int(time_match.group(1)) * 4.0 / int(time_match.group(2))
        if capo is None:
            capo = AsciiTabParser.header_capo(tab_string) or 0

        # Read the embedded tuning header so a generated tab round-trips in its own
        # tuning (unless the caller supplied one explicitly, which wins).
        if open_string_pitches is None:
            open_string_pitches = AsciiTabParser.header_tuning(tab_string)

        lines = tab_string.split('\n')
        # A tab line is a short (1-3 char) string label then '|' — accepts any
        # tuning's labels (not just eBGDAE), and comment lines never match.
        def _is_tab_line(s):
            return bool(re.match(r'^\s*[^\s|]{1,3}\|', s))
        tab_lines = [line for line in lines if _is_tab_line(line)]

        # 1. First, simply check if any tab lines were found at all.
        if not tab_lines:
            logger.warning("Tab parsing failed: No valid tab lines found in the input.")
            return song

        # 2. Determine strings per block: the tuning header's count if known,
        # else the length of the first contiguous run of tab lines (robust to
        # duplicate labels like the two E strings, which the old start-char scan
        # mis-counted as 5).
        if open_string_pitches:
            num_strings = len(open_string_pitches)
        else:
            num_strings = 0
            for line in lines:
                if _is_tab_line(line):
                    num_strings += 1
                elif num_strings:
                    break

        if num_strings == 0:
            logger.warning("Tab parsing failed: Could not determine the number of strings.")
            return song

        logger.debug(f"Dynamically detected {num_strings} strings per block.")

        # 3. Split the tab into bars: whatever sits between bar lines, system by system.
        # Each bar keeps where it starts on the page, and the line just over its row
        # (which holds the note-length letters, when the header says there are any).
        said = read_legend(tab_string)
        tab_line_numbers = [i for i, line in enumerate(lines) if _is_tab_line(line)]
        bars: List[tuple] = []                       # (segments, page column, line above)
        for i in range(0, len(tab_lines), num_strings):
            raw = tab_lines[i:i + num_strings]
            rows = [ln.strip().split('|', 1)[1] for ln in raw]
            rows += [""] * (num_strings - len(rows))              # an incomplete last system
            first = tab_line_numbers[i]
            above = lines[first - 1] if said["letters"] and first > 0 else ""
            if above.strip().startswith("//") or _is_tab_line(above):
                above = ""
            page_col = raw[0].index('|') + 1
            cells = [row.split('|') for row in rows]
            for k in range(max(len(c) for c in cells)):
                segs = [c[k] if k < len(c) else "" for c in cells]
                width = max(len(x) for x in segs)
                here, page_col = page_col, page_col + len(cells[0][k] if k < len(cells[0]) else "") + 1
                if width == 0:
                    continue                                      # '||', or the text after the last bar line
                bars.append(([x.ljust(width, '-') for x in segs], here, above))

        # A tab gtrsnipe wrote (it has a '// Tuning' header) starts each note a set
        # number of dashes after the END of the note before it, so a two-digit fret
        # pushes everything after it one column right. That column isn't time. Other
        # tabs follow no known rule, so their columns are read as they stand.
        own_layout = bool(re.search(r"^\s*//\s*Tuning\b", tab_string, re.MULTILINE))
        marks = {'h': "hammer-on", 'p': "pull-off", 't': "tap"}
        bar_length = exact(beats_per_bar)
        approximate: List[int] = []                  # bars (1-based) whose rhythm was only hinted

        for bar_index, (segs, page_col, above) in enumerate(bars):
            found: List[_TabEvent] = []
            for string_idx, seg in enumerate(segs):
                for match in re.finditer(r'(\d+)', seg):
                    col = match.start()
                    tech = marks.get(seg[col - 1]) if col > 0 else None
                    found.append(_TabEvent(col, string_idx, int(match.group(1)), tech))
            if not found:
                continue
            width = len(segs[0])
            widest = {}                                # onset column -> its widest fret number
            for ev in found:
                widest[ev.char_idx] = max(widest.get(ev.char_idx, 1), len(str(ev.fret)))

            # What the tab states exactly comes first: note-length letters, then the
            # dash count, then columns as time. Failing those, the spacing only hints.
            hinted = (bar_index + 1) in said["approximate"]            # the writer said so
            in_columns = not hinted and (said["layout"] == "columns" or (bar_index + 1) in said["in_columns"])
            when = AsciiTabParser._by_letters(above, page_col, width, widest, bar_length, bar_index == 0)
            if when is None and said["layout"] == "dashes" and not in_columns and not hinted:
                when = AsciiTabParser._by_dash_count(widest, width, said["base"], bar_length, bar_index == 0)
            if when is None and in_columns:
                lead = 1 if min(widest) >= 1 else 0
                when = {col: (col - lead) / width * beats_per_bar for col in widest}
            if when is None:
                approximate.append(bar_index + 1)
                when = AsciiTabParser._by_spacing(widest, width, beats_per_bar, own_layout)
            for ev in found:
                note_time = bar_index * beats_per_bar + float(when[ev.char_idx])
                pitch = AsciiTabParser._tab_pos_to_midi(ev.string_idx, ev.fret, num_strings,
                                                        open_string_pitches) + capo
                track.events.append(MusicalEvent(
                    time=note_time, pitch=pitch,
                    duration=quantization_resolution,        # the legato pass adjusts this
                    velocity=90, string=ev.string_idx, fret=ev.fret, technique=ev.technique))

        # Did the tab state its rhythm? If any bar's was only hinted, nothing written
        # from this song should claim exact lengths (the tab generator checks this).
        song.rhythm_approximate = bool(approximate)
        if approximate and (said["layout"] or said["letters"]):
            shown = ", ".join(map(str, approximate[:12])) + (" ..." if len(approximate) > 12 else "")
            logger.info(f"Tab rhythm: bar(s) {shown} read by their spacing (the legend names them as "
                        "approximate, or they don't add up to a measure as written).")

        if not track.events:
            logger.warning("No notes found in tab string.")
        else:
            logger.debug(f"Finished parsing. Total notes: {len(track.events)}. "
                         f"Bars: {len(bars)}.")

        # --- Pass 3: If staccato is enabled, modify the events now in the track ---
        if not staccato and track.events:
            logger.debug("Applying legato processing.")
            sorted_events = sorted(track.events, key=lambda e: e.time)
            events_grouped_by_time = [list(g) for t, g in groupby(sorted_events, key=lambda e: e.time)]
            
            logger.debug(f"Grouped notes into {len(events_grouped_by_time)} distinct time slices.")
            
            if len(events_grouped_by_time) <= 1:
                logger.debug("Cannot apply legato: only one time slice found. All notes may have the same start time.")
            else:
                for i in range(len(events_grouped_by_time) - 1):
                    current_group = events_grouped_by_time[i]
                    next_group = events_grouped_by_time[i+1]
                    duration = next_group[0].time - current_group[0].time
                    
                    logger.debug(f"Time: {current_group[0].time:<5.2f} | Notes: {str([e.pitch for e in current_group]):<15} | Old Duration: {current_group[0].duration:.2f} | New Duration: {duration:.2f}")

                    for event in current_group:
                        event.duration = duration
            # the last notes ring to the end of their bar (they have no next onset)
            last = events_grouped_by_time[-1]
            bar_end = (int(last[0].time // beats_per_bar) + 1) * beats_per_bar
            for event in last:
                event.duration = max(bar_end - event.time, event.duration)
        elif staccato:
            logger.debug("Staccato flag set, skipping legato processing.")

        # --- Pass 4: 'string' sustain: a note rings until its own string is struck again
        if sustain == "string" and not staccato and track.events:
            AsciiTabParser._string_sustain(track.events, tab_string)

        song.tracks.append(track)
        logger.debug("Finished creating Song object.")
        return song

    @staticmethod
    def _by_letters(above: str, page_col: int, width: int, widest: dict, bar, first_bar: bool):
        """Onset column -> offset in the bar, from the note-length letters over it; None
        if there are none, they don't sit over the notes, or don't add up to the bar.
        A letter with no note under it is a rest; a short first bar is a pickup."""
        tokens = [(m.start() - page_col, m.group(0)) for m in re.finditer(r"\S+", above)
                  if page_col <= m.start() < page_col + width]
        if not tokens or {col for col, _ in tokens} < set(widest):
            return None
        at, when = Fraction(0), {}
        for col, token in tokens:
            length = letters_length(token)
            if length is None:
                return None
            if col in widest:
                when[col] = at
            at += length
        if set(when) != set(widest):
            return None
        if at == bar:
            return when
        if first_bar and at < bar:
            return {col: t + (bar - at) for col, t in when.items()}
        return None

    @staticmethod
    def _by_dash_count(widest: dict, width: int, base, bar, first_bar: bool):
        """Onset column -> offset in the bar, from the dashes after each note (counted
        from the end of its fret number); None if the bar isn't written that way or
        doesn't add up to a measure. A short first bar is a pickup."""
        starts = sorted(widest)
        if starts[0] < 1:
            return None                              # no padding dash: not this layout
        at = Fraction(0)
        if starts[0] > 1:
            rest = length_for(starts[0] - 1, base)
            if rest is None:
                return None
            at = rest
        when = {}
        for col, nxt in zip(starts, starts[1:] + [width]):
            length = length_for(nxt - (col + widest[col]), base)
            if length is None:
                return None
            when[col] = at
            at += length
        if at == bar:
            return when
        if first_bar and at < bar:
            return {col: t + (bar - at) for col, t in when.items()}
        return None

    @staticmethod
    def _by_spacing(widest: dict, width: int, beats_per_bar: float, own_layout: bool) -> dict:
        """Onset column -> offset in the bar when the tab only hints: a note's time is
        its column over the bar's width (the bar's first dash is padding)."""
        late, shift = {}, 0                           # start column -> columns to take off
        if own_layout:
            for col in sorted(widest):
                late[col] = shift
                shift += widest[col] - 1
            width -= shift
        starts = sorted(col - late.get(col, 0) for col in widest)
        # The bar line usually cuts the last note's slot one column short ("-5-7-8-5|"
        # is four equal slots), so the whole width is the measure; unless a tab from
        # elsewhere has evenly spaced notes whose slots end exactly at the bar line
        # ("-5-7-8-5-|"), where the padding is extra.
        lead = 1 if starts[0] >= 1 else 0
        span = width
        step = min((b - a for a, b in zip(starts, starts[1:])), default=0)
        if not own_layout and step and (width - lead) % step == 0:
            span = width - lead
        span = max(span, 1)
        return {col: (col - late.get(col, 0) - lead) / span * beats_per_bar for col in widest}

    @staticmethod
    def header_capo(tab_string: str) -> Optional[int]:
        """The capo fret from a tab's '// Capo: 2nd Fret' line, or None."""
        m = re.search(r"//\s*Capo:\s*(\d+)", tab_string, re.IGNORECASE)
        return int(m.group(1)) if m else None

    @staticmethod
    def header_tuning(tab_string: str) -> Optional[List[int]]:
        """Open-string pitches (index 0 = highest string) from a tab's embedded
        tuning header, or None. Handles the current '// Tuning: <low..high>' and
        the legacy '// Tuning (High to Low): ...'."""
        hm = re.search(r"//\s*Tuning([^:]*):\s*(.+)", tab_string, re.IGNORECASE)
        if not hm:
            return None
        names = [x for x in re.split(r"[,\s]+", hm.group(2).strip()) if x]
        try:
            pitches = [note_name_to_pitch(x) for x in names]
        except ValueError:
            return None  # unparseable header -> fall back
        # index 0 = highest string; names low->high unless labeled otherwise.
        return pitches if "high to low" in hm.group(1).lower() else list(reversed(pitches))

    @staticmethod
    def _tab_pos_to_midi(string_idx: int, fret: int, num_strings: int,
                         open_string_pitches: Optional[List[int]] = None) -> int:
        """Converts a string/fret position to a MIDI pitch.

        Uses the caller-supplied ``open_string_pitches`` (high->low) when given —
        so a tab is decoded in its actual tuning — else falls back to standard
        guitar/bass tuning by string count.
        """
        if not open_string_pitches:
            # Standard 6-String Guitar (high->low) / 4-String Bass fallback.
            guitar_tuning = [64, 59, 55, 50, 45, 40]
            bass_tuning = [43, 38, 33, 28]  # G2, D2, A1, E1
            open_string_pitches = bass_tuning if num_strings == 4 else guitar_tuning

        # Ensure we don't go out of bounds if string_idx is too high
        if string_idx >= len(open_string_pitches):
            logger.error(f"Invalid string index {string_idx} for a {num_strings}-string instrument.")
            return 0 # Return a default, silent pitch
    
        return open_string_pitches[string_idx] + fret