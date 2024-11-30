import asyncio
import pyaudio
import logging

# Set up logging
logging.basicConfig(level=logging.CRITICAL)
logger = logging.getLogger(__name__)

def audio_player_sync(audio_queue: asyncio.Queue, playback_rate: int, loop: asyncio.AbstractEventLoop):
    """
    Synchronous audio player that reads from an asyncio queue.
    """
    pyaudio_instance = pyaudio.PyAudio()
    stream = None
    try:
        # Initialize PyAudio stream
        stream = pyaudio_instance.open(
            format=pyaudio.paInt16,  # 16-bit PCM
            channels=1,              # Mono audio
            rate=playback_rate,      # Playback rate
            output=True
        )
        logger.info(f"Audio player started with playback rate: {playback_rate} Hz")

        while True:
            # Fetch audio data from the queue using the provided event loop
            future = asyncio.run_coroutine_threadsafe(
                audio_queue.get(), loop
            )
            try:
                audio_data = future.result()
            except Exception as e:
                logger.error(f"Error fetching audio data: {e}")
                break

            if audio_data is None:
                logger.info("Received termination signal. Stopping audio playback.")
                break  # Exit when None is received

            try:
                stream.write(audio_data)  # Play the audio chunk
                logger.debug("Played an audio chunk.")
            except Exception as e:
                logger.error(f"Error writing to stream: {e}")
                break
    except Exception as e:
        logger.error(f"Error in audio_player_sync: {e}")
    finally:
        if stream:
            stream.stop_stream()
            stream.close()
            logger.info("Audio stream closed.")
        pyaudio_instance.terminate()
        logger.info("PyAudio instance terminated.")

async def start_audio_player_async(audio_queue: asyncio.Queue, playback_rate: int, loop: asyncio.AbstractEventLoop):
    """
    Asynchronous wrapper for the synchronous PyAudio player.
    """
    logger.info("Starting asynchronous audio player.")
    await asyncio.to_thread(audio_player_sync, audio_queue, playback_rate, loop)
    logger.info("Asynchronous audio player has stopped.")
