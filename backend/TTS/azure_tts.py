import asyncio
import queue
import logging
import re
from typing import Optional
import azure.cognitiveservices.speech as speechsdk
from backend.config import Config, get_azure_speech_config

# Initialize logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def get_config_value(config: dict, key: str, parent_key: str = ""):
    """
    Fetches a configuration value and ensures it exists.
    Raises a KeyError with a descriptive error message if the key is missing.
    """
    if key not in config:
        full_key = f"{parent_key}.{key}" if parent_key else key
        logger.error(f"Configuration key missing: {full_key}")
        raise KeyError(f"Missing required configuration: '{full_key}'. Please set it in the config.")
    return config[key]


class PushAudioOutputStreamCallback(speechsdk.audio.PushAudioOutputStreamCallback):
    """
    A callback mechanism to handle real-time audio streaming.
    Audio data is pushed to the provided audio queue.
    """

    def __init__(self, audio_queue: queue.Queue):
        super().__init__()
        self.audio_queue = audio_queue

    def write(self, data: memoryview) -> int:
        """
        Called by Azure Speech SDK when audio data is available.
        Pushes the audio data to the queue.
        """
        self.audio_queue.put(data.tobytes())
        return len(data)

    def close(self):
        """
        Called when the audio stream is closed.
        """
        self.audio_queue.put(None)
        logger.info("Audio stream closed.")


def create_ssml(phrase: str) -> str:
    """
    Wraps the phrase in SSML to adjust prosody (rate, pitch, volume) as per configuration.
    Inserts <break> tags based on DYNAMIC_PAUSES settings.
    """
    azure_config = Config.TTS_MODELS['AZURE_TTS']
    prosody = get_config_value(azure_config, 'PROSODY', 'TTS_MODELS.AZURE_TTS')
    rate = get_config_value(prosody, 'rate', 'TTS_MODELS.AZURE_TTS.PROSODY')
    pitch = get_config_value(prosody, 'pitch', 'TTS_MODELS.AZURE_TTS.PROSODY')
    volume = get_config_value(prosody, 'volume', 'TTS_MODELS.AZURE_TTS.PROSODY')
    voice_name = get_config_value(azure_config, 'TTS_VOICE', 'TTS_MODELS.AZURE_TTS')
    dynamic_pauses = get_config_value(azure_config, 'DYNAMIC_PAUSES', 'TTS_MODELS.AZURE_TTS')
    delimiter_map = get_config_value(azure_config, 'DELIMITER_MAP', 'TTS_MODELS.AZURE_TTS')

    # Build a regex pattern from the delimiters
    delimiters_pattern = '[' + re.escape(''.join(delimiter_map.keys())) + ']'

    # Function to replace delimiters with themselves and a break tag if needed
    def replace_delimiter(match):
        delimiter = match.group(0)
        config_key = delimiter_map[delimiter]
        duration = get_config_value(dynamic_pauses, config_key, 'TTS_MODELS.AZURE_TTS.DYNAMIC_PAUSES')
        duration_ms = int(duration * 1000)  # Convert seconds to milliseconds
        if duration_ms > 0:
            return f"{delimiter}<break time='{duration_ms}ms'/>"
        else:
            return delimiter  # No break tag if duration is zero

    # Apply the replacement to the phrase
    phrase_with_breaks = re.sub(delimiters_pattern, replace_delimiter, phrase)

    ssml = f"""
<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='en-US'>
    <voice name='{voice_name}'>
        <prosody rate='{rate}' pitch='{pitch}' volume='{volume}'>
            {phrase_with_breaks}
        </prosody>
    </voice>
</speak>
"""
    logger.debug(f"Generated SSML: {ssml}")
    return ssml


async def azure_text_to_speech_processor(
    phrase_queue: asyncio.Queue,
    audio_queue: queue.Queue,
):
    """
    Converts phrases from the phrase queue into speech using Azure TTS and sends audio to the audio queue.
    """
    try:
        while True:
            phrase = await phrase_queue.get()
            if phrase is None:
                # Signal that processing is complete
                audio_queue.put(None)
                logger.info("TTS processing complete.")
                return

            try:
                # Initialize Speech Config
                speech_config = get_azure_speech_config()

                # Optional: Enable profanity filter (implement if needed)
                if Config.TTS_MODELS['AZURE_TTS'].get('ENABLE_PROFANITY_FILTER', False):
                    logger.warning("Profanity filter is enabled but not implemented.")
                    # Implement profanity filtering here if required

                # Create SSML with prosody adjustments and dynamic pauses
                ssml_phrase = create_ssml(phrase)

                # Set up push audio output stream with the callback
                push_stream_callback = PushAudioOutputStreamCallback(audio_queue)
                push_stream = speechsdk.audio.PushAudioOutputStream(push_stream_callback)
                audio_config = speechsdk.audio.AudioOutputConfig(stream=push_stream)
                synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

                # Synthesize speech using SSML
                logger.info(f"Processing phrase: {phrase}")
                result = synthesizer.speak_ssml_async(ssml_phrase).get()

                if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                    logger.info("TTS synthesis completed successfully.")
                elif result.reason == speechsdk.ResultReason.Canceled:
                    details = result.cancellation_details
                    logger.error(f"TTS canceled: {details.reason} - {details.error_details}")
                else:
                    logger.error("Unknown TTS error occurred.")
            except Exception as e:
                logger.error(f"Error processing phrase '{phrase}': {e}")

            # No silent chunk addition here; pauses are handled via SSML
    except Exception as e:
        logger.error(f"Error in TTS processing: {e}")
        audio_queue.put(None)
