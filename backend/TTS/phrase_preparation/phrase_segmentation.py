# backend/TTS/phrase_preparation/phrase_segmentation.py

import re
from typing import Tuple, List
from backend.config import Config

async def segment_text(text: str, config: Config) -> Tuple[str, List[str]]:
    """
    Segments the text based on delimiters.

    Args:
        text (str): The text to segment.
        config (Config): Configuration object.

    Returns:
        Tuple[str, List[str]]: Remaining text and list of segmented phrases.
    """
    delimiters = config.DELIMITERS
    pattern = '|'.join(map(re.escape, delimiters))
    segments = re.split(f'({pattern})', text)

    phrases = []
    current_phrase = ''

    for segment in segments:
        if segment in delimiters:
            current_phrase += segment
            phrases.append(current_phrase.strip())
            current_phrase = ''
        else:
            current_phrase += segment

    # At this point, any remaining text in current_phrase does not end with a delimiter
    return current_phrase, phrases
