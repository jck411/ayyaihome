# /home/jack/ayyaihome/backend/TTS/phrase_preparation/processing_pipeline.py

import asyncio
from backend.config import Config
from backend.TTS.phrase_preparation.tokenizer import tokenize_text
from backend.TTS.phrase_preparation.custom_text_modifier import modify_text
from backend.TTS.phrase_preparation.phrase_segmentation import segment_text

async def process_pipeline(text: str) -> str:
    """
    Processes the text through the configured modules and returns the final output.

    Args:
        text (str): The text to process.

    Returns:
        str: The processed text.
    """
    modules = Config.MODULES
    for module_name in modules:
        if module_name == 'segmentation':
            if Config.USE_PHRASE_SEGMENTATION:
                working_string = text
                working_string, phrases = await segment_text(working_string, Config)
                # Optionally process each phrase further
                processed_phrases = []
                for phrase in phrases:
                    # You can process each phrase with other modules if needed
                    processed_phrases.append(phrase)
                # Combine back to text
                text = ' '.join(processed_phrases) + ' ' + working_string
        elif module_name == 'tokenizer':
            text = await tokenize_text(text, Config.TOKENIZER_TYPE)
        elif module_name == 'custom_text_modifier':
            if Config.CUSTOM_TEXT_MODIFIER_ENABLED:
                text = await modify_text(text)
        else:
            # Handle unknown modules or raise an error
            pass

    # Return the final processed text
    return text.strip()

async def dispatch_to_phrase_queue(text: str, phrase_queue: asyncio.Queue):
    """
    Processes the text using the processing pipeline before dispatching.

    Args:
        text (str): The text to process and dispatch.
        phrase_queue (asyncio.Queue): The queue to dispatch phrases to.
    """
    # Process the text through the pipeline
    processed_text = await process_pipeline(text)
    # Dispatch the processed text to the phrase_queue
    await phrase_queue.put(processed_text)
