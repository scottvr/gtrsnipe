from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Dict, Set, Tuple
#from gtrsnipe import Technique, FretPosition, Tuning, MusicalEvent, TimeSignature, GuitarProgram
from .types import FretPosition, Technique, Tuning,MusicalEvent, TimeSignature
from ..computer.program import GuitarProgram, create_musical_events
from ..computer.cpu import GuitarCPU
from .operations import GuitarOperation

@dataclass
class TabNote:
    """Represents a single note in a tab"""
    position: FretPosition
    beat_in_measure: float
    technique: Optional[Technique] = None
    duration: float = 1.0
    annotation: Optional[str] = None

@dataclass
class TabMeasure:
    """Represents a measure of tab"""
    notes: List[TabNote]
    time_signature: tuple[int, int] = (4, 4)
    
    @property
    def beats(self) -> int:
        return self.time_signature[0]

class TabScore:
    """Represents a complete tab score"""
    def __init__(self, 
                 tuning: Tuning = Tuning.STANDARD,
                 time_signature: tuple[int, int] = (4, 4),
                 tempo: float = 120.0):
        self.tuning = tuning
        self.time_signature = time_signature
        self.tempo = tempo
        self.measures: List[TabMeasure] = []
        self.annotations: Dict[int, str] = {}  # Measure number to annotation

