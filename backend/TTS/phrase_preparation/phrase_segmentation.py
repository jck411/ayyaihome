# /path/to/your/project/utilities.py

import asyncio
from typing import Any, List
from backend.config import Config

async def segment_and_dispatch_phrases(
    working_string: str,
    content: str,
    phrase_queue: asyncio.Queue,
    config: Config
) -> str:
    """
    Segments phrases from the accumulated content and dispatches them to the phrase_queue.

    Args:
        working_string (str): The current accumulated content.
        content (str): The new content chunk to add.
        phrase_queue (asyncio.Queue): The queue to dispatch phrases to.
        config (Config): Configuration settings.

    Returns:
        str: The updated working_string after processing.
    """
    working_string += content
    while len(working_string) >= config.MINIMUM_PHRASE_LENGTH:
        delimiter_index = next(
            (working_string.find(d, config.MINIMUM_PHRASE_LENGTH) for d in config.DELIMITERS
             if working_string.find(d, config.MINIMUM_PHRASE_LENGTH) != -1), -1)
        if delimiter_index == -1:
            break
        phrase = working_string[:delimiter_index + 1].strip()
        working_string = working_string[delimiter_index + 1:]
        await phrase_queue.put(phrase)
    return working_string
