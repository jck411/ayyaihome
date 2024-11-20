import time
import queue
import threading
import pyaudio

# Initialize PyAudio for audio playback
pyaudio_instance = pyaudio.PyAudio()

def audio_player(audio_queue: queue.Queue, playback_rate: int):
    """
    Plays audio data from the audio queue using PyAudio with the specified playback rate.
    """
    stream = None
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

            stream.write(audio_data)  # Play the audio chunk
    except Exception:
        pass  
    finally:
        if stream:
            stream.stop_stream()
            stream.close()

def start_audio_player(audio_queue: queue.Queue, playback_rate: int):
    """
    Starts the audio player in a separate thread with the specified playback rate.
    """
    threading.Thread(
        target=audio_player,
        args=(audio_queue, playback_rate),
        daemon=True
    ).start()
