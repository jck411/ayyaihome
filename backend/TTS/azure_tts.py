import asyncio
import queue
import azure.cognitiveservices.speech as speechsdk
from backend.config import Config, get_azure_speech_config

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
    return ssml

async def azure_text_to_speech_processor(
    phrase_queue: asyncio.Queue,
    audio_queue: queue.Queue,
):
    try:
        while True:
            phrase = await phrase_queue.get()
            if phrase is None:
                audio_queue.put(None)
                return

            try:
                # Initialize Speech Config
                speech_config = get_azure_speech_config()

                # Retrieve and set the audio format from configuration
                azure_config = Config.TTS_MODELS['AZURE_TTS']
                audio_format_str = azure_config.get('AUDIO_FORMAT', 'Audio16Khz32KBitRateMonoMp3')
                audio_format = getattr(speechsdk.SpeechSynthesisOutputFormat, audio_format_str)
                speech_config.set_speech_synthesis_output_format(audio_format)

                # Create SSML with prosody adjustments
                ssml_phrase = create_ssml(phrase)

                # Set up push audio output stream with the callback
                push_stream_callback = PushAudioOutputStreamCallback(audio_queue)
                push_stream = speechsdk.audio.PushAudioOutputStream(push_stream_callback)
                audio_config = speechsdk.audio.AudioOutputConfig(stream=push_stream)
                synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

                # Synthesize speech using SSML without blocking
                result_future = synthesizer.speak_ssml_async(ssml_phrase)
                # Do not call .get() here; allow the callback to handle audio data

                # Optionally, you can await the result if needed
                await asyncio.get_event_loop().run_in_executor(None, result_future.get)
            except Exception:
                pass
    except Exception:
        audio_queue.put(None)
