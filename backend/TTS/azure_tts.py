import asyncio
import queue
import logging
import os
import azure.cognitiveservices.speech as speechsdk
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path="/home/jack/ayyaihome/backend/.env")

# Azure credentials
AZURE_SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")
AZURE_REGION = os.getenv("AZURE_REGION")

if not all([AZURE_SPEECH_KEY, AZURE_REGION]):
    raise EnvironmentError("Missing required Azure TTS environment variables.")

# Default settings
DEFAULT_VOICE_NAME = "en-US-LewisMultilingualNeural" # Replace with your desired Azure voice
DEFAULT_TTS_SPEED = "1.0"  # Speech speed (default: normal)
DEFAULT_SAMPLE_RATE = 16000  # Ensure sample rate matches Azure TTS output (16 kHz)
DEFAULT_CHUNK_SIZE = DEFAULT_SAMPLE_RATE * 2  # 2400 bytes equivalent to 16-bit PCM mono

# Initialize logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class PushAudioOutputStreamCallback(speechsdk.audio.PushAudioOutputStreamCallback):
    """
    A callback mechanism to handle real-time audio streaming.
    Audio data is pushed to the provided audio queue.
    """

    def __init__(self, audio_queue: queue.Queue):
        super().__init__()
        self.audio_queue = audio_queue

    def write(self, audio_buffer: memoryview) -> int:
        """
        Called by Azure Speech SDK when audio data is available.
        Pushes the audio data to the queue.
        """
        self.audio_queue.put(audio_buffer.tobytes())
        return audio_buffer.nbytes

    def close(self):
        """
        Called when the audio stream is closed.
        """
        self.audio_queue.put(None)
        logger.info("Audio stream closed.")


def get_silent_chunk(delimiter: str) -> bytes:
    """
    Returns a silent chunk based on the delimiter to dynamically adjust pause duration.
    """
    base_rate = 16000  # Sample rate (16 kHz)
    duration = 0.5  # Default pause duration in seconds

    if delimiter == '.':
        duration = 0.3  # Shorter pause for periods
    elif delimiter == ',':
        duration = 0.2  # Even shorter pause for commas
    elif delimiter == '?':
        duration = 0.4  # Slightly longer pause for questions
    elif delimiter == '!':
        duration = 0.5  # Standard pause for exclamations

    # Calculate chunk size based on duration
    chunk_size = int(base_rate * 2 * duration)  # 16-bit PCM
    return b'\x00' * chunk_size


async def azure_text_to_speech_processor(
    phrase_queue: asyncio.Queue,
    audio_queue: queue.Queue,
    speech_config: Optional[speechsdk.SpeechConfig] = None,
):
    """
    Converts phrases from the phrase queue into speech using Azure TTS and sends audio to the audio queue.
    """
    if speech_config is None:
        speech_config = speechsdk.SpeechConfig(subscription=AZURE_SPEECH_KEY, region=AZURE_REGION)
        speech_config.speech_synthesis_voice_name = DEFAULT_VOICE_NAME
        speech_config.speech_synthesis_rate = DEFAULT_TTS_SPEED

        # Explicitly set output format to match playback configuration
        speech_config.set_speech_synthesis_output_format(
            speechsdk.SpeechSynthesisOutputFormat.Raw16Khz16BitMonoPcm
        )

    try:
        while True:
            # Get a phrase from the queue
            phrase = await phrase_queue.get()
            if phrase is None:
                # Signal that processing is complete
                audio_queue.put(None)
                logger.info("TTS processing complete.")
                return

            try:
                # Set up push audio output stream
                push_stream_callback = PushAudioOutputStreamCallback(audio_queue)
                push_stream = speechsdk.audio.PushAudioOutputStream(push_stream_callback)
                audio_config = speechsdk.audio.AudioOutputConfig(stream=push_stream)
                synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

                # Synthesize speech
                logger.info(f"Processing phrase: {phrase}")
                result = synthesizer.speak_text_async(phrase).get()

                if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                    logger.info("TTS synthesis completed successfully.")
                elif result.reason == speechsdk.ResultReason.Canceled:
                    details = result.cancellation_details
                    logger.error(f"TTS canceled: {details.reason} - {details.error_details}")
                else:
                    logger.error("Unknown TTS error occurred.")
            except Exception as e:
                logger.error(f"Error processing phrase '{phrase}': {e}")

            # Determine the appropriate silent chunk based on the phrase ending
            last_char = phrase.strip()[-1] if phrase.strip() else ''
            silent_chunk = get_silent_chunk(last_char)
            audio_queue.put(silent_chunk)
            logger.info(f"Added silent audio chunk for delimiter '{last_char}'.")
    except Exception as e:
        logger.error(f"Error in TTS processing: {e}")
        audio_queue.put(None)
