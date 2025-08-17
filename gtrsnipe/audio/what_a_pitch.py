import librosa
import mido
import numpy as np
from collections import defaultdict

# Define your input files
AUDIO_FILE = 'guitar.wav'
MIDI_INPUT_FILE = 'guitar_basic_pitch.mid'
MIDI_OUTPUT_FILE = 'guitar_cleaned_output.mid'

# Load the audio file
print("Loading audio...")
y, sr = librosa.load(AUDIO_FILE)

# Separate the harmonic component to focus on tonal content
print("Separating harmonic content...")
y_harmonic, _ = librosa.effects.hpss(y)

# Compute the chromagram for the entire audio
print("Computing chromagram...")
chromagram = librosa.feature.chroma_stft(y=y_harmonic, sr=sr)

# A list to hold our cleaned-up notes
# Each note will be a dictionary: {'note': pitch, 'velocity': vel, 'time': start, 'duration': dur}
clean_notes = []

# Load the messy MIDI file
midi = mido.MidiFile(MIDI_INPUT_FILE)
ticks_per_beat = midi.ticks_per_beat
tempo = 500000  # Default tempo (120 bpm) in microseconds per beat

# A dictionary to track active notes
# Key = MIDI pitch, Value = [start_time_in_seconds, velocity]
active_notes = defaultdict(list)
current_time_seconds = 0

print("Parsing input MIDI with robust note tracking...")
for msg in midi:
    current_time_seconds += mido.tick2second(msg.time, ticks_per_beat, tempo)
    if msg.type == 'set_tempo': tempo = msg.tempo
    elif msg.type == 'note_on' and msg.velocity > 0:
        # Append the new note_on event; don't overwrite
        active_notes[msg.note].append([current_time_seconds, msg.velocity])
    elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
        # If a note_off arrives, process the OLDEST note_on for that pitch (FIFO)
        if msg.note in active_notes and active_notes[msg.note]:
            start_time, velocity = active_notes[msg.note].pop(0)
            duration = current_time_seconds - start_time
            if duration > 0.02:
                clean_notes.append({'note': msg.note, 'velocity': velocity, 'time': start_time, 'duration': duration})

print(f"Found {len(clean_notes)} potential notes after initial duration filter.")



# Group notes by start time using a time window
# Key = quantized time, Value = list of notes in that window
time_window = 0.1 # Group notes within 100ms of each other
note_groups = defaultdict(list)
for note in clean_notes:
    quantized_time = round(note['time'] / time_window)
    note_groups[quantized_time].append(note)

# This will be our final, fully cleaned list of notes
final_notes = []
note_names = ['C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B']

print("Applying adaptive spectral filter to note groups...")
for time_group in note_groups.values():
    if not time_group: continue

    group_time = sum(n['time'] for n in time_group) / len(time_group)
    chroma_frame_index = librosa.time_to_frames(group_time, sr=sr)
    if chroma_frame_index >= chromagram.shape[1]: continue
    
    spectral_profile = chromagram[:, chroma_frame_index]
    
    # --- ADAPTIVE THRESHOLD LOGIC ---
    peak_energy_in_frame = np.max(spectral_profile)
    
    # Set a minimum floor to avoid silence being processed
    if peak_energy_in_frame < 0.1: continue 
    
    # Our new threshold is relative to the peak energy in this specific moment
    energy_threshold = peak_energy_in_frame * 0.5 # e.g., keep notes that are >= 50% of the peak
    
    kept_notes = []
    for note in time_group:
        pitch_class = note['note'] % 12
        energy = spectral_profile[pitch_class]
        
        if energy >= energy_threshold:
            note['energy'] = energy
            kept_notes.append(note)

    # (The rest of the logic with MAX_POLYPHONY remains the same)
    MAX_POLYPHONY = 6 
    if len(kept_notes) > MAX_POLYPHONY:
        kept_notes.sort(key=lambda x: x['energy'], reverse=True)
        final_notes.extend(kept_notes[:MAX_POLYPHONY])
    else:
        final_notes.extend(kept_notes)

print("Generating clean MIDI file...")
# Sort final notes by start time to build the new track
final_notes.sort(key=lambda x: x['time'])

mid_new = mido.MidiFile(ticks_per_beat=ticks_per_beat)
track = mido.MidiTrack()
mid_new.tracks.append(track)

# We need to add note_off events too and sort all events by time
events_to_write = []
for note in final_notes:
    events_to_write.append({'type': 'note_on', 'note': note['note'], 'velocity': note['velocity'], 'time': note['time']})
    events_to_write.append({'type': 'note_off', 'note': note['note'], 'velocity': 0, 'time': note['time'] + note['duration']})

events_to_write.sort(key=lambda x: x['time'])

# Convert absolute times to delta ticks for Mido
last_time_seconds = 0
for event in events_to_write:
    delta_seconds = event['time'] - last_time_seconds
    delta_ticks = int(mido.second2tick(delta_seconds, ticks_per_beat, tempo))
    track.append(mido.Message(event['type'], note=event['note'], velocity=event['velocity'], time=delta_ticks))
    last_time_seconds = event['time']

mid_new.save(MIDI_OUTPUT_FILE)
print(f"Done! Cleaned MIDI saved to {MIDI_OUTPUT_FILE}")
