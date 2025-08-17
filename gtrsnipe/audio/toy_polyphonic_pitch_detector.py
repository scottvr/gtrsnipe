import librosa
import numpy as np

from scipy.io.wavfile import write
sr = 22050; T = 5.0
t = np.linspace(0, T, int(T*sr), endpoint=False)
C4 = 261.63 * 2 * np.pi * t
E4 = 329.63 * 2 * np.pi * t
G4 = 392.00 * 2 * np.pi * t
chord = 0.5 * (np.sin(C4) + np.sin(E4) + np.sin(G4))
write('c_major_chord.wav', sr, chord.astype(np.float32))

def detect_prominent_notes(
    audio_path: str, 
    max_polyphony: int = 3, 
    interval_seconds: float = 0.5
) -> None:
    """
    Analyzes an audio file to detect the most prominent musical notes in intervals.

    This is a conceptual demonstration of using a chromagram for polyphonic
    analysis and is not a full-fledged transcription tool.

    Args:
        audio_path: Path to the audio file (wav, mp3, etc.).
        max_polyphony: The maximum number of notes to identify at any given time.
        interval_seconds: How often to report the detected notes (in seconds).
    """
    print(f"--- Analyzing '{audio_path}' ---")
    
    try:
        # 1. Load the audio file
        y, sr = librosa.load(audio_path)

        # 2. Separate harmonics from percussives. This can help clean up the signal
        # by focusing on the tonal components of the audio.
        y_harmonic, y_percussive = librosa.effects.hpss(y)

        # 3. Compute the chromagram from the harmonic component. This is our
        # "harmonic stacking" that groups octaves together.
        # The result is an array where rows are notes (C, C#, D...) and
        # columns are time frames.
        chromagram = librosa.feature.chroma_stft(y=y_harmonic, sr=sr)
        
        # Define the 12 note names
        note_names = ['C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B']

        # Calculate how many columns in the chromagram correspond to our interval
        frames_per_interval = int(librosa.time_to_frames(interval_seconds, sr=sr))

        # 4. Iterate through the audio in intervals and find the strongest notes
        for i in range(0, chromagram.shape[1], frames_per_interval):
            # Get the current slice of the chromagram
            interval_slice = chromagram[:, i:i + frames_per_interval]
            
            # Calculate the average energy for each note over this interval
            average_energy = np.mean(interval_slice, axis=1)
            
            # 5. Find the indices of the top 'n' notes (our heuristic)
            # We use argpartition for efficiency, as it finds the k-th largest
            # element without fully sorting the entire array.
            strongest_note_indices = np.argpartition(
                average_energy, -max_polyphony
            )[-max_polyphony:]
            
            # Filter out notes with very low average energy to avoid reporting noise
            strongest_notes = [
                note_names[idx] for idx in strongest_note_indices 
                if average_energy[idx] > 0.1  # Energy threshold heuristic
            ]

            # Sort the notes for consistent display
            strongest_notes.sort()
            
            current_time = librosa.frames_to_time(i, sr=sr)
            
            if strongest_notes:
                print(f"Time {current_time:.2f}s: Prominent notes are {', '.join(strongest_notes)}")

    except Exception as e:
        print(f"An error occurred: {e}")

detect_prominent_notes('c_major_chord.wav', max_polyphony=3)