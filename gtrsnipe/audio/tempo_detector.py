import librosa
import logging

logger = logging.getLogger(__name__)

def estimate_tempo(audio_file: str, sr: int | None = 22050) -> float:
    """
    Estimates the tempo of an audio file in Beats Per Minute (BPM).

    Args:
        audio_file: Path to the input audio file.
        sr: The sample rate to use for analysis.

    Returns:
        The estimated tempo as a float.
    """
    logger.info("--- Estimating tempo... ---")
    
    # Load the audio file
    y, sr = librosa.load(audio_file, sr=sr)
    
    # Use librosa's beat tracking function to estimate the tempo
    # It returns an array, but we typically just need the first estimate.
    tempo_estimate = round(librosa.beat.tempo(y=y, sr=sr)[0], 3)
    
    logger.info(f"Estimated tempo: {tempo_estimate:.3f} BPM")
    return float(tempo_estimate)