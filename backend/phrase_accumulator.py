# backend/phrase_accumulator.py

import asyncio
from typing import List, Optional, Callable
from backend.config import Config
from backend.TTS.phrase_preparation.phrase_segmentation import segment_text
from backend.TTS.phrase_preparation.tokenizer import tokenize_text
from backend.TTS.phrase_preparation.custom_text_modifier import modify_text

class PhraseAccumulator:
    def __init__(self, config: Config, phrase_queue: asyncio.Queue):
        self.config = config
        self.working_string = ""
        self.phrase_queue = phrase_queue

    async def add_content(self, content: str) -> None:
        """
        Adds content to the working string and processes phrases if any are ready.
        Dispatches processed phrases to the phrase queue.

        Args:
            content (str): The incoming content chunk.
        """
        self.working_string += content

        # Determine if segmentation is enabled
        if 'segmentation' in self.config.MODULES and self.config.USE_PHRASE_SEGMENTATION:
            self.working_string, phrases = await segment_text(self.working_string, self.config)
        else:
            # If segmentation is disabled, treat end of stream as delimiter handled in finalize()
            phrases = []

        # Process and dispatch each phrase
        for phrase in phrases:
            processed_phrase = await self.process_phrase(phrase)
            await self.phrase_queue.put(processed_phrase)  # Dispatch to the queue immediately

    async def finalize(self) -> None:
        """
        Finalizes processing any remaining content in the working string.
        Dispatches the processed residual content to the phrase queue.
        """
        if self.working_string.strip():
            # Treat end of stream as a delimiter
            processed_text = await self.process_phrase(self.working_string.strip())
            self.working_string = ""
            await self.phrase_queue.put(processed_text)

        # Signal completion
        await self.phrase_queue.put(None)

    async def process_phrase(self, phrase: str) -> str:
        """
        Processes a phrase through the enabled modules and returns the final output.

        Args:
            phrase (str): The phrase to process.

        Returns:
            str: The processed phrase.
        """
        # Apply tokenizer if enabled
        if 'tokenizer' in self.config.MODULES:
            phrase = await tokenize_text(phrase)

        # Apply custom text modifier if enabled
        if 'custom_text_modifier' in self.config.MODULES and self.config.CUSTOM_TEXT_MODIFIER_ENABLED:
            phrase = await modify_text(phrase)

        return phrase
