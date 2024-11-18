import asyncio
import queue
import logging
import azure.cognitiveservices.speech as speechsdk
from backend.config import Config, get_azure_speech_config
import stanza
import nltk

# Initialize logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


# Function to initialize tokenizers based on configuration
def initialize_tokenizers():
    """
    Initializes NLTK and Stanza resources based on the configuration.
    """
    tokenizer = Config.TTS_MODELS['AZURE_TTS']['TOKENIZER']  # Mandatory configuration
    if tokenizer == "NLTK":
        nltk.download('punkt', quiet=True)
    elif tokenizer == "STANZA":
        stanza.download('en')
        return stanza.Pipeline(lang='en', processors='tokenize')
    elif tokenizer == "NONE":
        return None
    else:
        raise ValueError(f"Unsupported tokenizer: {tokenizer}")


# Initialize the appropriate tokenizer (STANZA or NONE)
nlp_stanza = initialize_tokenizers()


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


def tokenize_text(text: str, tokenizer: str):
    """
    Tokenizes input text using the specified tokenizer (NLTK, STANZA, or NONE).
    """
    if tokenizer == "NLTK":
        return nltk.tokenize.sent_tokenize(text)
    elif tokenizer == "STANZA":
        doc = nlp_stanza(text)
        return [sentence.text for sentence in doc.sentences]
    elif tokenizer == "NONE":
        return [text]  # Treat the entire input as a single phrase
    else:
        raise ValueError(f"Unsupported tokenizer: {tokenizer}")


async def azure_text_to_speech_processor(
    phrase_queue: asyncio.Queue,
    audio_queue: queue.Queue,
    start_tts_after_paragraph: bool = False,
):
    """
    Converts phrases from the phrase queue into speech using Azure TTS and sends audio to the audio queue.
    If start_tts_after_paragraph is True, waits for paragraph completion before processing.
    """
    buffer = []  # Buffer to store accumulated phrases when waiting for paragraph completion
    tokenizer = Config.TTS_MODELS['AZURE_TTS']['TOKENIZER']  # NLTK, STANZA, or NONE

    try:
        while True:
            phrase = await phrase_queue.get()
            if phrase is None:
                # Process the final buffer if paragraph completion is enabled
                if start_tts_after_paragraph and buffer:
                    combined_text = " ".join(buffer)
                    tokenized_phrases = tokenize_text(combined_text, tokenizer)
                    for phrase in tokenized_phrases:
                        await process_tts(phrase, audio_queue)
                    buffer = []

                # Signal that processing is complete
                audio_queue.put(None)
                return

            if start_tts_after_paragraph:
                # Accumulate text in the buffer until a paragraph is complete
                buffer.append(phrase)
                if phrase.endswith("\n") or not phrase_queue.empty():
                    continue  # Wait for more input if the paragraph isn't finished
                combined_text = " ".join(buffer)
                tokenized_phrases = tokenize_text(combined_text, tokenizer)
                for phrase in tokenized_phrases:
                    await process_tts(phrase, audio_queue)
                buffer = []  # Clear buffer after processing
            else:
                # Process each phrase immediately
                tokenized_phrases = tokenize_text(phrase, tokenizer)
                for phrase in tokenized_phrases:
                    await process_tts(phrase, audio_queue)
    except Exception as e:
        logger.error(f"Error in TTS processing: {e}")
        audio_queue.put(None)


async def process_tts(phrase: str, audio_queue: queue.Queue):
    """
    Sends text to Azure TTS for synthesis and streams the audio to the queue.
    """
    try:
        # Initialize Speech Config
        speech_config = get_azure_speech_config()

        # Retrieve and set the audio format from configuration
        azure_config = Config.TTS_MODELS['AZURE_TTS']
        audio_format_str = azure_config['AUDIO_FORMAT']
        try:
            audio_format = getattr(speechsdk.SpeechSynthesisOutputFormat, audio_format_str)
            speech_config.set_speech_synthesis_output_format(audio_format)
        except AttributeError:
            raise ValueError(f"Invalid audio format: {audio_format_str}")

        # Create SSML with prosody adjustments
        ssml_phrase = create_ssml(phrase)

        # Set up push audio output stream with the callback
        push_stream_callback = PushAudioOutputStreamCallback(audio_queue)
        push_stream = speechsdk.audio.PushAudioOutputStream(push_stream_callback)
        audio_config = speechsdk.audio.AudioOutputConfig(stream=push_stream)
        synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

        # Synthesize speech using SSML
        result = synthesizer.speak_ssml_async(ssml_phrase).get()

        if result.reason != speechsdk.ResultReason.SynthesizingAudioCompleted:
            raise RuntimeError(f"Failed to synthesize audio. Reason: {result.reason}")
    except Exception as e:
        logger.error(f"Error processing phrase '{phrase}': {e}")
