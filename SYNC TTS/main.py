# main.py

import os
import threading
import queue
import pyaudio
from dotenv import load_dotenv
import time

# Import the modules
from text_generator_interface import TextGenerator
from tts_service_interface import TTSService
import config  # Import the configuration

# Import the timing module
import timing

# Load environment variables
load_dotenv()

# Initialize queues and events
text_queue = queue.Queue()
sentence_queue = queue.Queue()
audio_queue = queue.Queue()

text_generation_complete = threading.Event()
sentence_processing_complete = threading.Event()
audio_generation_complete = threading.Event()

# Initialize PyAudio
p = pyaudio.PyAudio()

# Open a stream with specific audio format parameters
stream = p.open(format=pyaudio.paInt16,
                channels=1,
                rate=24000,
                output=True)

# Initialize the text generator based on configuration
if config.TEXT_GENERATOR == "openai":
    from openai_text_generator import OpenAITextGenerator
    from openai import OpenAI

    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set.")

    text_client = OpenAI(api_key=openai_api_key)

    text_generator = OpenAITextGenerator(text_client, text_queue, text_generation_complete)

elif config.TEXT_GENERATOR == "anthropic":
    from anthropic_text_generator import AnthropicTextGenerator
    import anthropic

    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    if not anthropic_api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable is not set.")

    text_client = anthropic.Client(api_key=anthropic_api_key)

    text_generator = AnthropicTextGenerator(text_client, text_queue, text_generation_complete)

else:
    raise ValueError("Invalid TEXT_GENERATOR in config.py")

# Initialize the sentence processor based on configuration
if config.SENTENCE_PROCESSOR == "default":
    from default_sentence_processor import DefaultSentenceProcessor

    sentence_processor = DefaultSentenceProcessor(
        text_queue,
        sentence_queue,
        text_generation_complete,
        sentence_processing_complete
    )

elif config.SENTENCE_PROCESSOR == "transformers":
    from transformers_sentence_processor import transformersSentenceProcessor

    sentence_processor = transformersSentenceProcessor(
        text_queue,
        sentence_queue,
        text_generation_complete,
        sentence_processing_complete,
        content_transformers=config.CONTENT_TRANSFORMERS,
        phrase_transformers=config.PHRASE_TRANSFORMERS,
        delimiters=config.DELIMITERS,
        minimum_phrase_length=config.MINIMUM_PHRASE_LENGTH
    )

elif config.SENTENCE_PROCESSOR == "async":
    from async_sentence_processor import AsyncSentenceProcessor

    sentence_processor = AsyncSentenceProcessor(
        text_queue,
        sentence_queue,
        text_generation_complete,
        sentence_processing_complete,
        content_transformers=config.CONTENT_TRANSFORMERS,
        phrase_transformers=config.PHRASE_TRANSFORMERS,
        delimiters=config.DELIMITERS,
        minimum_phrase_length=config.MINIMUM_PHRASE_LENGTH
    )

else:
    raise ValueError("Invalid SENTENCE_PROCESSOR in config.py")

# Initialize the TTS service based on configuration
if config.TTS_SERVICE == "openai":
    from openai_tts_service import OpenAITTSService
    from openai import OpenAI

    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set.")

    tts_client = OpenAI(api_key=openai_api_key)

    tts_service = OpenAITTSService(
        tts_client,
        sentence_queue,
        audio_queue,
        sentence_processing_complete,
        audio_generation_complete
    )

elif config.TTS_SERVICE == "azure":
    from azure_tts_service import AzureTTSService
    import azure.cognitiveservices.speech as speechsdk

    azure_speech_key = os.getenv("AZURE_SPEECH_KEY")
    azure_service_region = os.getenv("AZURE_SERVICE_REGION")
    if not azure_speech_key or not azure_service_region:
        raise ValueError("AZURE_SPEECH_KEY and AZURE_SERVICE_REGION environment variables must be set.")

    speech_config = speechsdk.SpeechConfig(subscription=azure_speech_key, region=azure_service_region)

    tts_service = AzureTTSService(
        speech_config,
        sentence_queue,
        audio_queue,
        sentence_processing_complete,
        audio_generation_complete
    )

else:
    raise ValueError("Invalid TTS_SERVICE in config.py")


# Define the play_audio function with timing logic
def play_audio(audio_queue, audio_generation_complete, stream):
    while not (audio_generation_complete.is_set() and audio_queue.empty()):
        try:
            audio_chunk = audio_queue.get(timeout=0.5)

            # Log the time when the first audio chunk is played
            if timing.first_audio_chunk_time is None:
                timing.first_audio_chunk_time = time.time()
                time_taken = timing.first_audio_chunk_time - timing.prompt_received_time
                print(f"\nTime from prompt to first sound: {time_taken:.2f} seconds")

            stream.write(audio_chunk)
        except queue.Empty:
            continue

# Start the threads
text_thread = threading.Thread(target=text_generator.generate_text)
text_thread.start()

sentence_thread = threading.Thread(target=sentence_processor.process_sentences)
sentence_thread.start()

audio_gen_thread = threading.Thread(target=tts_service.generate_audio)
audio_gen_thread.start()

time.sleep(1)  # Delay for smooth start
audio_play_thread = threading.Thread(
    target=play_audio,
    args=(audio_queue, audio_generation_complete, stream)
)
audio_play_thread.start()

# Wait for all threads to complete
text_thread.join()
sentence_thread.join()
audio_gen_thread.join()
audio_play_thread.join()

# Close the PyAudio stream properly
stream.stop_stream()
stream.close()
p.terminate()

from abc import ABC, abstractmethod

class SentenceProcessor(ABC):
    @abstractmethod
    def process_sentences(self):
        pass
