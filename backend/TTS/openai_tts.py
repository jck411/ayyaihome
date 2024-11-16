import asyncio
import queue
import logging
from typing import Optional
from openai import AsyncOpenAI
from backend.config import Config, get_openai_client

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

            # Use OpenAI TTS settings from Config
            model = Config.OPENAI_TTS_CONFIG.get("TTS_MODEL", "tts-1")
            voice = Config.OPENAI_TTS_CONFIG.get("TTS_VOICE", "onyx")
            speed = Config.OPENAI_TTS_CONFIG.get("TTS_SPEED", 1.0)
            response_format = Config.OPENAI_TTS_CONFIG.get("AUDIO_RESPONSE_FORMAT", "pcm")

            logger.info(f"Using OpenAI TTS Model: {model}, Voice: {voice}, Speed: {speed}")

            async with openai_client.audio.speech.with_streaming_response.create(
                model=model,
                voice=voice,
                input=phrase,
                speed=speed,
                response_format=response_format
            ) as response:
                async for audio_chunk in response.iter_bytes(Config.TTS_CHUNK_SIZE):
                    audio_queue.put(audio_chunk)

            # Add a small pause between phrases
            audio_queue.put(b'\x00' * Config.TTS_CHUNK_SIZE)
    except Exception as e:
        logger.error(f"Error in TTS processing: {e}")
        audio_queue.put(None)
