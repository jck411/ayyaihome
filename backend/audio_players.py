# audio_players.py

import time
import asyncio
import logging

import pyaudio

from abc_classes import AudioPlayerBase
from config import Config

logger = logging.getLogger(__name__)

class PyAudioPlayer(AudioPlayerBase):
    def __init__(self, config: Config):
        self.pyaudio_instance = pyaudio.PyAudio()
        self.config = config

    async def play(
        self, 
        audio_queue: asyncio.Queue, 
        stop_event: asyncio.Event, 
        stream_id: str, 
        start_time: float
    ):
        stream = None
        try:
            stream = self.pyaudio_instance.open(
                format=self.config.AUDIO_FORMAT,
                channels=self.config.CHANNELS,
                rate=self.config.RATE,
                output=True,
                frames_per_buffer=2048
            )
            await asyncio.to_thread(stream.write, b'\x00' * 2048)

            first_audio = True  # Flag to check for the first audio chunk

            while not stop_event.is_set():
                audio_data = await audio_queue.get()
                if audio_data is None:
                    break

                # Measure time when the first audio data is processed
                if first_audio:
                    elapsed_time = time.time() - start_time
                    logger.info(f"Time taken for the first audio to be heard: {elapsed_time:.2f} seconds")
                    first_audio = False  # Reset the flag after the first chunk is processed

                await asyncio.to_thread(stream.write, audio_data)
        except Exception as e:
            logger.error(f"Error in audio player (Stream ID: {stream_id}): {e}")
        finally:
            if stream:
                await asyncio.to_thread(stream.stop_stream)
                await asyncio.to_thread(stream.close)

    def terminate(self):
        self.pyaudio_instance.terminate()
