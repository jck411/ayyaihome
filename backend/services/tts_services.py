# services/tts_services.py

import asyncio
import logging
from services.ai_services import AIService


from abc_classes import TTSService
from config import Config

logger = logging.getLogger(__name__)

class OpenAITTSService(TTSService):
    def __init__(self, client: 'AIService', config: Config):  # Using a forward reference
        self.client = client
        self.config = config


    async def process(
        self, 
        phrase_queue: asyncio.Queue, 
        audio_queue: asyncio.Queue, 
        stop_event: asyncio.Event, 
        stream_id: str
    ):
        try:
            while not stop_event.is_set():
                phrase = await phrase_queue.get()
                if phrase is None:
                    await audio_queue.put(None)
                    break

                try:
                    if self.config.tts_service.RESPONSE_FORMAT not in self.config.response_format.SUPPORTED_FORMATS:
                        raise ValueError(f"Unsupported response format: {self.config.tts_service.RESPONSE_FORMAT}")

                    async with self.client.client.audio.speech.with_streaming_response.create(
                        model=self.config.tts_service.DEFAULT_TTS_MODEL,
                        voice=self.config.tts_service.DEFAULT_VOICE,
                        input=phrase,
                        speed=self.config.TTS_SPEED,
                        response_format=self.config.tts_service.RESPONSE_FORMAT
                    ) as response:
                        async for audio_chunk in response.iter_bytes(self.config.TTS_CHUNK_SIZE):
                            if stop_event.is_set():
                                break
                            await audio_queue.put(audio_chunk)
                    await audio_queue.put(b'\x00' * 2400)
                except Exception as e:
                    logger.error(f"Error in TTS processing (Stream ID: {stream_id}): {e}")
                    await audio_queue.put(None)
                    break
        finally:
            await audio_queue.put(None)
