# utils.py

import re
from config import Config

def find_next_phrase_end(text: str, config: Config) -> int:
    """
    Finds the end position of the next phrase based on delimiters using regex.

    Args:
        text (str): The text to search within.
        config (Config): Configuration instance.

    Returns:
        int: The index of the delimiter if found after the minimum phrase length; otherwise, -1.
    """
    match = config.DELIMITER_PATTERN.search(text, pos=config.MINIMUM_PHRASE_LENGTH)
    return match.start() if match else -1
