# /home/jack/ayyaihome/backend/TTS/phrase_preparation/phrase_segmentation.py

import asyncio
from typing import Callable
from backend.config import Config

async def segment_and_dispatch_phrases(
    working_string: str,
    content: str,
    dispatch_function: Callable[[str, asyncio.Queue], asyncio.Future],
    phrase_queue: asyncio.Queue,
    config: Config
) -> str:
    """
    Segments phrases from the accumulated content and dispatches them using the provided dispatch function.

    Args:
        working_string (str): The current accumulated content.
        content (str): The new content chunk to add.
        dispatch_function (Callable): Function to dispatch segmented phrases.
        phrase_queue (asyncio.Queue): The queue to dispatch phrases to.
        config (Config): Configuration settings.

    Returns:
        str: The updated working_string after processing.
    """
    working_string += content
    while len(working_string) >= config.MINIMUM_PHRASE_LENGTH:
        delimiter_index = next(
            (working_string.find(d, config.MINIMUM_PHRASE_LENGTH) for d in config.DELIMITERS
             if working_string.find(d, config.MINIMUM_PHRASE_LENGTH) != -1),
            -1
        )
        if delimiter_index == -1:
            break
        phrase = working_string[:delimiter_index + 1].strip()
        working_string = working_string[delimiter_index + 1:]
        await dispatch_function(phrase, phrase_queue)
    return working_string
