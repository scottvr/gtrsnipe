import numpy as np
from ..core.types import TempoEvent
import logging

logger = logging.getLogger(__name__)

def analyze_dynamic_tempo(beat_times: np.ndarray, time_signature: str = "4/4") -> list[TempoEvent]:
    """
    Analyzes beat timestamps to find per-measure tempo changes.

    Args:
        beat_times: An array of timestamps for each detected beat.
        time_signature: The time signature of the song (e.g., "4/4").

    Returns:
        A list of TempoEvent objects indicating where the tempo changes.
    """
    try:
        beats_per_measure = int(time_signature.split('/')[0])
    except (ValueError, IndexError):
        beats_per_measure = 4 # Default to 4 if parsing fails

    tempo_events = []
    last_bpm = 0.0

    # Iterate through the beats, measure by measure
    for i in range(0, len(beat_times) - beats_per_measure, beats_per_measure):
        measure_start_beat = i
        measure_end_beat = i + beats_per_measure
        
        # Get the timestamps for the beats in the current measure
        measure_beat_times = beat_times[measure_start_beat : measure_end_beat + 1]
        
        # Calculate the average duration of a beat in this measure
        beat_durations = np.diff(measure_beat_times)
        if not beat_durations.any():
            continue
            
        avg_beat_duration = np.mean(beat_durations)
        
        # Convert the beat duration to BPM
        current_bpm = round(60.0 / avg_beat_duration, 2)
        
        # If the tempo has changed significantly from the last measure, create an event
        # Use a tolerance to avoid creating unnecessary events for minor fluctuations
        if abs(current_bpm - last_bpm) > 1.0:
            tempo_events.append(TempoEvent(time=float(measure_start_beat), bpm=current_bpm))
            last_bpm = current_bpm
            
    logger.info(f"--- Detected {len(tempo_events)} significant tempo changes. ---")
    return tempo_events