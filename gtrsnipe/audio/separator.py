import logging
from pathlib import Path
from demucs.separate import main as demucs_run

logger = logging.getLogger(__name__)

def separate_instrument(audio_file: str, instrument: str = "guitar", model_name: str = "htdemucs") -> str:
    """
    Separates a specific instrument stem from an audio file using Demucs.

    Args:
        audio_file: Path to the input audio file.
        instrument: The instrument to isolate. For Demucs's default model,
                    'guitar' is in the 'other' stem.

    Returns:
        The file path to the generated instrument stem.
    """
    # The default 4-stem model in Demucs is 'htdemucs', which separates
    # audio into 'bass', 'drums', 'vocals', and 'other'. Guitars, pianos,
    # and other melodic instruments are typically in the 'other' stem.
    # We map our "guitar" input to "other" for demucs.
    target_stem = "other" if instrument == "guitar" and model_name not in 'htdemucs_6s' else instrument
    
    logger.info(f"[PIPELINE] Step 1: Isolating '{target_stem}' stem with Demucs...")
    logger.info("This may take a moment depending on the file size and your hardware...")

    # Define the output directory for separated files
    output_dir = Path("./separated")
    
    # Demucs's main function can be called like a command-line script.
    # We build the list of arguments programmatically.
    # '-n htdemucs' specifies the default model.
    # '--two-stems' tells it to save only the target stem and its inverse.
    # '-o' specifies the output directory.
    demucs_args = [
        "--two-stems", target_stem,
        "-n", model_name,
        "-o", str(output_dir),
        audio_file,
    ]

    # Run the separation process
    demucs_run(demucs_args)

    # Determine the output file path based on Demucs's naming convention
    input_path = Path(audio_file)
    # e.g., separated/htdemucs/song_name/other.wav
    expected_output = output_dir / model_name / input_path.stem / f"{target_stem}.wav"

    if not expected_output.exists():
        raise FileNotFoundError(f"Demucs did not produce the expected output file: {expected_output}")

    logger.info(f"--- Demucs stem successfully generated: {expected_output} ---")
    
    return str(expected_output)