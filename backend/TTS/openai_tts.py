
import asyncio
import queue
import time
from typing import List, Dict, Optional
import logging
from openai import AsyncOpenAI
from backend.config import Config, get_openai_client  # Absolute import

# Initialize logging
logger = logging.getLogger(__name__)


async def text_to_speech_processor(
    phrase_queue: asyncio.Queue,
    audio_queue: queue.Queue,
    openai_client: Optional[AsyncOpenAI] = None
):
    """
    Processes phrases into speech using the OpenAI TTS model.
    """
    openai_client = openai_client or get_openai_client()
    try:
        while True:
            phrase = await phrase_queue.get()
            if phrase is None:
                audio_queue.put(None)
                return

            async with openai_client.audio.speech.with_streaming_response.create(
                model=Config.TTS_MODEL,
                voice=Config.TTS_VOICE,
                input=phrase,
                speed=Config.TTS_SPEED,
                response_format=Config.AUDIO_RESPONSE_FORMAT
            ) as response:
                async for audio_chunk in response.iter_bytes(Config.TTS_CHUNK_SIZE):
                    audio_queue.put(audio_chunk)
            # Add a small pause between phrases
            audio_queue.put(b'\x00' * 2400)
    except Exception as e:
        logger.error(f"Error in TTS processing: {e}")
        audio_queue.put(None)