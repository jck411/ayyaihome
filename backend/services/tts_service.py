# /home/jack/ayyaihome/backend/services/tts_service.py

import asyncio
import logging
from init import stop_event, aclient, SHARED_CONSTANTS
from services.audio_player import start_audio_player
import queue
from pydub import AudioSegment
from pydub.utils import which
import io
import opuslib

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Set to DEBUG for more granular logs
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ensure pydub can find ffmpeg
AudioSegment.converter = which("ffmpeg")
if AudioSegment.converter is None:
    logger.error("ffmpeg not found. Please ensure ffmpeg is installed and in your PATH.")
    raise EnvironmentError("ffmpeg not found. Please install ffmpeg and add it to your PATH.")

async def decode_opus(opus_data: bytes) -> bytes:
    """
    Decodes raw Opus audio data to PCM using opuslib.
    """
    try:
        # Initialize the Opus decoder with sample rate and channels
        decoder = opuslib.Decoder(SHARED_CONSTANTS["RATE"], SHARED_CONSTANTS["CHANNELS"])
        # Decode the entire Opus data
        pcm_data = decoder.decode(opus_data, frame_size=960, decode_fec=False)  # 20ms at 48kHz
        return pcm_data
    except opuslib.OpusError as e:
        logger.error(f"opuslib decoding failed: {e}")
        raise RuntimeError(f"opuslib decoding failed: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during Opus decoding: {e}")
        raise RuntimeError(f"Unexpected error during Opus decoding: {e}")

async def enqueue_phrase(phrase_queue: asyncio.Queue, text: str):
    """
    Enqueues a phrase for TTS processing.
    """
    await phrase_queue.put(text)
    logger.info(f"Enqueued phrase with text: '{text}'")

async def text_to_speech_processor(phrase_queue: asyncio.Queue, audio_queue: queue.Queue, tts_constants):
    """
    Processes phrases into speech using OpenAI's TTS model.
    Streams audio chunks to the audio queue for playback.
    """
    try:
        while not stop_event.is_set():
            phrase = await phrase_queue.get()

            if phrase is None:
                audio_queue.put(None)
                logger.info("Received stop signal. Exiting TTS processor.")
                return

            try:
                # Send the phrase to OpenAI's TTS API with appropriate constants
                async with aclient.audio.speech.with_streaming_response.create(
                    model=tts_constants["DEFAULT_TTS_MODEL"],
                    voice=tts_constants["DEFAULT_VOICE"],
                    input=phrase,
                    speed=tts_constants["TTS_SPEED"],
                    response_format=tts_constants["RESPONSE_FORMAT"]  # Use the configurable format
                ) as response:
                    audio_data = b""
                    async for audio_chunk in response.iter_bytes(tts_constants["TTS_CHUNK_SIZE"]):
                        if stop_event.is_set():
                            logger.info("Stop event detected. Terminating TTS processing.")
                            return
                        audio_data += audio_chunk

                    # Handle decoding for compressed formats
                    if tts_constants["RESPONSE_FORMAT"] in ["opus", "mp3", "aac"]:
                        try:
                            # Use pydub's AudioSegment for decoding
                            format_map = {
                                "opus": "ogg",
                                "mp3": "mp3",
                                "aac": "aac"
                            }
                            audio_format = format_map.get(tts_constants["RESPONSE_FORMAT"], "pcm")
                            logger.debug(f"Decoding {tts_constants['RESPONSE_FORMAT'].upper()} format using pydub.")
                            audio_segment = AudioSegment.from_file(io.BytesIO(audio_data), format=audio_format)
                            raw_data = audio_segment.raw_data

                            # Enqueue the raw PCM data for playback
                            audio_queue.put(raw_data)
                            logger.info(f"Successfully decoded and enqueued audio for format {tts_constants['RESPONSE_FORMAT']}.")
                        except Exception as decode_error:
                            logger.error(f"Decoding failed for format {tts_constants['RESPONSE_FORMAT']}: {decode_error}")
                            audio_queue.put(None)
                    else:
                        # For PCM formats, stream directly
                        audio_queue.put(audio_data)
                        logger.info("Enqueued PCM audio data directly for playback.")

                # Insert a short pause between phrases (optional)
                audio_queue.put(b'\x00' * 2400)
                logger.debug("Inserted a short pause between phrases.")
            except Exception as tts_error:
                logger.error(f"TTS processing failed with error: {tts_error}")
                audio_queue.put(None)

    except Exception as e:
        logger.error(f"Error in text_to_speech_processor: {e}")
        audio_queue.put(None)
             



async def process_streams(phrase_queue: asyncio.Queue, audio_queue: queue.Queue, tts_constants):
    """
    Manages the processing of text-to-speech and audio playback using OpenAI TTS.
    """
    tts_task = asyncio.create_task(text_to_speech_processor(phrase_queue, audio_queue, tts_constants))
    start_audio_player(audio_queue)
    await tts_task
