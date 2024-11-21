# /home/jack/ayyaihome/backend/TTS/phrase_preparation/processing_pipeline.py

import asyncio
from backend.config import Config
from backend.TTS.phrase_preparation.tokenizer import tokenize_text
from backend.TTS.phrase_preparation.custom_text_modifier import modify_text

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
        if module_name == 'tokenizer':
            text = await tokenize_text(text, Config.TOKENIZER_TYPE)
        elif module_name == 'custom_text_modifier':
            if Config.CUSTOM_TEXT_MODIFIER_ENABLED:
                text = await modify_text(text)
        else:
            # Handle unknown modules or raise an error
            pass

    # Return the final processed text
    return text
