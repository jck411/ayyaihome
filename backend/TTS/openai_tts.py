import asyncio
import logging
from typing import Optional
from openai import AsyncOpenAI
from backend.config import Config, get_openai_client

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Disable logging for httpx
logging.getLogger("httpx").setLevel(logging.CRITICAL)

async def text_to_speech_processor(
    phrase_queue: asyncio.Queue,
    audio_queue: asyncio.Queue,
    openai_client: Optional[AsyncOpenAI] = None
):
    openai_client = openai_client or get_openai_client()

    # Load OpenAI TTS configurations directly from Config
    try:
        model = Config.OPENAI_TTS_MODEL
        voice = Config.OPENAI_TTS_VOICE
        speed = Config.OPENAI_TTS_SPEED
        response_format = Config.OPENAI_AUDIO_FORMAT
        chunk_size = Config.OPENAI_TTS_CHUNK_SIZE
        logger.info("Loaded TTS configuration: model=%s, voice=%s, speed=%s, format=%s, chunk_size=%d",
                    model, voice, speed, response_format, chunk_size)
    except AttributeError as e:
        logger.error("Missing TTS configuration: %s", e)
        await audio_queue.put(None)
        return

    try:
        while True:
            phrase = await phrase_queue.get()
            if phrase is None:
                logger.info("Received termination signal. Ending processing.")
                await audio_queue.put(None)
                return

            stripped_phrase = phrase.strip()
            if not stripped_phrase:
                logger.warning("Received empty phrase. Skipping.")
                continue

            logger.info("Processing phrase: '%s'", stripped_phrase)

            try:
                async with openai_client.audio.speech.with_streaming_response.create(
                    model=model,
                    voice=voice,
                    input=stripped_phrase,
                    speed=speed,
                    response_format=response_format
                ) as response:
                    async for audio_chunk in response.iter_bytes(chunk_size):
                        await audio_queue.put(audio_chunk)

                # Add a small pause between phrases
                await audio_queue.put(b'\x00' * chunk_size)

            except Exception as e:
                logger.error("Error processing phrase '%s': %s", stripped_phrase, e)
                continue

    except Exception as e:
        logger.critical("Unexpected error in text_to_speech_processor: %s", e, exc_info=True)
        await audio_queue.put(None)
