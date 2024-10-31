# openai_tts_service.py

from tts_service_interface import TTSService
import asyncio
import logging

logger = logging.getLogger(__name__)

class OpenAITTSService(TTSService):
    def __init__(self, client, sentence_queue, audio_queue, sentence_processing_complete, audio_generation_complete):
        self.client = client  # This should be the openai module
        self.sentence_queue = sentence_queue
        self.audio_queue = audio_queue
        self.sentence_processing_complete = sentence_processing_complete
        self.audio_generation_complete = audio_generation_complete

    async def _process_sentence(self, sentence):
        # This function will run in a separate thread
        try:
            with self.client.audio.speech.with_streaming_response.create(
                model="tts-1",
                voice="alloy",
                input=sentence,
                response_format="pcm"
            ) as response:
                audio_data = b""
                for audio_chunk in response.iter_bytes(1024):
                    audio_data += audio_chunk
                    # Put each audio chunk into the queue asynchronously
                    await self.audio_queue.put(audio_chunk)
                
            # Add a short pause between sentences
            await self.audio_queue.put(b'\x00' * 4800)  # 0.1 seconds of silence at 24000 Hz

        except Exception as e:
            logger.error(f"Error processing sentence for TTS: {e}")

    async def generate_audio(self):
        loop = asyncio.get_event_loop()

        while not (self.sentence_processing_complete.is_set() and self.sentence_queue.empty()):
            try:
                # Use asyncio.wait_for to implement a timeout
                sentence = await asyncio.wait_for(self.sentence_queue.get(), timeout=0.5)
            except asyncio.TimeoutError:
                await asyncio.sleep(0.1)
                continue

            # Offload the blocking TTS processing to a separate thread
            await loop.run_in_executor(None, asyncio.run, self._process_sentence(sentence))

        # Signal that audio generation is complete
        self.audio_generation_complete.set()
