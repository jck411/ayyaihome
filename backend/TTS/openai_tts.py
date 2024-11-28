import asyncio
import queue
import logging
from typing import Optional
from openai import AsyncOpenAI

from backend.config import Config, get_openai_client

# Set up logging
logging.basicConfig(level=logging.DEBUG)
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

    logger.info("Initializing OpenAI TTS processor.")

    # Load OpenAI TTS configurations directly from Config
    try:
        model = Config.OPENAI_TTS_MODEL
        voice = Config.OPENAI_TTS_VOICE
        speed = Config.OPENAI_TTS_SPEED
        response_format = Config.OPENAI_AUDIO_FORMAT
        chunk_size = Config.OPENAI_TTS_CHUNK_SIZE

        logger.info(f"Configuration loaded: model={model}, voice={voice}, speed={speed}, "
                    f"response_format={response_format}, chunk_size={chunk_size}")
    except AttributeError as e:
        logger.error(f"Configuration error: {e}")
        audio_queue.put(None)
        return

    try:
        while True:
            logger.debug("Waiting for a phrase from the queue.")
            phrase = await phrase_queue.get()
            if phrase is None:
                # Signal the end of processing
                logger.info("Received termination signal. Ending TTS processing.")
                audio_queue.put(None)
                return

            logger.info(f"Processing phrase: {phrase}")

            try:
                async with openai_client.audio.speech.with_streaming_response.create(
                    model=model,
                    voice=voice,
                    input=phrase,
                    speed=speed,
                    response_format=response_format
                ) as response:
                    logger.info("TTS API call successful. Streaming audio...")
                    async for audio_chunk in response.iter_bytes(chunk_size):
                        audio_queue.put(audio_chunk)
                        logger.debug("Audio chunk added to the queue.")
                
                # Add a small pause between phrases
                audio_queue.put(b'\x00' * chunk_size)
                logger.debug("Pause added between phrases.")

            except Exception as e:
                logger.error(f"Error during TTS processing for phrase '{phrase}': {e}")
                audio_queue.put(None)

    except Exception as e:
        logger.error(f"Unexpected error in TTS processor: {e}")
        audio_queue.put(None)
