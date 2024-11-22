# /home/jack/ayyaihome/backend/TTS/phrase_preparation/phrase_segmentation.py

import asyncio
from typing import List, Tuple
from backend.config import Config

async def segment_text(
    working_string: str,
    config: Config
) -> Tuple[str, List[str]]:
    """
    Segments the content based on configuration.

    Args:
        working_string (str): The accumulated content.
        config (Config): Configuration settings.

    Returns:
        Tuple[str, List[str]]: Remaining working_string after processing, and list of phrases.
    """
    phrases = []
    while len(working_string) >= config.MINIMUM_PHRASE_LENGTH:
        delimiter_indices = [
            idx for idx in (
                working_string.find(d, config.MINIMUM_PHRASE_LENGTH) for d in config.DELIMITERS
            ) if idx != -1
        ]
        if not delimiter_indices:
            break
        delimiter_index = min(delimiter_indices)
        # Adjust the index to include the delimiter's length
        delimiter_length = len(next((d for d in config.DELIMITERS if working_string.startswith(d, delimiter_index)), ''))
        phrase = working_string[:delimiter_index + delimiter_length].strip()
        working_string = working_string[delimiter_index + delimiter_length:]
        phrases.append(phrase)
    return working_string, phrases
