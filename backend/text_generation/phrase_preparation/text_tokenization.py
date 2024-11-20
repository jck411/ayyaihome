# backend/text_generation/phrase_preparation/text_tokenization.py

import asyncio
import logging
from typing import Optional
import nltk
from stanza.pipeline.core import Pipeline as StanzaPipeline

# Initialize logging
logger = logging.getLogger(__name__)

# Global variables
stanza_pipeline = None
stanza_lock = asyncio.Lock()
nltk_downloaded = False

def initialize_nltk():
    global nltk_downloaded
    if not nltk_downloaded:
        nltk.download("punkt", quiet=True)
        nltk_downloaded = True
        logger.info("NLTK 'punkt' tokenizer downloaded.")

async def initialize_stanza():
    global stanza_pipeline
    async with stanza_lock:
        if stanza_pipeline is None:
            stanza_pipeline = StanzaPipeline(lang="en", processors="tokenize", use_gpu=False)
            logger.info("Stanza pipeline initialized.")

async def tokenize_and_queue(phrase: str, phrase_queue: asyncio.Queue, tokenizer: str):
    """
    Tokenizes text and queues the result.

    Args:
        phrase (str): The text to tokenize.
        phrase_queue (asyncio.Queue): Queue to store the tokenized phrase.
        tokenizer (str): The tokenizer to use ('nltk', 'stanza', or 'none').
    """
    try:
        if tokenizer.lower() == "nltk":
            initialize_nltk()
            tokens = nltk.word_tokenize(phrase)
            logger.debug(f"NLTK tokens: {tokens}")
        elif tokenizer.lower() == "stanza":
            await initialize_stanza()
            doc = stanza_pipeline(phrase)
            tokens = [word.text for sentence in doc.sentences for word in sentence.words]
            logger.debug(f"Stanza tokens: {tokens}")
        elif tokenizer.lower() == "none":
            tokens = [phrase]
            logger.debug("Tokenization is disabled. Passing phrase as-is.")
        else:
            raise ValueError(f"Unsupported tokenizer: {tokenizer}")

        # Queue the tokenized phrase
        tokenized_phrase = " ".join(tokens)
        await phrase_queue.put(tokenized_phrase)
        logger.debug(f"Queued tokenized phrase: {tokenized_phrase}")
    except Exception as e:
        logger.error(f"Error during tokenization: {e}")
        await phrase_queue.put(phrase)  # Fallback to original phrase
