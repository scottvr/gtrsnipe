import librosa
import logging

logger = logging.getLogger(__name__)


def librosa_tempo(y, sr):
    """Return librosa's tempo estimate, across librosa API relocations.

    The tempo estimator moved: ``librosa.beat.tempo`` (<=0.9) ->
    ``librosa.feature.tempo`` (0.10) -> ``librosa.feature.rhythm.tempo`` (1.x).
    Try newest-to-oldest so we work on whatever is installed (this repo is
    tested against 1.0.0). Returns the array librosa returns (index [0] for the
    scalar estimate).
    """
    feature = getattr(librosa, "feature", None)
    rhythm = getattr(feature, "rhythm", None) if feature else None
    candidates = [
        getattr(rhythm, "tempo", None) if rhythm else None,
        getattr(feature, "tempo", None) if feature else None,
        getattr(getattr(librosa, "beat", None), "tempo", None),
    ]
    for fn in candidates:
        if fn is not None:
            return fn(y=y, sr=sr)
    raise AttributeError(
        "librosa exposes no tempo estimator "
        "(checked feature.rhythm.tempo, feature.tempo, beat.tempo)")


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
    tempo_estimate = round(librosa_tempo(y, sr)[0], 3)
    
    logger.info(f"Estimated tempo: {tempo_estimate:.3f} BPM")
    return float(tempo_estimate)