class TabFormatter:
    """Handles the formatting and display of guitar tablature"""
    def __init__(self, measures_per_line: int = 2, tuning: Tuning = Tuning.STANDARD):
        self.measures_per_line = measures_per_line
        self.string_names = ['e', 'B', 'G', 'D', 'A', 'E']
        self.tuning = tuning
        self.chars_per_beat = 12  # Default spacing

    def format_score(self, score: TabScore) -> str:
        """Format a complete tab score"""
        lines = [
            "// Guitar Tab Score",
            f"// Time signature: {score.time_signature[0]}/{score.time_signature[1]}",
            f"// Tempo: {score.tempo} BPM",
            f"// Tuning: {score.tuning.name}",
            ""
        ]
        
        # Format measures in groups
        for start_measure in range(0, len(score.measures), self.measures_per_line):
            end_measure = min(start_measure + self.measures_per_line, len(score.measures))
            measure_group = score.measures[start_measure:end_measure]
            
            # Add beat numbers
            lines.extend(self._format_measure_group_header(measure_group))
            
            # Add tab lines
            lines.extend(self._format_measure_group(measure_group))
            
            # Add any measure annotations
            for i, measure_num in enumerate(range(start_measure, end_measure)):
                if measure_num in score.annotations:
                    lines.append(f"// M{measure_num + 1}: {score.annotations[measure_num]}")
            
            lines.append("")  # Empty line between groups
        
        return "\n".join(lines)

    def _format_measure_group_header(self, measures: List[TabMeasure]) -> List[str]:
        """Format the beat numbers header for a group of measures"""
        header = "    "  # Initial spacing
        for measure in measures:
            print(f'DBG: hdr-msr {measure}')
            # Use the time signature's numerator for number of beats
            beats_per_measure = measure.time_signature[0]
            header += "".join(f"{b + 1:<12}" for b in range(beats_per_measure))[:-1] + "|-"
        return [header]

    def _format_measure_group(self, measures: List[TabMeasure]) -> List[str]:
        """Format a group of measures"""
        # Initialize string lines
        string_lines = [f"{name}|-" for name in self.string_names]
        
        # Add each measure
        for measure in measures:
            print(f'DBG: hdr-msr {measure}')
            measure_strings = self._format_measure(measure)
            for i, content in enumerate(measure_strings):
                string_lines[i] += f"{content}|"
        
        return string_lines

    def _format_measure(self, measure: TabMeasure) -> List[str]:
        """Format a single measure"""
        print(f'DEBUG: {measure}')
        beats_per_measure = measure.time_signature[0]
        width = beats_per_measure * self.chars_per_beat
        strings = [list('-' * width) for _ in range(6)]
        
        # Sort notes by time position within measure
        for note in sorted(measure.notes, key=lambda n: n.beat_in_measure):
            string_idx = note.position.string
            fret_str = str(note.position.fret)
            
            # Calculate beat position within measure
            beat_offset = int(note.beat_in_measure * self.chars_per_beat)
            
            # Add padding dash for single digit
            if len(fret_str) == 1:
                if beat_offset < width:
                    strings[string_idx][beat_offset] = '-'
                beat_offset += 1
            
            # Place the note
            for i, char in enumerate(fret_str):
                if beat_offset + i < width:
                    strings[string_idx][beat_offset + i] = char

            # Add technique symbol if present
            if note.technique:
                technique_symbol = {
                    Technique.HAMMER: 'h',
                    Technique.PULL: 'p',
                    Technique.BEND: 'b',
                    Technique.SLIDE: '/',
                    Technique.TAP: 't',
                    Technique.HARMONIC: '*'
                }.get(note.technique)
                if technique_symbol and beat_offset + len(fret_str) < width:
                    strings[string_idx][beat_offset + len(fret_str)] = technique_symbol
        
        return [''.join(s) for s in strings]

    def create_tab_from_events(self, events: List[MusicalEvent], 
                              tempo: float, 
                              time_sig: tuple[int, int]) -> TabScore:
        """Convert musical events to a tab score"""
        score = TabScore(tempo=tempo, time_signature=time_sig)
        current_measure = TabMeasure([], time_sig)
        beats_per_measure = time_sig[0]
        seconds_per_beat = 60.0 / tempo
        
        for event in sorted(events, key=lambda e: e.time):
            # Convert to beats
            beat_time = event.time / seconds_per_beat
            beat_duration = event.duration / seconds_per_beat
            beat_in_measure = beat_time % beats_per_measure
        
            # Calculate measure number
            measure_num = int(beat_time / beats_per_measure)
            
            # Create new measures if needed
            while len(score.measures) <= measure_num:
                score.measures.append(TabMeasure([], time_sig))
            
            # Add note to appropriate measure
            if event.string is not None and event.fret is not None:
                note = TabNote(
                    position=FretPosition(event.string, event.fret),
                    technique=Technique(event.technique) if event.technique else None,
                    beat_in_measure=beat_in_measure,
                    duration=beat_duration
                )
                score.measures[measure_num].notes.append(note)
        
        return score

    def technique_to_tab(self, instruction: GuitarOperation) -> str:
        """Convert a guitar instruction to tab notation"""
        print(f'DEBUG: instop {instruction}')
        fret = str(instruction.fret).rjust(2, '0')
        
        match instruction.technique:
            case Technique.PICK:
                return fret
            case Technique.HAMMER:
                return f"{fret}h"
            case Technique.PULL:
                return f"{fret}p"
            case Technique.BEND:
                bend_amount = instruction.modifier or 1
                return f"{fret}b{bend_amount}"
            case Technique.SLIDE:
                dest = str(int(instruction.modifier or 0)).rjust(2, '0')
                return f"{fret}/{dest}"
            case Technique.TAP:
                return f"t{fret}"
            case Technique.HARMONIC:
                return f"<{fret}>"
            case Technique.PALM_MUTE:
                return f"x{fret}"
            case None:
                return f"{fret}"

    def render_program(self, program: GuitarProgram) -> str:
        """Render the complete program with cycle-accurate timing"""
        compiled = program.compile()
        time_sig = program.time_signature[0]

        if not compiled:
            return "Empty program"
        print(f'c0mp1l3d: {compiled}')    
        events = create_musical_events(program, compiled)

        # Calculate total cycles needed
        max_cycle = max(instr.end_cycle for instr in compiled)
        cycles_per_measure = program.time_signature[0] * program.cycles_per_beat
        total_measures = (max_cycle // cycles_per_measure) + 1
        
        # Initialize the tab grid
        width = cycles_per_measure * total_measures
        tab = [list('-' * width) for _ in range(6)]
        #tab = [[] for _ in range(self.strings)]
        #for s in range(self.strings):
        #    tab[s] = ['-'] * (total_measures * cycles_per_measure)
        
        # Place each instruction
        for timed_inst in compiled:
            inst = timed_inst.operation
            content = self.technique_to_tab(inst)
            for i, char in enumerate(content):
                if timed_inst.start_cycle + i < len(tab[0]):
                    tab[inst.string][timed_inst.start_cycle + i] = char
        
        positions = self._convert_events_to_positions(events, program.tempo, program.time_signature)
        beats_per_measure = time_sig.numerator
        chars_per_beat = 4  * 3 # since frets can be a two-digit num, but what about 32nd notes for example? we need to deal with this.
        total_measures = int(max(p.beat_in_measure / beats_per_measure for p in positions)) + 1
        
        tab_lines = [
            "// Guitar Code Translation",
            f"// Time signature: {time_sig.numerator}/{time_sig.denominator}",
            f"// Tempo: {program.tempo} BPM",
            f"// Tuning: {self.tuning.name}",
            ""
        ]

        # Format into measures
        output = []
        
        # Add timing markers
        timing = "    "
        for m in range(total_measures):
            for b in range(program.time_signature[0]):
                timing += f"{b+1}   "
            timing += "|"
        output.append(timing)
        
        # Add tab lines
        string_lines = [f"{name}|-" for name in self.string_names]
        for measure_group in range(0, total_measures, self.measures_per_line):
            timing_header = ""  # Initial spacing to align with string names

            # Add measures in this group
            for measure in range(measure_group, min(measure_group + self.measures_per_line, total_measures)):
                #measure_content = self._format_measure(measure, positions, beats_per_measure, chars_per_beat)
                measure_content = self._format_measure(measure)
                for i, content in enumerate(measure_content):
                    string_lines[i] += f"{content}|"
            
            tab_lines.extend(string_lines)
            tab_lines.append('')
        
        return '\n'.join(tab_lines)

    def _convert_events_to_positions(self, events: List[MusicalEvent], 
                                   tempo: float, time_sig: TimeSignature) -> List[TabNote]:
        positions = []
        seconds_per_beat = 60.0 / tempo
        
        for event in events:
            if event.string is not None and event.fret is not None:
                positions.append(TabNote(
                    beat_in_measure=event.time / seconds_per_beat,
                    position=tuple[event.string,event.fret],
                    technique=event.technique,
                    duration=event.duration / seconds_per_beat
                ))
        
        return sorted(positions, key=lambda p: p.beat_in_measure)

#        for s in range(self.strings):
#            string_line = f"{self.string_names[s]}|"
#            for m in range(total_measures):
#                start = m * cycles_per_measure
#                end = start + cycles_per_measure
#                string_line += ''.join(tab[s][start:end]) + "|"
#            output.append(string_line)
#        return '\n'.join(output)


# class GuitarTabGenerator:
#     def __init__(self, default_tempo: float = 100.0, default_time_sig: TimeSignature = TimeSignature()):
#         self.default_tempo = default_tempo
#         self.default_time_sig = default_time_sig
#         self.fretboard_mapper = FretboardMapper()
#         self.tab_formatter = TabFormatter()
# 
#     def midi_to_tab(self, midi_path: str, optimize_positions: bool = True, prefer_techniques: bool = True) -> str:
#         events, tempo, time_sig = self._parse_midi(midi_path)
#         guitar_events = self._map_to_guitar(events, optimize_positions, prefer_techniques)
#         return self.tab_formatter.format_events(guitar_events, tempo, time_sig)
#         
#     def _parse_midi(self, midi_path: str) -> Tuple[List[MusicalEvent], float, TimeSignature]:
#         midi_file = mido.MidiFile(midi_path)
#         events = []
#         cumulative_time = {track_idx: 0 for track_idx in range(len(midi_file.tracks))}
#         tempo = self.default_tempo
#         time_sig = self.default_time_sig
#         
#         print("MIDI Note Sequence:")
#         for track_idx, track in enumerate(midi_file.tracks):
#             for msg in track:
#                 cumulative_time[track_idx] += msg.time
#                 
#                 if msg.type == 'set_tempo':
#                     tempo = mido.tempo2bpm(msg.tempo)
#                 elif msg.type == 'time_signature':
#                     time_sig = TimeSignature(msg.numerator, msg.denominator)
#                 elif msg.type == 'note_on' and msg.velocity > 0:
#                     beat_time = cumulative_time[track_idx] / midi_file.ticks_per_beat
#                     print(f"Note On: {msg.note} at beat {beat_time}")
#                     events.append(MusicalEvent(
#                         time=beat_time,
#                         pitch=msg.note,
#                         velocity=msg.velocity,
#                         duration=0
#                     ))
#                 elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
#                     beat_time = cumulative_time[track_idx] / midi_file.ticks_per_beat
#                     for event in reversed(events):
#                         if event.pitch == msg.note and event.duration == 0:
#                             event.duration = beat_time - event.time
#                             break
#         
#         return sorted(events, key=lambda e: e.time), tempo, time_sig
#     
# 
#     def _map_to_guitar(self, events: List[MusicalEvent],
#                       optimize_positions: bool = True,
#                       prefer_techniques: bool = True) -> List[MusicalEvent]:
#         previous_position = None
#         guitar_events = []
#         
#         for event in events:
#             try:
#                 technique = self._determine_technique(event) if prefer_techniques else None
#                 
#                 if optimize_positions:
#                     position = self.fretboard_mapper.find_optimal_position(
#                         pitch=event.pitch,
#                         technique=technique,
#                         previous_position=previous_position
#                     )
#                     print(f"Mapped MIDI note {event.pitch} to position {position}")
#                     event.string = position.string
#                     event.fret = position.fret
#                     event.technique = technique
#                     previous_position = position
#                 else:
#                     pitch = self.fretboard_mapper.normalize_pitch(event.pitch)
#                     positions = self.fretboard_mapper.pitch_to_positions[pitch]
#                     position = next(iter(positions))
#                     print(f"Mapped MIDI note {event.pitch} to position {position}")
#                     event.string = position.string
#                     event.fret = position.fret
#                 
#                 guitar_events.append(event)
#                 
#             except (ValueError, KeyError) as e:
#                 print(f"Warning: Could not map pitch {event.pitch}: {str(e)}")
#                 continue
#         
#         return guitar_events
#     
#     def _determine_technique(self, event: MusicalEvent) -> Optional[str]:
#         if event.velocity > 100:
#             return "hammer-on"
#         elif event.velocity < 50:
#             return "pull-off"
#         elif event.duration > 2.0:
#             return "bend"
#         return "pick"
# 