from openai import AsyncOpenAI
import openai
import os
import queue
import threading
import pyaudio
from functools import reduce
from typing import Callable, AsyncGenerator, List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Constants
DELIMITERS = [f"{d} " for d in (".", "?", "!")]  # Determine where one phrase ends
MINIMUM_PHRASE_LENGTH = 200  # Minimum length of phrases to minimize audio choppiness
TTS_CHUNK_SIZE = 1024

# Default values
DEFAULT_RESPONSE_MODEL = "gpt-4o-mini"  # Updated model
DEFAULT_TTS_MODEL = "tts-1"
DEFAULT_VOICE = "alloy"

# Initialize OpenAI client.
# This uses OPENAI_API_KEY in your .env file implicitly.
aclient = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Global stop event
stop_event = threading.Event()


def apply_transformers(s: str, transformers: List[Callable[[str], str]]) -> str:
    return reduce(lambda c, transformer: transformer(c), transformers, s)


async def stream_delimited_completion(
    messages: List[dict],
    client: AsyncOpenAI,
    model: str = DEFAULT_RESPONSE_MODEL,
    content_transformers: List[Callable[[str], str]] = [],
    phrase_transformers: List[Callable[[str], str]] = [],
    delimiters: List[str] = DELIMITERS,
) -> AsyncGenerator[str, None]:
    """Generates delimited phrases from OpenAI's chat completions."""

    working_string = ""
    response = await client.chat.completions.create(
        model=model,
        messages=messages,
        stream=True
    )
    
    async for chunk in response:
        if stop_event.is_set():
            yield None
            return

        content = chunk.choices[0].delta.content or ""
        if content:
            working_string += apply_transformers(content, content_transformers)
            while len(working_string) >= MINIMUM_PHRASE_LENGTH:
                delimiter_index = -1
                for delimiter in delimiters:
                    index = working_string.find(delimiter, MINIMUM_PHRASE_LENGTH)
                    if index != -1 and (delimiter_index == -1 or index < delimiter_index):
                        delimiter_index = index

                if delimiter_index == -1:
                    break

                phrase, working_string = (
                    working_string[: delimiter_index + len(delimiter)],
                    working_string[delimiter_index + len(delimiter) :],
                )
                yield apply_transformers(phrase, phrase_transformers)

    if working_string.strip():
        yield working_string.strip()

    yield None  # Sentinel value to signal "no more coming"


async def generate_openai_response(formatted_messages):
    full_content = ""
    last_chunk = None
    phrase_queue = queue.Queue()
    audio_queue = queue.Queue()

    # Processor Thread to handle TTS
    tts_thread = threading.Thread(target=text_to_speech_processor, args=(phrase_queue, audio_queue))
    # Audio Player Thread to handle audio playback
    audio_player_thread = threading.Thread(target=audio_player, args=(audio_queue,))

    # Start the threads
    tts_thread.start()
    audio_player_thread.start()

    try:
        async for phrase in stream_delimited_completion(
            messages=formatted_messages,
            client=aclient,
            model=DEFAULT_RESPONSE_MODEL,
            content_transformers=[lambda c: c.replace("\n", " ")],
            phrase_transformers=[lambda p: p.strip()]
        ):
            if phrase:
                phrase_queue.put(phrase)
                full_content += phrase
                yield phrase

    except Exception as e:
        yield f"Error: {e}"
    
    phrase_queue.put(None)
    tts_thread.join()
    audio_player_thread.join()

def text_to_speech_processor(phrase_queue: queue.Queue, audio_queue: queue.Queue):
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    while not stop_event.is_set():
        text = phrase_queue.get()
        if text is None:
            audio_queue.put(None)
            return

        try:
            response = client.audio.speech.create(
                model="tts-1",
                voice="alloy",
                response_format="pcm",
                input=text,
            )

            # Assuming the response is a stream, we need to read the content
            audio_data = b''
            for chunk in response.iter_bytes():
                audio_data += chunk

            # Split audio data into chunks of TTS_CHUNK_SIZE and put them into the queue
            for i in range(0, len(audio_data), TTS_CHUNK_SIZE):
                audio_chunk = audio_data[i:i + TTS_CHUNK_SIZE]
                audio_queue.put(audio_chunk)

        except Exception as e:
            print(f"Error in text_to_speech_processor: {e}")
            audio_queue.put(None)
            return

def audio_player(audio_queue: queue.Queue):
    p = pyaudio.PyAudio()
    player_stream = p.open(format=pyaudio.paInt16, channels=1, rate=24000, output=True)

    try:
        while not stop_event.is_set():
            audio_data = audio_queue.get()
            if audio_data is None:
                break
            player_stream.write(audio_data)

    except Exception as e:
        print(f"Error in audio_player: {e}")

    finally:
        player_stream.stop_stream()
        player_stream.close()
        p.terminate()

# Wait for Enter key to stop
def wait_for_enter():
    input("Press Enter to stop...\n\n")
    stop_event.set()
    print("STOP instruction received. Working to quit...")

# Daemon thread to handle stopping
threading.Thread(target=wait_for_enter, daemon=True).start()
