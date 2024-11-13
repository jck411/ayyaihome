import time
import queue
import threading
import logging
import pyaudio
from backend.config import Config  # Absolute import for configuration

# Initialize logging
logger = logging.getLogger(__name__)

# Initialize PyAudio for audio playback
pyaudio_instance = pyaudio.PyAudio()

def audio_player(audio_queue: queue.Queue, request_timestamp: float):
    """
    Plays audio data from the audio queue using PyAudio.
    """
    stream = None
    first_audio_timestamp = None
    try:
        stream = pyaudio_instance.open(
            format=Config.AUDIO_FORMAT,
            channels=Config.CHANNELS,
            rate=Config.RATE,
            output=True
        )

        while True:
            audio_data = audio_queue.get()
            if audio_data is None:
                break

            if first_audio_timestamp is None:
                first_audio_timestamp = time.time()
                elapsed_time = first_audio_timestamp - request_timestamp
                logger.info(f"Time to first audio: {elapsed_time:.2f} seconds")

            stream.write(audio_data)
    except Exception as e:
        logger.error(f"Error in audio player: {e}")
    finally:
        if stream:
            stream.stop_stream()
            stream.close()

def start_audio_player(audio_queue: queue.Queue, request_timestamp: float):
    threading.Thread(target=audio_player, args=(audio_queue, request_timestamp), daemon=True).start()
