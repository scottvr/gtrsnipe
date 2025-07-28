from midiutil import MIDIFile # midutil has writeFile method, MIDI's MIDIFile only has parse()
import os
import re
import logging

logger = logging.getLogger(__name__)

def save_text_file(content: str, output_path: str):
    """
    Saves string content to a text file.

    Args:
        content: The string content to save.
        output_path: The path to the file to be created.
    
    Raises:
        IOError: If the file cannot be written to the specified path.
    """
    try:
        directory = os.path.dirname(output_path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        
        with open(output_path, 'w') as f:
            f.write(content)
        logger.info(f"Successfully saved to {output_path}")

    except IOError as e:
        logger.info(f"Error: Could not write to file at {output_path}")
        raise e

def save_midi_file(midi_object: MIDIFile, output_path: str):
    """
    Saves a MIDIFile object to a binary .mid file.

    Args:
        midi_object: The MIDIFile object to save.
        output_path: The path to the .mid file to be created.

    Raises:
        IOError: If the file cannot be written to the specified path.
    """
    try:
        # Ensure the directory exists
        directory = os.path.dirname(output_path)
        if directory:
            os.makedirs(directory, exist_ok=True)

        with open(output_path, 'wb') as output_file:
            midi_object.writeFile(output_file)
        logger.info(f"Successfully saved MIDI file to {output_path}")

    except IOError as e:
        logger.error(f"Error: Could not write MIDI file at {output_path}")
        raise e

def read_text_file(file_path: str) -> str:
    """
    Reads a text file and returns its content with comments and extra whitespace removed.

    Args:
        file_path: The path to the text file.

    Returns:
        A cleaned string of the file's content.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        # Remove comment lines (starting with // or #) and strip whitespace
        cleaned_lines = [line for line in lines if not re.match(r'^\s*(//|#)', line)]
        
        # Join lines and strip leading/trailing whitespace from the whole content
        content = "".join(cleaned_lines).strip()
        
        return content

    except FileNotFoundError:
        logger.error(f"Error: File not found at {file_path}")
        raise
