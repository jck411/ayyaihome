import asyncio
import queue
import logging
from backend.TTS.openai_tts import text_to_speech_processor as openai_text_to_speech_processor
from backend.TTS.azure_tts import azure_text_to_speech_processor
from backend.audio_players.pyaudio import start_audio_player
from backend.config import Config

# Initialize logging
logger = logging.getLogger(__name__)

async def process_streams(phrase_queue: asyncio.Queue, audio_queue: queue.Queue, request_timestamp: float):
    """
    Manages the processing of text-to-speech and audio playback.
    Dynamically selects TTS processor (OpenAI or Azure) and playback rate based on configuration.
    """
    try:
        # Determine which TTS processor to use
        tts_processor = None
        playback_rate = Config.get_playback_rate()

        if Config.TTS_PROVIDER == "openai":
            logger.info("Using OpenAI TTS processor.")
            tts_processor = openai_text_to_speech_processor
        elif Config.TTS_PROVIDER == "azure":
            logger.info("Using Azure TTS processor.")
            tts_processor = azure_text_to_speech_processor
        else:
            raise ValueError(f"Unsupported TTS provider: {Config.TTS_PROVIDER}")

        logger.info(f"Selected playback rate: {playback_rate} Hz")

        # Start the TTS processor task
        tts_task = asyncio.create_task(tts_processor(phrase_queue, audio_queue))

        # Start the audio player with the correct playback rate
        start_audio_player(audio_queue, request_timestamp, playback_rate)

        # Wait for the TTS task to complete
        await tts_task
    except Exception as e:
        logger.error(f"Error in processing streams: {e}")
