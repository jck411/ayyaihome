import asyncio
import queue
from typing import Optional
from openai import AsyncOpenAI
from backend.config import Config, get_openai_client

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
    openai_client: Optional[AsyncOpenAI] = None
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
    chunk_size = get_config_value(openai_config, "TTS_CHUNK_SIZE", "OPENAI_TTS_CONFIG")

    try:
        while True:
            phrase = await phrase_queue.get()
            if phrase is None:
                # Signal the end of processing
                audio_queue.put(None)
                return

            try:
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
                audio_queue.put(None)
    except Exception as e:
        audio_queue.put(None)