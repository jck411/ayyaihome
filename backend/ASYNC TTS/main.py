# main.py

import os
import asyncio
import pyaudio
from dotenv import load_dotenv
import time

# Import the modules
import config  # Import the configuration
import timing

# Load environment variables
load_dotenv()

# Initialize queues and events
text_queue = asyncio.Queue()
sentence_queue = asyncio.Queue()
audio_queue = asyncio.Queue()

text_generation_complete = asyncio.Event()
sentence_processing_complete = asyncio.Event()
audio_generation_complete = asyncio.Event()

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
    import openai

    # Set OpenAI API key
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set.")
    openai.api_key = openai_api_key

    # Initialize `aclient` as an async OpenAI client
    aclient = openai

    text_generator = OpenAITextGenerator(aclient, text_queue, text_generation_complete)

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
    from transformers_sentence_processor import TransformersSentenceProcessor

    sentence_processor = TransformersSentenceProcessor(
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
    import openai

    # Use `aclient` if already initialized above
    tts_service = OpenAITTSService(
        aclient,
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
async def play_audio(audio_queue, audio_generation_complete, stream):
    while not (audio_generation_complete.is_set() and audio_queue.empty()):
        try:
            audio_chunk = await asyncio.wait_for(audio_queue.get(), timeout=0.5)

            # Log the time when the first audio chunk is played
            if timing.first_audio_chunk_time is None:
                timing.first_audio_chunk_time = time.time()
                time_taken = timing.first_audio_chunk_time - timing.prompt_received_time
                print(f"\nTime from prompt to first sound: {time_taken:.2f} seconds")

            stream.write(audio_chunk)
        except asyncio.TimeoutError:
            await asyncio.sleep(0.1)
            continue

# Define the main function
async def main():
    # Start the tasks
    tasks = [
        asyncio.create_task(text_generator.generate_text()),
        asyncio.create_task(sentence_processor.process_sentences()),
        asyncio.create_task(tts_service.generate_audio()),
        asyncio.create_task(play_audio(audio_queue, audio_generation_complete, stream))
    ]

    # Wait for all tasks to complete
    await asyncio.gather(*tasks)

    # Close the PyAudio stream properly
    stream.stop_stream()
    stream.close()
    p.terminate()

# Run the main function
if __name__ == "__main__":
    asyncio.run(main())
