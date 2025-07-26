import logging
import sys

def setup_logger(level=logging.INFO):
    logger = logging.getLogger()
    
    if logger.hasHandlers():
        logger.handlers.clear()

    logger.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    # Create a formatter for the log messages
    # In debug mode, we'll show more info (module name, line number)
    if level == logging.DEBUG:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)'
        )
    else:
        # A simpler format for normal (INFO) output
        formatter = logging.Formatter('%(message)s')

    handler.setFormatter(formatter)
    logger.addHandler(handler)