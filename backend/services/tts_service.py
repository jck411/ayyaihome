# /home/jack/ayyaihome/backend/services/tts_service.py

import asyncio
import logging
import queue
from threading import Event
from init import aclient, SHARED_CONSTANTS, connection_manager, pyaudio

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def process_streams(phrase_queue: asyncio.Queue, audio_queue: queue.Queue, tts_constants, stop_event: Event):
    if SHARED_CONSTANTS.get("FRONTEND_PLAYBACK", False):
        # Frontend playback via WebSocket
        audio_sender_task = asyncio.create_task(audio_sender(audio_queue, stop_event))
        await text_to_speech_processor(phrase_queue, audio_queue, tts_constants, stop_event)
        audio_queue.put(None)
        await audio_sender_task
    else:
        # Backend audio playback
        audio_player_task = asyncio.create_task(audio_player(audio_queue, tts_constants, stop_event))
        await text_to_speech_processor(phrase_queue, audio_queue, tts_constants, stop_event)
        audio_queue.put(None)
        await audio_player_task

async def text_to_speech_processor(phrase_queue: asyncio.Queue, audio_queue: queue.Queue, tts_constants, stop_event: Event):
    try:
        while not stop_event.is_set():
            phrase = await phrase_queue.get()
            if phrase is None:
                logger.info("Received stop signal. Exiting TTS processor.")
                return
            try:
                logger.info(f"Processing phrase: {phrase}")
                # Process one phrase at a time
                async with aclient.audio.speech.with_streaming_response.create(
                    model=tts_constants["DEFAULT_TTS_MODEL"],
                    voice=tts_constants["DEFAULT_VOICE"],
                    input=phrase,
                    speed=tts_constants["TTS_SPEED"],
                    response_format=tts_constants["RESPONSE_FORMAT"]
                ) as response:
                    audio_data = b""
                    async for audio_chunk in response.iter_bytes(tts_constants["TTS_CHUNK_SIZE"]):
                        if stop_event.is_set():
                            logger.info("Stop event detected. Terminating TTS processing.")
                            return
                        audio_data += audio_chunk
                    # Enqueue the audio data
                    audio_queue.put(audio_data)
                    logger.info(f"Enqueued audio data for phrase.")
            except Exception as tts_error:
                logger.error(f"TTS processing failed with error: {tts_error}")
                audio_queue.put(None)
                break  # Exit on TTS error
    except Exception as e:
        logger.error(f"Error in text_to_speech_processor: {e}")
        audio_queue.put(None)

async def audio_sender(audio_queue: queue.Queue, stop_event: Event):
    try:
        logger.info("Audio sender started.")
        while not stop_event.is_set():
            audio_data = await asyncio.get_event_loop().run_in_executor(None, audio_queue.get)
            if audio_data is None:
                logger.info("Audio sender ended.")
                break
            if not audio_data:
                # Skip sending empty audio data
                continue
            if connection_manager.active_connection:
                await connection_manager.send_audio(audio_data)
            else:
                logger.warning("No active WebSocket connection to send audio.")
    except Exception as e:
        logger.error(f"Error in audio_sender: {e}")

async def audio_player(audio_queue: queue.Queue, tts_constants, stop_event: Event):
    try:
        logger.info("Backend audio player started.")
        # Initialize PyAudio
        p = pyaudio.PyAudio()
        # Configure audio stream based on RESPONSE_FORMAT
        stream = p.open(format=pyaudio.paInt16,
                        channels=tts_constants["CHANNELS"],
                        rate=tts_constants["RATE"],
                        output=True)
        while not stop_event.is_set():
            audio_data = await asyncio.get_event_loop().run_in_executor(None, audio_queue.get)
            if audio_data is None:
                logger.info("Audio player ended.")
                break
            if not audio_data:
                # Skip empty audio data
                continue
            # Play the audio data
            stream.write(audio_data)
        # Clean up
        stream.stop_stream()
        stream.close()
        p.terminate()
    except Exception as e:
        logger.error(f"Error in audio_player: {e}")
