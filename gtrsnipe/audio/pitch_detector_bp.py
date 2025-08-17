import logging
from pathlib import Path
from basic_pitch.inference import predict
from basic_pitch import ICASSP_2022_MODEL_PATH

# Add a standard, plain-text handler
bp_logger = logging.getLogger("basic-pitch")
# Remove its fancy emoji-printing handlers
bp_logger.handlers = []
bp_logger.addHandler(logging.StreamHandler())
bp_logger.setLevel(logging.INFO)

logger = logging.getLogger(__name__)

def transcribe_to_midi_with_bp(audio_file: str, 
                        final_output_path: str,
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
    logger.info("Transcribing audio to MIDI with Basic-Pitch...")
    logger.info("This may take a moment...")

    output_path = Path(final_output_path)
    if not output_path.exists() or overwrite:
        logger.info(f"Predicting MIDI for {audio_file}...")

        model_output, midi_data, note_events = predict(
            audio_path=audio_file,
            model_or_model_path=ICASSP_2022_MODEL_PATH,
            onset_threshold=onset_threshold,
            frame_threshold=frame_threshold,
            minimum_frequency=min_freq,
            maximum_frequency=max_freq,
            minimum_note_length=(min_note_len_ms / 1000),
            multiple_pitch_bends=melodia_trick
        )
        
        # --- Use our own reliable file-saving function ---
        if overwrite and output_path.exists():
            logger.info(f"Overwrite enabled. Removing existing file: {output_path}")
            output_path.unlink()
            
        # The midi_data object from basic-pitch can be written directly to a file
        midi_data.write(str(output_path))

        logger.info(f"--- MIDI transcription successfully generated: {output_path} ---")
    else:
        logger.info(f"--- MIDI file already exists, skipping transcription: {output_path} ---")

    return str(output_path)