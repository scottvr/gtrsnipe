import librosa
import numpy as np
import logging
from pathlib import Path
from ..core.types import Song, Track, MusicalEvent
from ..formats.mid import MidiGenerator
from ..utils.io import save_midi_file
from .tempo_detector import estimate_tempo

logger = logging.getLogger(__name__)

def transcribe_to_midi_with_lr(audio_file: str, final_output_path: str, fmin_hz: float | None, fmax_hz: float | None) -> str:
    """
    Creates a simple, monophonic MIDI file from an audio file using librosa,
    constrained by the provided frequency range.
    """
    logger.info("--- Detecting pitch with simple engine (librosa/pYIN)... ---")
    
    # Use provided frequency constraints, or fall back to a safe default for bass.
    fmin = fmin_hz if fmin_hz is not None else librosa.note_to_hz('E1')
    fmax = fmax_hz if fmax_hz is not None else librosa.note_to_hz('G4')
    logger.info(f"Using frequency range: {fmin:.2f} Hz to {fmax:.2f} Hz.")

    y, sr = librosa.load(audio_file)

    # 1. Get pitch (f0) and voicing information using the provided frequency range
    f0, voiced_flag, voiced_probs = librosa.pyin(y, fmin=float(fmin), fmax=float(fmax))    
    # 2. Detect note onset times
    onset_frames = librosa.onset.onset_detect(y=y, sr=sr, units='frames')
    #onset_times = librosa.frames_to_time(onset_frames, sr=sr)
    
    # 3. Estimate loudness (RMS energy) to approximate velocity
    rms = librosa.feature.rms(y=y)[0]
    
    events = []
    if len(onset_frames) > 0:
        for i in range(len(onset_frames) - 1):
            start_frame = onset_frames[i]
            end_frame = onset_frames[i+1]
            
            # Get the pitch for this note segment
            note_f0_segment = f0[start_frame:end_frame]
            note_f0_segment = note_f0_segment[~np.isnan(note_f0_segment)] # Remove unvoiced frames
            
            if len(note_f0_segment) > 0:
                # Use the median frequency as the note's pitch
                pitch_hz = np.median(note_f0_segment)
                midi_note = librosa.hz_to_midi(pitch_hz)
                
                # Calculate timing
                start_time = librosa.frames_to_time(start_frame, sr=sr)
                duration = librosa.frames_to_time(end_frame - start_frame, sr=sr)

                # Estimate velocity from the max RMS in the segment
                note_rms = rms[start_frame:end_frame]
                velocity = int(np.max(note_rms) * 127) + 40
                velocity = max(0, min(127, velocity)) # Clamp to valid MIDI range

                events.append(
                    MusicalEvent(time=start_time, pitch=int(round(midi_note)), 
                                 duration=duration, velocity=velocity)
                )
    estimated_tempo = estimate_tempo(audio_file)
    
    track = Track(events=events, instrument_name="Synth Bass 1")
    song = Song(tracks=[track], tempo=estimated_tempo, time_signature="4/4") 

    p = Path(audio_file)
    output_path = Path(final_output_path)
    
    midi_data = MidiGenerator.generate(song)
    save_midi_file(midi_data, str(output_path))
    
    logger.info(f"--- Librosa MIDI transcription generated: {output_path} ---")
    return str(output_path)