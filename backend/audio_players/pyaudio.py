import time
import queue
import threading
import logging
import pyaudio

# Initialize logging
logger = logging.getLogger(__name__)

# Initialize PyAudio for audio playback
pyaudio_instance = pyaudio.PyAudio()

def audio_player(audio_queue: queue.Queue, request_timestamp: float, playback_rate: int):
    """
    Plays audio data from the audio queue using PyAudio with the specified playback rate.
    """
    stream = None
    first_audio_timestamp = None
    try:
        # Open PyAudio stream with dynamic playback rate
        stream = pyaudio_instance.open(
            format=pyaudio.paInt16,  # 16-bit PCM
            channels=1,             # Mono audio
            rate=playback_rate,     # Dynamically set playback rate
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

            stream.write(audio_data)  # Play the audio chunk
    except Exception as e:
        logger.error(f"Error in audio player: {e}")
    finally:
        if stream:
            stream.stop_stream()
            stream.close()

def start_audio_player(audio_queue: queue.Queue, request_timestamp: float, playback_rate: int):
    threading.Thread(
        target=audio_player,
        args=(audio_queue, request_timestamp, playback_rate),
        daemon=True
    ).start()
