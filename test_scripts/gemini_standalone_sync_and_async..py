# Required installations:
# pip install fastapi uvicorn google-generativeai openai pyaudio python-dotenv

import asyncio
import os
import google.generativeai as genai
import queue
import threading
from typing import List, Dict

import openai
import pyaudio
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

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

# Initialize PyAudio for audio playback
p = pyaudio.PyAudio()

# Initialize FastAPI app
app = FastAPI(title="Google Gemini TTS Service")

# Configure CORS
origins = [
    "http://localhost:3000",  # Frontend origin
    # Add more origins if needed
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define Pydantic models for request validation
class Message(BaseModel):
    role: str
    content: str

class GoogleRequest(BaseModel):
    messages: List[Message]

# Queues
phrase_sync_queue = queue.Queue()  # Synchronous queue for phrases
audio_queue = queue.Queue()        # Synchronous queue for audio data

# Background threads
tts_thread = None
audio_player_thread = None

# Lock to ensure background threads are started only once
background_lock = threading.Lock()

def find_next_phrase_end(text: str) -> int:
    # Find the next sentence delimiter after the minimum phrase length
    sentence_delim_pos = [text.find(d, MINIMUM_PHRASE_LENGTH) for d in DELIMITERS]
    sentence_delim_pos = [pos for pos in sentence_delim_pos if pos != -1]
    return min(sentence_delim_pos, default=-1)

async def stream_google_completion(messages: List[Dict[str, str]], async_phrase_queue: asyncio.Queue):
    """
    Streams completion from Google's Gemini API and processes the text.

    Args:
        messages (List[Dict[str, str]]): List of message dictionaries with `role` and `content` keys.
        async_phrase_queue (asyncio.Queue): Async queue to handle processed phrases.
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
                print(f"> {content}")  # Logging each chunk
                await async_phrase_queue.put(content)

        # Signal the end of processing
        await async_phrase_queue.put(None)

    except Exception as e:
        await async_phrase_queue.put(None)
        print(f"Error calling Google's Gemini API: {e}")

async def transfer_async_to_sync(async_queue: asyncio.Queue, sync_queue: queue.Queue):
    """
    Transfers items from an asyncio.Queue to a thread-safe queue.Queue.

    Args:
        async_queue (asyncio.Queue): The asyncio queue to read from.
        sync_queue (queue.Queue): The thread-safe queue to write to.
    """
    try:
        while True:
            item = await async_queue.get()
            if item is None:
                sync_queue.put(None)
                break
            sync_queue.put(item)
    except Exception as e:
        print(f"Error transferring from async to sync queue: {e}")
        sync_queue.put(None)

def google_phrase_generator(messages: List[Dict[str, str]], phrase_sync_queue: queue.Queue):
    """
    Generates phrases using Google's Gemini API and puts them in the sync phrase queue.

    Args:
        messages (List[Dict[str, str]]): List of message dictionaries with `role` and `content` keys.
        phrase_sync_queue (queue.Queue): Thread-safe queue to handle processed phrases.
    """
    async def async_google_generation():
        try:
            async_phrase_queue = asyncio.Queue()
            await stream_google_completion(messages=messages, async_phrase_queue=async_phrase_queue)
            await transfer_async_to_sync(async_phrase_queue, phrase_sync_queue)
        except Exception as e:
            print(f"Error in google_phrase_generator: {e}")
            phrase_sync_queue.put(None)

    asyncio.run(async_google_generation())

@app.post("/api/google")
async def api_google(request: GoogleRequest):
    """
    Endpoint to receive messages and process them using Google's Gemini API and TTS.

    Args:
        request (GoogleRequest): The incoming request containing messages.

    Returns:
        dict: Status message.
    """
    if not request.messages:
        raise HTTPException(status_code=400, detail="No messages provided.")

    # Start the phrase generation in a separate thread
    with background_lock:
        if not phrase_sync_queue.empty():
            raise HTTPException(status_code=429, detail="Processing is already in progress.")

        # Convert Pydantic models to dicts
        messages = [msg.dict() for msg in request.messages]

        phrase_generation_thread = threading.Thread(
            target=google_phrase_generator, args=(messages, phrase_sync_queue), daemon=True
        )
        phrase_generation_thread.start()

    return {"status": "Processing started."}

if __name__ == "__main__":
    # Define the wait_for_enter function
    def wait_for_enter():
        """
        Waits for the Enter key press to stop the operation.
        """
        input("Press Enter to stop...\n\n")
        stop_event.set()
        print("STOP instruction received. Working to quit...")

    # Start the "enter to stop" thread if running as a standalone script
    threading.Thread(target=wait_for_enter, daemon=True).start()

    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
