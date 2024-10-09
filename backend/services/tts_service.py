# /home/jack/ayyaihome/backend/services/tts_service.py

import asyncio
import logging
import queue
from init import aclient, SHARED_CONSTANTS, connection_manager, pyaudio
from services.audio_player import start_audio_player  # Import start_audio_player

logger = logging.getLogger(__name__)

# Main function to process audio streams based on configuration
async def process_streams(phrase_queue: asyncio.Queue, audio_queue: queue.Queue, tts_constants):
    """
    Processes the audio streams by converting phrases to speech and handling playback.
    """
    try:
        if SHARED_CONSTANTS.get("FRONTEND_PLAYBACK", False):
            # If FRONTEND_PLAYBACK is enabled, send audio via WebSocket
            audio_sender_task = asyncio.create_task(audio_sender(audio_queue))
            await text_to_speech_processor(phrase_queue, audio_queue, tts_constants)
            audio_queue.put(None)  # Signal the end of audio processing
            await audio_sender_task
        else:
            # If FRONTEND_PLAYBACK is not enabled, play audio locally
            start_audio_player(audio_queue)  # Start audio player in a separate thread
            await text_to_speech_processor(phrase_queue, audio_queue, tts_constants)
            audio_queue.put(None)  # Signal the end of audio processing
            # No need to await audio_player_task, as it runs in separate thread

    except asyncio.CancelledError:
        logger.info("process_streams task was cancelled.")
        # Signal the end of audio processing
        audio_queue.put(None)
        raise
    except Exception as e:
        logger.error(f"Error in process_streams: {e}")
        audio_queue.put(None)

# Function to process text-to-speech requests
async def text_to_speech_processor(phrase_queue: asyncio.Queue, audio_queue: queue.Queue, tts_constants):
    """
    Converts text phrases to speech and enqueues audio data for playback or sending.
    """
    try:
        while True:
            # Get the next phrase from the queue
            phrase = await phrase_queue.get()
            if phrase is None:
                logger.info("Received stop signal. Exiting TTS processor.")
                return
            try:
                logger.info(f"Processing phrase: {phrase}")
                # Create a streaming response for the given phrase
                async with aclient.audio.speech.with_streaming_response.create(
                    model=tts_constants["DEFAULT_TTS_MODEL"],
                    voice=tts_constants["DEFAULT_VOICE"],
                    input=phrase,
                    speed=tts_constants["TTS_SPEED"],
                    response_format=tts_constants["RESPONSE_FORMAT"]
                ) as response:
                    audio_data = b""
                    # Iterate over the response chunks and accumulate audio data
                    async for audio_chunk in response.iter_bytes(tts_constants["TTS_CHUNK_SIZE"]):
                        audio_data += audio_chunk
                    # Enqueue the audio data for further processing (playback or sending)
                    audio_queue.put(audio_data)
                    logger.info(f"Enqueued audio data for phrase.")
            except asyncio.CancelledError:
                logger.info("text_to_speech_processor was cancelled.")
                audio_queue.put(None)
                raise
            except Exception as tts_error:
                logger.error(f"TTS processing failed with error: {tts_error}")
                audio_queue.put(None)  # Signal an error occurred
                break  # Exit on TTS error
    except asyncio.CancelledError:
        logger.info("text_to_speech_processor was cancelled.")
        audio_queue.put(None)
        raise
    except Exception as e:
        logger.error(f"Error in text_to_speech_processor: {e}")
        audio_queue.put(None)  # Signal an error occurred

# Function to send audio data via WebSocket
async def audio_sender(audio_queue: queue.Queue):
    """
    Sends audio data over WebSocket to the frontend.
    """
    try:
        logger.info("Audio sender started.")
        while True:
            # Get the next audio data from the queue (blocking call executed in a thread pool)
            audio_data = await asyncio.get_event_loop().run_in_executor(None, audio_queue.get)
            if audio_data is None:
                logger.info("Audio sender ended.")
                break
            if not audio_data:
                # Skip sending empty audio data
                continue
            # Send audio data via ConnectionManager
            await connection_manager.send_audio(audio_data)
    except asyncio.CancelledError:
        logger.info("audio_sender was cancelled.")
        raise
    except Exception as e:
        logger.error(f"Error in audio_sender: {e}")
        audio_queue.put(None)  # Signal an error occurred
