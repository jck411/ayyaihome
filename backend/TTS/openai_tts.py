# backend/TTS/openai_tts.py

import asyncio
import queue
import logging
from typing import Optional

from backend.config import Config, get_openai_client
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

async def openai_text_to_speech_processor(
    phrase_queue: asyncio.Queue,
    audio_queue: queue.Queue,
    openai_client: Optional[AsyncOpenAI] = None,
    start_tts_after_paragraph: bool = False,  # Add this argument for compatibility
):
    """
    Processes phrases into speech using the OpenAI TTS model.

    Args:
        phrase_queue (asyncio.Queue): Queue containing phrases to process.
        audio_queue (queue.Queue): Queue to send audio data.
        openai_client (Optional[AsyncOpenAI]): OpenAI client instance.
        start_tts_after_paragraph (bool): Whether to start TTS after a paragraph.
    """
    openai_client = openai_client or get_openai_client()

    # Load and validate OpenAI TTS configurations
    openai_config = Config.OPENAI_TTS
    model = openai_config.get("TTS_MODEL", "tts-1")
    voice = openai_config.get("TTS_VOICE", "onyx")
    speed = openai_config.get("TTS_SPEED", 1.0)
    response_format = openai_config.get("AUDIO_RESPONSE_FORMAT", "pcm")
    chunk_size = Config.AUDIO_FORMAT  # Assuming AUDIO_FORMAT corresponds to chunk_size

    buffer = []  # Buffer to accumulate text for paragraph handling

    try:
        while True:
            phrase = await phrase_queue.get()
            if phrase is None:
                # Process remaining buffer if needed
                if start_tts_after_paragraph and buffer:
                    combined_text = " ".join(buffer)
                    await process_openai_tts(combined_text, audio_queue, openai_client, model, voice, speed, response_format, chunk_size)
                    buffer = []
                # Signal the end of processing
                audio_queue.put(None)
                logger.info("TTS processing complete.")
                return

            if start_tts_after_paragraph:
                # Accumulate phrases in the buffer
                buffer.append(phrase)
                if phrase.endswith("\n") or not phrase_queue.empty():
                    continue  # Wait for more input
                combined_text = " ".join(buffer)
                await process_openai_tts(combined_text, audio_queue, openai_client, model, voice, speed, response_format, chunk_size)
                buffer = []
            else:
                # Process each phrase immediately
                await process_openai_tts(phrase, audio_queue, openai_client, model, voice, speed, response_format, chunk_size)
    except Exception as e:
        logger.error(f"Error in TTS processing: {e}")
        audio_queue.put(None)

async def process_openai_tts(phrase, audio_queue, openai_client, model, voice, speed, response_format, chunk_size):
    """
    Handles the actual processing of a single phrase with OpenAI TTS.

    Args:
        phrase (str): The phrase to convert to speech.
        audio_queue (queue.Queue): Queue to send audio data.
        openai_client (AsyncOpenAI): OpenAI client instance.
        model (str): OpenAI TTS model to use.
        voice (str): Voice to use for TTS.
        speed (float): Speed of speech.
        response_format (str): Audio response format.
        chunk_size (int): Size of audio chunks.
    """
    try:
        logger.info(f"Processing phrase with OpenAI TTS: {phrase}")
        async with openai_client.audio.speech.with_streaming_response.create(
            model=model,
            voice=voice,
            input=phrase,
            speed=speed,
            response_format=response_format
        ) as response:
            async for audio_chunk in response.iter_bytes(chunk_size):
                audio_queue.put(audio_chunk)

        # Add a small pause between phrases
        audio_queue.put(b'\x00' * chunk_size)
    except Exception as e:
        logger.error(f"Error processing phrase '{phrase}': {e}")
