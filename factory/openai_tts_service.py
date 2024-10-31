# openai_tts_service.py

from tts_service_interface import TTSService
import queue

class OpenAITTSService(TTSService):
    def __init__(self, client, sentence_queue, audio_queue, sentence_processing_complete, audio_generation_complete):
        self.client = client
        self.sentence_queue = sentence_queue
        self.audio_queue = audio_queue
        self.sentence_processing_complete = sentence_processing_complete
        self.audio_generation_complete = audio_generation_complete

    def generate_audio(self):
        while not (self.sentence_processing_complete.is_set() and self.sentence_queue.empty()):
            try:
                sentence = self.sentence_queue.get(timeout=0.5)
                with self.client.audio.speech.with_streaming_response.create(
                    model="tts-1",
                    voice="alloy",
                    input=sentence,
                    response_format="pcm"
                ) as response:
                    for audio_chunk in response.iter_bytes(1024):
                        self.audio_queue.put(audio_chunk)

                # Add a short pause between sentences
                self.audio_queue.put(b'\x00' * 4800)  # 0.1 seconds of silence at 24000 Hz
            except queue.Empty:
                continue

        self.audio_generation_complete.set()
