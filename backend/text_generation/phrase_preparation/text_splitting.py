# backend/text_generation/phrase_preparation/text_splitting.py

import asyncio
import logging

logger = logging.getLogger(__name__)

async def process_text(working_string: str, phrase_queue: asyncio.Queue, settings: dict):
    """
    Splits text based on a unified list of delimiters.

    Args:
        working_string (str): The text to process.
        phrase_queue (asyncio.Queue): Queue to store processed phrases.
        settings (dict): Configuration for splitting behavior.
    """
    # Check if text splitting is enabled
    if not settings.get("USE_TEXT_SPLITTING", False):
        await phrase_queue.put(working_string.strip())
        logger.debug("Text splitting is disabled. Passing entire text without splitting.")
        return

    delimiters = settings.get("DELIMITERS", {})
    logger.debug(f"Loaded delimiters: {delimiters}")

    while working_string:
        delimiter_index = -1
        selected_delimiter = None

        for delimiter, config in delimiters.items():
            if not config.get("enabled", False):
                continue

            index = working_string.find(delimiter)
            if index != -1 and (delimiter_index == -1 or index < delimiter_index):
                delimiter_index = index + len(delimiter)
                selected_delimiter = delimiter

        if delimiter_index != -1 and selected_delimiter:
            chunk = working_string[:delimiter_index].strip()
            working_string = working_string[delimiter_index:]
            logger.debug(f"Chunk extracted using delimiter '{selected_delimiter}': {chunk}")
            await phrase_queue.put(chunk)

            pause_time = delimiters[selected_delimiter].get("pause_time", 0)
            if pause_time:
                logger.debug(f"Pausing for {pause_time} ms")
                await asyncio.sleep(pause_time / 1000)
        else:
            break

    if working_string.strip():
        logger.debug(f"Final chunk without delimiter: {working_string.strip()}")
        await phrase_queue.put(working_string.strip())
