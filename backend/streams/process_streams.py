import asyncio
import logging
from backend.TTS.openai_tts import text_to_speech_processor
from backend.audio_players.pyaudio import start_audio_player

logger = logging.getLogger(__name__)

async def start_stream_processing(
    phrase_queue: asyncio.Queue,
    audio_queue: asyncio.Queue,
    request_timestamp: float
):
    """
    Manages the processing of text-to-speech and audio playback.
    """
    try:
        tts_task = asyncio.create_task(text_to_speech_processor(phrase_queue, audio_queue))
        start_audio_player(audio_queue, request_timestamp)
        await tts_task
    except Exception as e:
        logger.error(f"Error in processing streams: {e}")
