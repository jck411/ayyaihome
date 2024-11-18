import asyncio
import queue
import logging
from typing import Optional
from openai import AsyncOpenAI
from backend.config import Config, get_openai_client

# Initialize logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def get_config_value(config: dict, key: str, parent_key: str = ""):
    """
    Fetches a configuration value and ensures it exists.
    Raises a KeyError with a descriptive error message if the key is missing.
    """
    if key not in config:
        full_key = f"{parent_key}.{key}" if parent_key else key
        raise KeyError(f"Missing required configuration: '{full_key}'. Please set it in the config.")
    return config[key]

async def text_to_speech_processor(
    phrase_queue: asyncio.Queue,
    audio_queue: queue.Queue,
    openai_client: Optional[AsyncOpenAI] = None,
    start_tts_after_paragraph: bool = False,  # Add this argument for compatibility
):
    """
    Processes phrases into speech using the OpenAI TTS model.
    """
    openai_client = openai_client or get_openai_client()

    # Load and validate OpenAI TTS configurations
    openai_config = Config.OPENAI_TTS_CONFIG
    model = get_config_value(openai_config, "TTS_MODEL", "OPENAI_TTS_CONFIG")
    voice = get_config_value(openai_config, "TTS_VOICE", "OPENAI_TTS_CONFIG")
    speed = get_config_value(openai_config, "TTS_SPEED", "OPENAI_TTS_CONFIG")
    response_format = get_config_value(openai_config, "AUDIO_RESPONSE_FORMAT", "OPENAI_TTS_CONFIG")
    chunk_size = Config.TTS_CHUNK_SIZE  # Fetch from GENERAL_TTS instead of OPENAI_TTS_CONFIG

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
