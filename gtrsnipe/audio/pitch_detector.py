import logging
from pathlib import Path
from basic_pitch.inference import predict_and_save
from basic_pitch import ICASSP_2022_MODEL_PATH

# Add a standard, plain-text handler
bp_logger = logging.getLogger("basic-pitch")
# Remove its fancy emoji-printing handlers
bp_logger.handlers = []
bp_logger.addHandler(logging.StreamHandler())
bp_logger.setLevel(logging.INFO)

logger = logging.getLogger(__name__)

def transcribe_to_midi(audio_file: str, 
                       overwrite: bool = False, 
                       min_freq: float | None = None, 
                       max_freq: float | None = None,
                       melodia_trick: bool = False,
                       onset_threshold: float = 0.5,
                       frame_threshold: float = 0.3,
                       min_note_len_ms: float = 127.70,
                       ) -> str:
    """
    Transcribes an audio file to MIDI using Basic-Pitch.

    Args:
        audio_file: Path to the input audio file.
        overwrite: If True, will overwrite existing MIDI files.
        min_freq: The minimum frequency (in Hz) to detect.
        max_freq: The maximum frequency (in Hz) to detect.

    Returns:
        The file path to the generated .mid file.
    """
    logger.info("[PIPELINE] Step 3: Transcribing audio to MIDI with Basic-Pitch...")
    logger.info("This may take a moment...")

    p = Path(audio_file)
    output_path = p.with_name(f"{p.stem}_basic_pitch.mid")

    if melodia_trick:
        logger.info("--- Using melodia_trick ---")
    
    if not output_path.exists() or overwrite:
        if output_path.exists() and overwrite:
            logger.info(f"Overwrite enabled. Removing existing intermediate file: {output_path}")
            output_path.unlink()

        predict_and_save(
            audio_path_list=[audio_file],
            model_or_model_path=ICASSP_2022_MODEL_PATH,
            output_directory=str(output_path.parent),
            save_midi=True,
            sonify_midi=False,
            save_model_outputs=False,
            save_notes=False,
            minimum_frequency=min_freq,
            maximum_frequency=max_freq,
            onset_threshold=onset_threshold,
            frame_threshold=frame_threshold,
            minimum_note_length=(min_note_len_ms / 1000),
            melodia_trick = melodia_trick
        )

        logger.info(f"--- MIDI transcription successfully generated: {output_path} ---")
    else:
        logger.info(f"--- MIDI file already exists, skipping transcription: {output_path} ---")

    return str(output_path)