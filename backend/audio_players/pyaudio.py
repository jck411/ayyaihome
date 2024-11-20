# backend/audio_players/pyaudio.py

import time
import threading
import logging
import queue

import pyaudio
from backend.config import AUDIO_FORMAT_PLAYBACK_RATE_MAP

logger = logging.getLogger(__name__)

# Initialize PyAudio instance
pyaudio_instance = pyaudio.PyAudio()

def audio_player(audio_queue: queue.Queue, request_timestamp: float, playback_rate: int):
    """
    Plays audio data from the audio queue using PyAudio with the specified playback rate.

    Args:
        audio_queue (queue.Queue): Queue containing audio data.
        request_timestamp (float): Timestamp when the request was received.
        playback_rate (int): Playback rate (sample rate in Hz).
    """
    stream = None
    try:
        # Open PyAudio stream with dynamic playback rate
        stream = pyaudio_instance.open(
            format=pyaudio.paInt16,  # 16-bit PCM
            channels=1,             # Mono audio
            rate=playback_rate,     # Dynamic playback rate
            output=True
        )
        logger.info(f"Audio stream opened with playback rate: {playback_rate} Hz.")

        while True:
            audio_data = audio_queue.get()
            if audio_data is None:
                logger.info("Received termination signal for audio playback.")
                break  # End playback
            stream.write(audio_data)
    except Exception as e:
        logger.error(f"Error in audio player: {e}")
    finally:
        if stream:
            stream.stop_stream()
            stream.close()
            logger.info("Audio stream closed.")

def start_audio_player(audio_queue: queue.Queue, request_timestamp: float, playback_rate: int):
    """
    Starts the audio player in a separate thread with the specified playback rate.

    Args:
        audio_queue (queue.Queue): Queue containing audio data.
        request_timestamp (float): Timestamp when the request was received.
        playback_rate (int): Playback rate (sample rate in Hz).
    """
    try:
        threading.Thread(
            target=audio_player,
            args=(audio_queue, request_timestamp, playback_rate),
            daemon=True
        ).start()
        logger.info("Audio player thread started.")
    except Exception as e:
        logger.error(f"Failed to start audio player thread: {e}")
        raise
