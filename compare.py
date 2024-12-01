# pip install google-generativeai openai pyaudio python-dotenv fastapi uvicorn

import asyncio
import os
import google.generativeai as genai
import queue
import threading

from fastapi import FastAPI, Request, HTTPException
import uvicorn

import openai
import pyaudio
from dotenv import load_dotenv

# Import the validate function from your module
from backend.utils.request_utils import validate_and_prepare_for_google_completion

# Load environment variables from .env file
load_dotenv()

# Constants
DELIMITERS = [f"{d} " for d in (".", "?", "!")]  # Determine where one phrase ends
MINIMUM_PHRASE_LENGTH = 200  # Minimum length of phrases to minimize audio choppiness
TTS_CHUNK_SIZE = 1024

# Default values
DEFAULT_TTS_MODEL = "tts-1"
DEFAULT_VOICE = "alloy"

# Initialize OpenAI client.
# This uses OPENAI_API_KEY in your .env file implicitly.
OPENAI_CLIENT = openai.OpenAI()

# Global stop event
stop_event = threading.Event()

app = FastAPI()

# Obtain the main event loop
loop = asyncio.get_event_loop()

@app.post("/process_messages")
async def process_messages(request: Request):
    """
    Receives messages via POST request and processes them.
    """
    try:
        messages = await validate_and_prepare_for_google_completion(request)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid request: {e}")

    # Initialize queues
    phrase_queue = asyncio.Queue()
    audio_queue = queue.Queue()

    # Start processing threads
    phrase_generation_thread = threading.Thread(
        target=google_phrase_generator, args=(messages, phrase_queue, loop)
    )
    tts_thread = threading.Thread(
        target=text_to_speech_processor, args=(phrase_queue, audio_queue, loop)
    )
    audio_player_thread = threading.Thread(target=audio_player, args=(audio_queue,))

    phrase_generation_thread.start()
    tts_thread.start()
    audio_player_thread.start()

    # Create and start the "enter to stop" thread
    threading.Thread(target=wait_for_enter, daemon=True).start()

    # Wait for threads to complete
    phrase_generation_thread.join()
    print("## All phrases enqueued. Phrase generation thread terminated.")
    tts_thread.join()
    print("## All TTS complete and enqueued. TTS thread terminated.")
    audio_player_thread.join()
    print("## Audio output complete. Audio player thread terminated.")

    return {"status": "Processing complete"}

def google_phrase_generator(messages: list[dict], phrase_queue: asyncio.Queue, loop: asyncio.AbstractEventLoop):
    """Generates phrases using Google's Gemini API and puts them in the phrase queue."""
    print(f"Sending messages:\n{messages}\n- - - - - - - - - -")

    async def async_google_generation():
        try:
            await stream_google_completion(messages=messages, phrase_queue=phrase_queue)
        except Exception as e:
            print(f"Error in async_google_generation: {e}")
            await phrase_queue.put(None)

    # Schedule the coroutine in the event loop
    asyncio.run_coroutine_threadsafe(async_google_generation(), loop).result()

def text_to_speech_processor(
    phrase_queue: asyncio.Queue,
    audio_queue: queue.Queue,
    loop: asyncio.AbstractEventLoop,
    client: openai.OpenAI = OPENAI_CLIENT,
    model: str = DEFAULT_TTS_MODEL,
    voice: str = DEFAULT_VOICE,
):
    """Processes phrases into speech and puts the audio in the audio queue."""
    async def async_tts_processing():
        while not stop_event.is_set():
            phrase = await phrase_queue.get()
            if phrase is None:
                audio_queue.put(None)
                break
            try:
                # Assuming `with_streaming_response.create` is async-compatible
                async with client.audio.speech.with_streaming_response.create(
                    model=model, voice=voice, response_format="pcm", input=phrase
                ) as response:
                    async for chunk in response.iter_bytes(chunk_size=TTS_CHUNK_SIZE):
                        audio_queue.put(chunk)
                        if stop_event.is_set():
                            break
            except Exception as e:
                print(f"Error in text_to_speech_processor: {e}")
                audio_queue.put(None)
                break

    # Schedule the coroutine in the event loop
    asyncio.run_coroutine_threadsafe(async_tts_processing(), loop).result()

def audio_player(audio_queue: queue.Queue):
    """Plays audio from the audio queue."""
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

def wait_for_enter():
    """Waits for the Enter key press to stop the operation."""
    input("Press Enter to stop...\n\n")
    stop_event.set()
    print("STOP instruction received. Working to quit...")

async def stream_google_completion(messages: list[dict], phrase_queue: asyncio.Queue):
    """
    Streams completion from Google's Gemini API and processes the text.

    Args:
        messages (list[dict]): List of message dictionaries with `role` and `content` keys.
        phrase_queue (asyncio.Queue): Queue to handle processed phrases.
    """
    try:
        # Configure the SDK with your API key
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise Exception("GEMINI_API_KEY is not set.")

        genai.configure(api_key=api_key)

        # Initialize the model
        model = genai.GenerativeModel("gemini-1.5-flash")

        # Construct the system prompt and user input
        system_prompt = "You are a helpful assistant who writes creative and engaging responses."
        user_inputs = "\n".join(msg["content"] for msg in messages)
        complete_prompt = f"{system_prompt}\n\n{user_inputs}"

        # Generate content asynchronously with the system prompt
        response = await model.generate_content_async(complete_prompt, stream=True)

        # Stream the response
        async for chunk in response:
            content = chunk.text or ""
            if content:
                # Log each chunk
                print(f"> {content}")
                await phrase_queue.put(content)

        # Signal the end of processing
        await phrase_queue.put(None)

    except Exception as e:
        await phrase_queue.put(None)
        print(f"Error calling Google's Gemini API: {e}")

if __name__ == "__main__":
    uvicorn.run("compare:app", host="0.0.0.0", port=8000)
