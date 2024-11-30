import asyncio
import logging
from typing import Optional
from openai import AsyncOpenAI
from backend.config import Config, get_openai_client

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
    except AttributeError:
        await audio_queue.put(None)
        return

    try:
        while True:
            phrase = await phrase_queue.get()
            if phrase is None:
                # Signal the end of processing
                await audio_queue.put(None)
                return

            # Strip the phrase and check if it's non-empty
            stripped_phrase = phrase.strip()
            if not stripped_phrase:
                continue

            try:
                # Make the TTS API call with streaming response
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

            except Exception:
                # Skip to the next phrase without terminating the audio queue
                continue

    except Exception:
        await audio_queue.put(None)
