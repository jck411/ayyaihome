import asyncio
import queue
import logging
import azure.cognitiveservices.speech as speechsdk
from backend.config import Config, get_azure_speech_config

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
    """
    azure_config = Config.TTS_MODELS['AZURE_TTS']
    prosody = azure_config['PROSODY']
    rate = prosody['rate']
    pitch = prosody['pitch']
    volume = prosody['volume']
    voice_name = azure_config['TTS_VOICE']

    ssml = f"""
<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='en-US'>
    <voice name='{voice_name}'>
        <prosody rate='{rate}' pitch='{pitch}' volume='{volume}'>
            {phrase}
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

                # Retrieve and set the audio format from configuration
                azure_config = Config.TTS_MODELS['AZURE_TTS']
                audio_format_str = azure_config.get('AUDIO_FORMAT', 'Audio16Khz32KBitRateMonoMp3')
                try:
                    audio_format = getattr(speechsdk.SpeechSynthesisOutputFormat, audio_format_str)
                    speech_config.set_speech_synthesis_output_format(audio_format)
                    logger.info(f"Set audio format to: {audio_format_str}")
                except AttributeError:
                    logger.error(f"Invalid audio format: {audio_format_str}. Using default format.")

                # Create SSML with prosody adjustments
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
    except Exception as e:
        logger.error(f"Error in TTS processing: {e}")
        audio_queue.put(None)
