# /home/jack/ayyaihome/backend/services/audio_player.py

import queue
import threading
import logging
from init import p, stop_event, OPENAI_CONSTANTS

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Set the logging level to INFO
    format='%(asctime)s - %(levelname)s - %(message)s'  # Define log message format
)
logger = logging.getLogger(__name__)

def find_next_phrase_end(text: str) -> int:
    """
    Finds the position of the next sentence-ending delimiter in the text
    starting from a specified minimum length.
    """
    sentence_delim_pos = [text.find(d, OPENAI_CONSTANTS["MINIMUM_PHRASE_LENGTH"]) for d in OPENAI_CONSTANTS["DELIMITERS"]]
    sentence_delim_pos = [pos for pos in sentence_delim_pos if pos != -1]
    return min(sentence_delim_pos, default=-1)

def audio_player(audio_queue: queue.Queue):
    """
    Plays audio data from the audio queue using PyAudio.
    Runs in a separate thread.
    Logs when playback starts and ends.
    """
    stream = None
    audio_playing = False  # Flag to track if audio is currently playing
    try:
        # Open the PyAudio stream for playback
        stream = p.open(
            format=OPENAI_CONSTANTS["AUDIO_FORMAT"],  # Use configurable audio format
            channels=OPENAI_CONSTANTS["CHANNELS"],
            rate=OPENAI_CONSTANTS["RATE"],
            output=True,
            frames_per_buffer=2048  # Buffer size for audio playback
        )
        stream.write(b'\x00' * 2048)  # Pre-fill buffer with silence

        logger.info("Audio player thread started.")

        while not stop_event.is_set():
            # Get the next chunk of audio data
            audio_data = audio_queue.get()

            if audio_data is None:
                if audio_playing:
                    logger.info("Audio playback ended.")
                break  # Exit if there's no more audio data

            # Ensure audio data is in the correct PCM format
            if not isinstance(audio_data, (bytes, bytearray)):
                continue

            if not audio_playing:
                logger.info("Audio playback started.")
                audio_playing = True

            # Play the audio data
            stream.write(audio_data)
            # Optionally, log each audio chunk being played (use DEBUG level to avoid clutter)
            # logger.debug("Playing audio chunk.")

        if audio_playing:
            logger.info("Audio playback ended.")

    except Exception as e:
        logger.error(f"Error in audio_player: {e}")
    finally:
        if stream:
            stream.stop_stream()  # Stop the audio stream
            stream.close()  # Close the audio stream
            logger.info("Audio stream closed.")

def start_audio_player(audio_queue: queue.Queue):
    """
    Starts the audio player in a separate thread.
    """
    threading.Thread(target=audio_player, args=(audio_queue,), daemon=True).start()
    logger.info("Audio player thread initiated.")
