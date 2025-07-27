import argparse
from itertools import groupby
from typing import List, Dict

from ..converter import MusicConverter
from ..formats import abc, mid, tab, vex
from ..core.types import Song, MusicalEvent

def midi_to_note_name(pitch: int) -> str:
    """Converts a MIDI pitch number to a human-readable note name (e.g., 60 -> C4)."""
    try:
        note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        octave = (pitch // 12) - 1
        note_in_octave = pitch % 12
        return f"{note_names[note_in_octave]}{octave}"
    except IndexError:
        return str(pitch)

def group_events_by_char_idx(events: List[MusicalEvent]) -> Dict[float, List[MusicalEvent]]:
    """Groups musical events by quantized time."""
    if not events:
        return {}
    QUANTIZATION_RESOLUTION = 0.125
    def quantize_time(beat):
        return round(beat / QUANTIZATION_RESOLUTION) * QUANTIZATION_RESOLUTION
    sorted_events = sorted(events, key=lambda e: e.time)
    grouped_events = {
        time: list(group_iter)
        for time, group_iter in groupby(sorted_events, key=lambda e: quantize_time(e.time))
    }
    return grouped_events

def compare_songs(source_song: Song, generated_song: Song):
    """Compares two Song objects and prints a detailed diff."""
    source_events = source_song.tracks[0].events if source_song.tracks else []
    generated_events = generated_song.tracks[0].events if generated_song.tracks else []
    
    print("\n--- Starting Music Diff ---")
    print(f"Source song has {len(source_events)} note events.")
    print(f"Roundtrip song has {len(generated_events)} note events.")
    print("="*30)

    source_groups = group_events_by_char_idx(source_events)
    generated_groups = group_events_by_char_idx(generated_events)
    all_times = sorted(list(set(source_groups.keys()) | set(generated_groups.keys())))
    
    discrepancies_found = False
    for time in all_times:
        source_notes_at_time = source_groups.get(time, [])
        generated_notes_at_time = generated_groups.get(time, [])
        if not source_notes_at_time:
            added_pitches = {e.pitch for e in generated_notes_at_time}
            pitch_names = [midi_to_note_name(p) for p in sorted(list(added_pitches))]
            print(f"🔴 Time ~{time:<5.3f}: ADDED notes. Pitches: {pitch_names}")
            discrepancies_found = True
            continue
        if not generated_notes_at_time:
            missing_pitches = {e.pitch for e in source_notes_at_time}
            pitch_names = [midi_to_note_name(p) for p in sorted(list(missing_pitches))]
            print(f"🔴 Time ~{time:<5.3f}: MISSING notes. Pitches: {pitch_names}")
            discrepancies_found = True
            continue
        source_pitches = {e.pitch for e in source_notes_at_time}
        generated_pitches = {e.pitch for e in generated_notes_at_time}
        if source_pitches != generated_pitches:
            discrepancies_found = True
            missing = sorted(list(source_pitches - generated_pitches))
            added = sorted(list(generated_pitches - source_pitches))
            if missing:
                print(f"🔴 Time ~{time:<5.3f}: MISSING notes. Pitches: {[midi_to_note_name(p) for p in missing]}")
            if added:
                print(f"🔴 Time ~{time:<5.3f}: ADDED notes. Pitches: {[midi_to_note_name(p) for p in added]}")
    
    if not discrepancies_found:
        print("\n✅ No significant note discrepancies found in the roundtrip test.")
    else:
        print("\n--- Diff Complete ---")

def main():
    parser = argparse.ArgumentParser(
        description="Debugs a generator/parser pair by performing an in-memory roundtrip test from a source MIDI file."
    )
    parser.add_argument('input_file', help='Path to the source MIDI file to test.')
    parser.add_argument(
        '--format',
        type=str,
        default='abc',
        choices=['abc'], # Add 'vex', 'tab' here when ready
        help='The format to test (e.g., abc).'
    )
    args = parser.parse_args()

    print(f"Loading source MIDI: '{args.input_file}'")
    
    # Use your existing MIDI parser to create the initial Song object
    source_song = gtrsnipe.converter.MusicConverter()._parse(args.input_file, 'mid')

    roundtrip_song = Song()
    if args.format == 'abc':
        print("--- 1. Generating ABC content in-memory...")
        generated_abc_string = AbcGenerator.generate(source_song)
        
        # Optional: Print the first few hundred characters of the generated string for a quick sanity check
        print("--- Generated ABC (first 200 chars):")
        print(generated_abc_string[:200].strip())
        print("-" * 20)

        print("\n--- 2. Parsing generated ABC content back into a Song object...")
        roundtrip_song = AbcParser.parse(generated_abc_string)

    # Add other formats here if needed
    # elif args.format == 'vex':
    #     generated_vex_string = VextabGenerator.generate(source_song)
    #     roundtrip_song = VextabParser.parse(generated_vex_string)

    print("\n--- 3. Comparing source song with the in-memory roundtrip song ---")
    compare_songs(source_song, roundtrip_song)

if __name__ == "__main__":
    main()