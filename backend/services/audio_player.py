import logging
import queue
import threading
from init import p, OPENAI_CONSTANTS  # Remove stop_event import

def audio_player(audio_queue: queue.Queue):
    """
    Plays audio data from the audio queue using PyAudio.
    Runs in a separate thread.
    """
    stream = None
    try:
        # Open the PyAudio stream for playback
        stream = p.open(
            format=OPENAI_CONSTANTS["AUDIO_FORMAT"],
            channels=OPENAI_CONSTANTS["CHANNELS"],
            rate=OPENAI_CONSTANTS["RATE"],
            output=True,
            frames_per_buffer=2048  # Buffer size for audio playback
        )
        stream.write(b'\x00' * 2048)  # Pre-fill buffer with silence

        while True:
            # Get the next chunk of audio data
            try:
                audio_data = audio_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            if audio_data is None:
                break  # Exit if there's no more audio data

            # Ensure audio data is in the correct PCM format
            if not isinstance(audio_data, (bytes, bytearray)):
                continue

            # Play the audio data
            stream.write(audio_data)
    except Exception as e:
        logging.exception(f"Error in audio_player: {e}")
    finally:
        if stream:
            stream.stop_stream()  # Stop the audio stream
            stream.close()  # Close the audio stream
        logging.info("Audio player has been stopped.")

def start_audio_player(audio_queue: queue.Queue):
    """
    Starts the audio player in a separate thread.
    """
    threading.Thread(target=audio_player, args=(audio_queue,), daemon=True).start()

