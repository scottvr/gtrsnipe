import logging
from pathlib import Path
import librosa
import noisereduce as nr
import soundfile as sf
import scipy

logger = logging.getLogger(__name__)

def apply_low_pass_filter(audio_file: str, cutoff_hz: float, sr: int) -> str:
    """
    Applies a low-pass filter to an audio file.

    Args:
        audio_file: Path to the input audio.
        cutoff_hz: The cutoff frequency for the filter in Hz.
        sr: The sample rate of the audio.

    Returns:
        The file path to the filtered audio file.
    """
    logger.info(f"Applying low-pass filter with cutoff at {cutoff_hz:.2f} Hz...")
    y, sr_loaded = librosa.load(audio_file, sr=sr)

    # Butterworth low-pass filter
    # The cutoff frequency is normalized to the Nyquist frequency (sr / 2)
    nyquist = 0.5 * sr
    normal_cutoff = cutoff_hz / nyquist
    b, a = scipy.signal.butter(4, normal_cutoff, btype='low', analog=False)

    # Apply the filter
    filtered_y = scipy.signal.lfilter(b, a, y)

    # Save the filtered audio
    p = Path(audio_file)
    output_path = p.with_name(f"{p.stem}_lpf{p.suffix}")
    sf.write(str(output_path), filtered_y, sr)
    
    logger.info(f"--- Low-pass filtered audio saved: {output_path} ---")
    return str(output_path)




def cleanup_audio(audio_file: str) -> str:
    """
    Reduces noise and reverb from an audio file using the noisereduce library.

    Args:
        audio_file: Path to the input audio file (e.g., the stem from Demucs).

    Returns:
        The file path to the cleaned audio file.
    """
    logger.info("Cleaning audio stem with NoiseReduce...")
    logger.info("Loading audio file...")

    try:
        y, sr = librosa.load(audio_file)

        logger.info("Performing noise/reverb reduction...")
        reduced_noise_y = nr.reduce_noise(y=y, sr=sr, stationary=False)

        p = Path(audio_file)
        output_path = p.with_name(f"{p.stem}_clean{p.suffix}")
        
        logger.info(f"Saving cleaned audio to {output_path}...")
        sf.write(str(output_path), reduced_noise_y, sr)

        logger.info(f"--- Cleaned audio successfully generated: {output_path} ---")
        return str(output_path)

    except Exception as e:
        logger.error(f"Failed during audio cleanup: {e}")
        # Return the original file path to allow the pipeline to continue 
        return audio_file