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
    logger.info(f"[PIPELINE] Applying low-pass filter with cutoff at {cutoff_hz:.2f} Hz...")
    y, sr_loaded = librosa.load(audio_file, sr=sr)

    # Design a Butterworth low-pass filter
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
    logger.info("[PIPELINE] Step 2: Cleaning audio stem with NoiseReduce...")
    logger.info("Loading audio file...")

    try:
        # 1. Load the audio file using librosa.
        # This handles different file formats and gives us the audio data as a
        # NumPy array (y) and the sample rate (sr).
        y, sr = librosa.load(audio_file)

        logger.info("Performing noise/reverb reduction...")
        # 2. Perform noise reduction.
        # The noisereduce library is effective at reducing reverb and other
        # non-stationary noise. For highly reverberant tracks, the parameters
        # could be fine-tuned, but the defaults are a great start.
        reduced_noise_y = nr.reduce_noise(y=y, sr=sr, stationary=False)

        # 3. Save the cleaned audio to a new file.
        p = Path(audio_file)
        # e.g., '.../song_guitar.wav' -> '.../song_guitar_clean.wav'
        output_path = p.with_name(f"{p.stem}_clean{p.suffix}")
        
        logger.info(f"Saving cleaned audio to {output_path}...")
        sf.write(str(output_path), reduced_noise_y, sr)

        logger.info(f"--- Cleaned audio successfully generated: {output_path} ---")
        return str(output_path)

    except Exception as e:
        logger.error(f"Failed during audio cleanup: {e}")
        # Return the original file path to allow the pipeline to continue if desired
        return audio_file