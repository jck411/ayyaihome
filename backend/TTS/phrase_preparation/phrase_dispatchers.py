# /home/jack/ayyaihome/backend/TTS/phrase_preparation/phrase_dispatchers.py

import asyncio
from backend.config import Config
from backend.TTS.phrase_preparation.processing_pipeline import process_pipeline

async def dispatch_to_phrase_queue(text: str, phrase_queue: asyncio.Queue):
    """
    Dispatches the text (phrase or whole text) to the phrase_queue.
    """
    await phrase_queue.put(text)

async def dispatch_to_other_module(text: str, phrase_queue: asyncio.Queue):
    """
    Processes the text using other modules before dispatching.
    """
    # Process the text through the pipeline
    processed_text = await process_pipeline(text)
    # Dispatch the processed text to the phrase_queue
    await phrase_queue.put(processed_text)
