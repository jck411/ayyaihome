import asyncio
from backend.TTS.openai_tts import text_to_speech_processor as openai_text_to_speech_processor
from backend.TTS.azure_tts import azure_text_to_speech_processor
from backend.audio_players.pyaudio import start_audio_player_async
from backend.config import Config
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def process_streams(phrase_queue: asyncio.Queue, audio_queue: asyncio.Queue):
    """
    Manages the processing of text-to-speech and audio playback.
    Dynamically selects TTS processor (OpenAI or Azure) based on configuration.
    """
    try:
        # Determine which TTS processor to use and retrieve playback rate
        if Config.TTS_PROVIDER.lower() == "openai":
            tts_processor = openai_text_to_speech_processor
            playback_rate = Config.OPENAI_PLAYBACK_RATE
            logger.info(f"Selected TTS Provider: OpenAI with playback rate {playback_rate} Hz")
        elif Config.TTS_PROVIDER.lower() == "azure":
            tts_processor = azure_text_to_speech_processor
            playback_rate = Config.AZURE_PLAYBACK_RATE
            logger.info(f"Selected TTS Provider: Azure with playback rate {playback_rate} Hz")
        else:
            raise ValueError(f"Unsupported TTS provider: {Config.TTS_PROVIDER}")

        # Get the current event loop
        loop = asyncio.get_running_loop()

        # Start the TTS processor task
        tts_task = asyncio.create_task(tts_processor(phrase_queue, audio_queue))

        # Start the audio player as an async task with playback_rate and loop
        audio_player_task = asyncio.create_task(start_audio_player_async(audio_queue, playback_rate, loop))

        # Wait for both tasks to complete
        await asyncio.gather(tts_task, audio_player_task)
    except Exception as e:
        # Handle exceptions appropriately
        logger.error(f"Error in process_streams: {e}")
