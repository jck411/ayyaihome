import asyncio
import queue
import logging
from backend.TTS.openai_tts import text_to_speech_processor
from backend.audio_players.pyaudio import start_audio_player

logger = logging.getLogger(__name__)

async def process_streams(
    phrase_queue: asyncio.Queue,
    audio_queue: queue.Queue,
    request_timestamp: float
):
    """
    Manages the processing of text-to-speech and audio playback.
    """
    try:
        # Start text-to-speech processing as a task
        tts_task = asyncio.create_task(text_to_speech_processor(phrase_queue, audio_queue))
        
        # Start audio player to handle the audio queue
        start_audio_player(audio_queue, request_timestamp)
        
        # Wait until text-to-speech processing is complete
        await tts_task
    except Exception as e:
        logger.error(f"Error in processing streams: {e}")
