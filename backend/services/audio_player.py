import queue
import threading
from init import p, stop_event, CONSTANTS
import asyncio

def find_next_phrase_end(text: str) -> int:
    """
    Finds the position of the next sentence-ending delimiter in the text
    starting from a specified minimum length.
    """
    sentence_delim_pos = [text.find(d, CONSTANTS["MINIMUM_PHRASE_LENGTH"]) for d in CONSTANTS["DELIMITERS"]]
    sentence_delim_pos = [pos for pos in sentence_delim_pos if pos != -1]
    return min(sentence_delim_pos, default=-1)

def audio_player(audio_queue: queue.Queue):
    """
    Plays audio data from the audio queue using PyAudio.
    Runs in a separate thread.
    """
    stream = None
    try:
        # Open the PyAudio stream for playback
        stream = p.open(
            format=CONSTANTS["AUDIO_FORMAT"],
            channels=CONSTANTS["CHANNELS"],
            rate=CONSTANTS["RATE"],
            output=True,
            frames_per_buffer=2048  # Buffer size for audio playback
        )
        stream.write(b'\x00' * 2048)  # Pre-fill buffer with silence

        while not stop_event.is_set():
            # Get the next chunk of audio data
            audio_data = audio_queue.get()

            if asyncio.iscoroutine(audio_data):
                # If somehow a coroutine got into the queue, this will catch it
                raise TypeError("Coroutines cannot be played as audio. Ensure correct data is passed.")
            
            if audio_data is None:
                break  # Exit if there's no more audio data

            # Play the audio data
            stream.write(audio_data)
    except Exception as e:
        print(f"Error in audio player: {e}")
    finally:
        if stream:
            stream.stop_stream()  # Stop the audio stream
            stream.close()  # Close the audio stream

def start_audio_player(audio_queue: queue.Queue):
    """
    Starts the audio player in a separate thread.
    """
    threading.Thread(target=audio_player, args=(audio_queue,)).start()
