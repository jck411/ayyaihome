import asyncio
import queue
import logging

from backend.config.config import Config
from backend.TTS.openai_tts import text_to_speech_processor as openai_text_to_speech_processor
from backend.TTS.azure_tts import azure_text_to_speech_processor
from backend.audio_players.pyaudio import start_audio_player

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def process_streams(phrase_queue: asyncio.Queue, audio_queue: queue.Queue):
    """
    Manages the processing of text-to-speech and audio playback.
    Dynamically selects TTS processor (OpenAI or Azure) and playback rate based on configuration.
    """
    try:
        logger.info("Starting process_streams...")

        # Determine which TTS processor to use
        tts_processor = None

        logger.info(f"Configured TTS Provider: {Config.TTS_PROVIDER}")

        # Dynamically set playback rate based on TTS_PROVIDER
        if Config.TTS_PROVIDER.lower() == "openai":
            tts_processor = openai_text_to_speech_processor
            playback_rate = Config.OPENAI_PLAYBACK_RATE
            logger.info("Using OpenAI TTS processor.")
        elif Config.TTS_PROVIDER.lower() == "azure":
            tts_processor = azure_text_to_speech_processor
            playback_rate = Config.AZURE_PLAYBACK_RATE
            logger.info("Using Azure TTS processor.")
        else:
            raise ValueError(f"Unsupported TTS provider: {Config.TTS_PROVIDER}")

        # Log the playback rate
        logger.info(f"Playback rate: {playback_rate}")

        # Start the TTS processor task
        logger.debug("Starting TTS processor task...")
        tts_task = asyncio.create_task(tts_processor(phrase_queue, audio_queue))

        # Start the audio player with the correct playback rate
        logger.debug("Starting audio player...")
        start_audio_player(audio_queue, playback_rate)

        # Wait for the TTS task to complete
        logger.debug("Waiting for the TTS task to complete...")
        await tts_task
        logger.info("TTS task completed successfully.")

    except Exception as e:
        logger.error(f"Error in process_streams: {e}")
