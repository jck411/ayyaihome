import asyncio
import logging
from typing import Optional

from init import aclient, SHARED_CONSTANTS, connection_manager
from services.audio_player import start_audio_player
from services.tts_manager import tts_manager  # Import the TTSManager

logger = logging.getLogger(__name__)

# Sentinel object to signal end of processing
END_OF_PROCESSING = object()

async def process_streams(phrase_queue: asyncio.Queue, audio_queue: asyncio.Queue, tts_constants: dict):
    """
    Processes the audio streams by converting phrases to speech and handling playback.
    """
    try:
        # Ensure no previous TTS task is running
        await tts_manager.stop_active_tts()

        if SHARED_CONSTANTS.get("FRONTEND_PLAYBACK", False):
            audio_sender_task = asyncio.create_task(audio_sender(audio_queue))
            tts_manager.register_task(audio_sender_task)  # Register the task with the TTS manager
        else:
            start_audio_player(audio_queue)

        # Start TTS processing
        tts_task = asyncio.create_task(text_to_speech_processor(phrase_queue, audio_queue, tts_constants))
        tts_manager.register_task(tts_task)  # Register the TTS task with the TTS manager

        await tts_task  # Await completion of TTS processing
        await audio_queue.put(END_OF_PROCESSING)

        if SHARED_CONSTANTS.get("FRONTEND_PLAYBACK", False):
            await audio_sender_task  # Await audio sending task completion

        # Clear the active task once processing is complete
        tts_manager.clear_task()

    except asyncio.CancelledError:
        logger.info("process_streams task was cancelled.")
        await audio_queue.put(END_OF_PROCESSING)
        await tts_manager.stop_active_tts()  # Ensure active TTS tasks are stopped on cancellation
        raise
    except Exception as e:
        logger.error(f"Error in process_streams: {e}")
        await audio_queue.put(END_OF_PROCESSING)
        await tts_manager.stop_active_tts()  # Ensure active TTS tasks are stopped on error

async def text_to_speech_processor(phrase_queue: asyncio.Queue, audio_queue: asyncio.Queue, tts_constants: dict):
    """
    Converts text phrases to speech and enqueues audio data for playback or sending.
    Accumulates audio data in chunks based on the provided tts_constants.
    """
    try:
        while True:
            phrase = await phrase_queue.get()
            if phrase is None:
                logger.info("Received stop signal. Exiting TTS processor.")
                return

            try:
                logger.info(f"Processing phrase: {phrase}")
                
                # Fetch audio data in chunks
                async with aclient.audio.speech.with_streaming_response.create(
                    model=tts_constants["DEFAULT_TTS_MODEL"],
                    voice=tts_constants["DEFAULT_VOICE"],
                    input=phrase,
                    speed=tts_constants["TTS_SPEED"],
                    response_format=tts_constants.get("RESPONSE_FORMAT")
                ) as response:
                    audio_data = b""
                    # Iterate over the response chunks and accumulate audio data
                    async for audio_chunk in response.iter_bytes(tts_constants.get("TTS_CHUNK_SIZE", 1024)):
                        audio_data += audio_chunk
                    # Enqueue the accumulated audio data
                    await audio_queue.put(audio_data)
                    logger.info(f"Enqueued audio data for phrase.")
            except asyncio.CancelledError:
                logger.info("text_to_speech_processor was cancelled.")
                await audio_queue.put(END_OF_PROCESSING)
                raise
            except Exception as tts_error:
                logger.error(f"TTS processing failed with error: {tts_error}")
                await audio_queue.put(END_OF_PROCESSING)
                break
    except asyncio.CancelledError:
        logger.info("text_to_speech_processor was cancelled.")
        await audio_queue.put(END_OF_PROCESSING)
        raise
    except Exception as e:
        logger.error(f"Error in text_to_speech_processor: {e}")
        await audio_queue.put(END_OF_PROCESSING)

async def audio_sender(audio_queue: asyncio.Queue):
    """
    Sends audio data over WebSocket to the frontend.
    """
    try:
        logger.info("Audio sender started.")
        while True:
            audio_data = await asyncio.wait_for(audio_queue.get(), timeout=10.0)
            
            if audio_data is END_OF_PROCESSING:
                logger.info("Audio sender ended.")
                break
            if audio_data:
                await connection_manager.send_audio(audio_data)
    except asyncio.TimeoutError:
        logger.error("Audio sender timed out waiting for audio data.")
    except asyncio.CancelledError:
        logger.info("audio_sender was cancelled.")
        raise
    except Exception as e:
        logger.error(f"Error in audio_sender: {e}")
        await audio_queue.put(END_OF_PROCESSING)
