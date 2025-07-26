# diff_tool.py
import argparse
from itertools import groupby
from typing import List, Dict

# Assuming the script is placed alongside your project structure
from gtrsnipe.converter import MusicConverter
from .core.types import Song, MusicalEvent

def midi_to_note_name(pitch: int) -> str:
    """Converts a MIDI pitch number to a human-readable note name (e.g., 60 -> C4)."""
    try:
        note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        octave = (pitch // 12) - 1
        note_in_octave = pitch % 12
        return f"{note_names[note_in_octave]}{octave}"
    except IndexError:
        return str(pitch) # Fallback for out-of-range pitches

def group_events_by_char_idx(events: List[MusicalEvent]) -> Dict[float, List[MusicalEvent]]:
    """
    Groups musical events by quantized time to handle chords and timing inaccuracies.
    This uses the same quantization resolution as your mapping and formatting code
    to ensure a fair comparison.
    """
    if not events:
        return {}
    
    # Use the same quantization resolution found in mapper.py and tab.py
    QUANTIZATION_RESOLUTION = 0.125  # Corresponds to a 32nd note
    def quantize_time(beat):
        return round(beat / QUANTIZATION_RESOLUTION) * QUANTIZATION_RESOLUTION
    
    # Sort events primarily by time for grouping
    sorted_events = sorted(events, key=lambda e: e.time)
    
    # Group events that occur at the same quantized time
    grouped_events = {
        time: list(group_iter)
        for time, group_iter in groupby(sorted_events, key=lambda e: quantize_time(e.time))
    }
    return grouped_events

def compare_songs(source_song: Song, generated_song: Song):
    """
    Compares two Song objects and prints a detailed, time-ordered diff of their note events.
    """
    # Assuming single-track comparison as requested
    source_events = source_song.tracks[0].events if source_song.tracks else []
    generated_events = generated_song.tracks[0].events if generated_song.tracks else []
    
    print("\n--- Starting Music Diff ---")
    print(f"Source file has {len(source_events)} note events.")
    print(f"Generated file has {len(generated_events)} note events.")
    print("="*30)

    source_groups = group_events_by_char_idx(source_events)
    generated_groups = group_events_by_char_idx(generated_events)

    # Combine all unique time points from both songs
    all_times = sorted(list(set(source_groups.keys()) | set(generated_groups.keys())))
    
    discrepancies_found = False

    for time in all_times:
        source_notes_at_time = source_groups.get(time, [])
        generated_notes_at_time = generated_groups.get(time, [])

        if not source_notes_at_time:
            # Events exist in generated song but not in the source at this time
            added_pitches = {e.pitch for e in generated_notes_at_time}
            pitch_names = [midi_to_note_name(p) for p in sorted(list(added_pitches))]
            print(f"🔴 Time ~{time:<5.3f}: ADDED notes. Pitches: {pitch_names}")
            discrepancies_found = True
            continue

        if not generated_notes_at_time:
            # Events exist in source song but not in the generated one at this time
            missing_pitches = {e.pitch for e in source_notes_at_time}
            pitch_names = [midi_to_note_name(p) for p in sorted(list(missing_pitches))]
            print(f"🔴 Time ~{time:<5.3f}: MISSING notes. Pitches: {pitch_names}")
            discrepancies_found = True
            continue
        
        # Events exist in both at this time; compare them
        source_pitches = {e.pitch for e in source_notes_at_time}
        generated_pitches = {e.pitch for e in generated_notes_at_time}

        if source_pitches != generated_pitches:
            discrepancies_found = True
            missing = source_pitches - generated_pitches
            added = generated_pitches - source_pitches
            
            if missing:
                pitch_names = [midi_to_note_name(p) for p in sorted(list(missing))]
                print(f"🔴 Time ~{time:<5.3f}: MISSING notes. Pitches: {pitch_names}")
            if added:
                pitch_names = [midi_to_note_name(p) for p in sorted(list(added))]
                print(f"🔴 Time ~{time:<5.3f}: ADDED notes. Pitches: {pitch_names}")
        else:
            # If pitches match, check for significant duration changes
            source_durations = {e.pitch: e.duration for e in source_notes_at_time}
            generated_durations = {e.pitch: e.duration for e in generated_notes_at_time}
            
            for pitch in source_pitches:
                dur_source = source_durations[pitch]
                dur_generated = generated_durations[pitch]
                # A tolerance is needed because of quantization (e.g., in abc.py)
                if abs(dur_source - dur_generated) > 0.1: # 10% of a quarter note
                    discrepancies_found = True
                    note_name = midi_to_note_name(pitch)
                    print(f"🟡 Time ~{time:<5.3f}: MODIFIED duration for {note_name}. Source: {dur_source:.3f}, Generated: {dur_generated:.3f}")
    
    if not discrepancies_found:
        print("\n✅ No significant note discrepancies found between the two files.")
    else:
        print("\n--- Diff Complete ---")


def main():
    parser = argparse.ArgumentParser(
        description="Compares two music files (e.g., a source MIDI and a generated ABC) to find differences in note events."
    )
    parser.add_argument('source_file', help='Path to the original music file (e.g., source.mid)')
    parser.add_argument('generated_file', help='Path to the converted music file (e.g., generated.abc)')
    
    args = parser.parse_args()

    # Determine file formats from extensions
    from_format_source = args.source_file.split('.')[-1]
    from_format_generated = args.generated_file.split('.')[-1]

    print(f"Loading source file: '{args.source_file}' (Format: {from_format_source})")
    print(f"Loading generated file: '{args.generated_file}' (Format: {from_format_generated})")

    converter = MusicConverter()

    try:
        # NOTE: Your converter references parsers for 'vex' and 'tab' that are not included
        # in the provided files. This tool will work for any format with a defined parser.
        source_song = converter._parse(args.source_file, from_format_source)
        generated_song = converter._parse(args.generated_file, from_format_generated)
        
        compare_songs(source_song, generated_song)

    except FileNotFoundError as e:
        print(f"\n*** ERROR: File not found. Please check the path. ***\n{e}")
    except Exception as e:
        print(f"\n*** An unexpected error occurred: {e} ***")

if __name__ == "__main__":
    main()