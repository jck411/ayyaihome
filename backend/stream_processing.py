# backend/stream_processing.py

import asyncio
import queue
import logging

from backend.TTS.openai_tts import openai_text_to_speech_processor
from backend.TTS.azure_tts import azure_text_to_speech_processor
from backend.audio_players.pyaudio import start_audio_player
from backend.config import Config

logger = logging.getLogger(__name__)

async def process_streams(phrase_queue: asyncio.Queue, audio_queue: queue.Queue, request_timestamp: float):
    """
    Manages the processing of text-to-speech and audio playback.

    Args:
        phrase_queue (asyncio.Queue): Queue containing phrases to process.
        audio_queue (queue.Queue): Queue to send audio data.
        request_timestamp (float): Timestamp when the request was received.
    """
    try:
        # Select the TTS processor based on configuration
        if Config.TTS_PROVIDER.lower() == "openai":
            tts_processor = openai_text_to_speech_processor
            logger.info("Selected OpenAI TTS processor.")
        elif Config.TTS_PROVIDER.lower() == "azure":
            tts_processor = azure_text_to_speech_processor
            logger.info("Selected Azure TTS processor.")
        else:
            raise ValueError(f"Unsupported TTS provider: {Config.TTS_PROVIDER}")

        # Start the TTS processor task
        tts_task = asyncio.create_task(
            tts_processor(
                phrase_queue=phrase_queue,
                audio_queue=audio_queue
            )
        )
        logger.info("TTS processor task started.")

        # Get playback rate from configuration
        playback_rate = Config.get_playback_rate()

        # Start the audio player
        start_audio_player(audio_queue, request_timestamp, playback_rate)
        logger.info(f"Audio player started with playback rate: {playback_rate} Hz.")

        # Wait for the TTS task to complete
        await tts_task
        logger.info("TTS processor task completed.")

    except Exception as e:
        logger.error(f"Error in processing streams: {e}")
