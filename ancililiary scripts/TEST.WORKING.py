from dotenv import load_dotenv
import os
from openai import AsyncOpenAI
from RealtimeTTS import TextToAudioStream, OpenAIEngine
from RealtimeTTS.threadsafe_generators import CharIterator, AccumulatingThreadSafeGenerator
import asyncio
import time
import logging

# Load .env file from the specified path
load_dotenv("/home/jack/ayyaihome/backend/.env")

# Retrieve the API key from environment variables
openai_api_key = os.getenv("OPENAI_API_KEY")

# Check if the API key was loaded correctly
if not openai_api_key:
    raise ValueError("API key not found. Please check the .env file and path.")

# Initialize OpenAI client
client = AsyncOpenAI(api_key=openai_api_key)  # Use the loaded API key

# Initialize TTS engine
engine = OpenAIEngine()  # Replace with your preferred TTS engine

# Initialize CharIterator with callbacks and settings
char_iterator = CharIterator(
    log_characters=True,  # Logs each character processed
    on_character=lambda char: print(f"Processed character: {char}"),  # Callback per character
    on_first_text_chunk=lambda: print("First text chunk received"),   # Callback for first chunk
    on_last_text_chunk=lambda: print("Last text chunk received")      # Callback for last chunk
)

# Initialize AccumulatingThreadSafeGenerator with settings
thread_safe_gen = AccumulatingThreadSafeGenerator(
    gen_func=char_iterator,  # Pass CharIterator instance
    on_first_text_chunk=lambda: print("First chunk callback in generator"),
    on_last_text_chunk=lambda: print("Last chunk callback in generator")
)

# Initialize TextToAudioStream with all configurable settings
stream = TextToAudioStream(
    engine=engine,
    log_characters=True,
    on_text_stream_start=lambda: print("Text stream started"),
    on_text_stream_stop=lambda: print("Text stream stopped"),
    on_audio_stream_start=lambda: print("Audio stream started"),
    on_audio_stream_stop=lambda: print("Audio stream stopped"),
    on_character=lambda char: print(f"Character processed: {char}"),
    output_device_index=None,
    tokenizer="nltk",
    language="en",
    muted=False,
    level=logging.INFO
)

# Define async generator to yield text chunks from OpenAI response
async def write(prompt: str):
    response_stream = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        stream=True,
    )
    
    async for chunk in response_stream:
        text_chunk = chunk.choices[0].delta.content
        if text_chunk:
            yield text_chunk

# Main function to handle text streaming and playback
async def main():
    # Use write() generator to feed text chunks into TTS stream
    text_stream = write("say some shiz")

    async for chunk in text_stream:
        stream.feed(chunk)

    # Feed character-based iterator with CharIterator into the stream
    stream.feed(char_iterator)

    # Start asynchronous playback with all additional settings
    stream.play_async(
        fast_sentence_fragment=True,
        buffer_threshold_seconds=0.5,
        minimum_sentence_length=50,
        minimum_first_fragment_length=10,
        reset_generated_text=True,
        on_sentence_synthesized=lambda sentence: print(f"Synthesized sentence: {sentence}"),
        before_sentence_synthesized=lambda sentence: print(f"About to synthesize: {sentence}"),
        on_audio_chunk=lambda chunk: print(f"Received audio chunk of size: {len(chunk)} bytes"),
    )

    # Keep the script running while playback is ongoing
    while stream.is_playing():
        time.sleep(0.1)

# Run the main function
asyncio.run(main())
