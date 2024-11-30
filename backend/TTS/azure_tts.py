import asyncio
import logging
import azure.cognitiveservices.speech as speechsdk
from backend.config.clients import get_azure_speech_config

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class PushAudioOutputStreamCallback(speechsdk.audio.PushAudioOutputStreamCallback):
    def __init__(self, audio_queue: asyncio.Queue):
        super().__init__()
        self.audio_queue = audio_queue
        self.loop = asyncio.get_event_loop()

    def write(self, data: memoryview) -> int:
        # Schedule the put_nowait call in the event loop
        self.loop.call_soon_threadsafe(self.audio_queue.put_nowait, data.tobytes())
        return len(data)

    def close(self):
        # Schedule the put_nowait call in the event loop
        self.loop.call_soon_threadsafe(self.audio_queue.put_nowait, None)

def create_ssml(phrase: str, voice: str, prosody: dict) -> str:
    return f"""
<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='en-US'>
    <voice name='{voice}'>
        <prosody rate='{prosody["rate"]}' pitch='{prosody["pitch"]}' volume='{prosody["volume"]}'>
            {phrase}
        </prosody>
    </voice>
</speak>
"""

async def azure_text_to_speech_processor(phrase_queue: asyncio.Queue, audio_queue: asyncio.Queue):
    try:
        # Fetch Azure configuration
        logger.debug(f"Fetching Azure SpeechConfig...")
        speech_config = get_azure_speech_config()
        
        from backend.config import Config
        prosody = Config.AZURE_PROSODY
        voice = Config.AZURE_TTS_VOICE
        audio_format = getattr(speechsdk.SpeechSynthesisOutputFormat, Config.AZURE_AUDIO_FORMAT)
        speech_config.set_speech_synthesis_output_format(audio_format)

        while True:
            phrase = await phrase_queue.get()
            if phrase is None:
                logger.info("Terminating Azure TTS processing.")
                await audio_queue.put(None)
                return

            try:
                logger.info(f"Processing phrase: {phrase}")
                ssml_phrase = create_ssml(phrase, voice, prosody)
                logger.debug(f"Generated SSML: {ssml_phrase}")

                push_stream_callback = PushAudioOutputStreamCallback(audio_queue)
                push_stream = speechsdk.audio.PushAudioOutputStream(push_stream_callback)
                audio_config = speechsdk.audio.AudioOutputConfig(stream=push_stream)

                synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
                result_future = synthesizer.speak_ssml_async(ssml_phrase)
                await asyncio.get_event_loop().run_in_executor(None, result_future.get)
            except Exception as e:
                logger.error(f"Error during Azure TTS processing: {e}")
                await audio_queue.put(None)
    except Exception as e:
        logger.error(f"Unexpected error in Azure TTS processor: {e}")
        await audio_queue.put(None)
