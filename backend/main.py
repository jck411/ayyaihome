import os
import asyncio
import time
import yaml
from typing import List, Dict, Optional
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import pyaudio
from dotenv import load_dotenv
from openai import AsyncOpenAI
import threading
import queue
import logging

from backend.text_generation.openai_chat_completions import stream_completion  # Absolute import
from backend.config import Config, get_openai_client  # Absolute import

# Load environment variables from a .env file
load_dotenv()

# Load configuration from YAML file
CONFIG_PATH = "/home/jack/ayyaihome/backend/config.yaml"
try:
    with open(CONFIG_PATH, 'r') as config_file:
        config_data = yaml.safe_load(config_file)
except FileNotFoundError:
    raise FileNotFoundError(f"Configuration file not found at {CONFIG_PATH}")
except yaml.YAMLError as e:
    raise ValueError(f"Error parsing YAML configuration: {e}")

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



# Initialize the OpenAI API client using dependency injection
def get_openai_client() -> AsyncOpenAI:
    api_key = config_data.get('OPENAI_API_KEY') or os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("OpenAI API key is not set.")
        raise ValueError("OpenAI API key is not set.")
    return AsyncOpenAI(api_key=api_key)

# Initialize the FastAPI app
app = FastAPI()

# Add CORS middleware to allow requests from various origins
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in cors_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize PyAudio for audio playback
pyaudio_instance = pyaudio.PyAudio()

@app.post("/api/openai")
async def openai_stream(request: Request):
    """
    Endpoint to handle OpenAI streaming requests.
    """
    request_timestamp = time.time()

    # Input validation
    try:
        data = await request.json()
        messages = data.get('messages', [])
        if not isinstance(messages, list):
            raise ValueError("Messages must be a list.")
        messages = [{"role": msg["sender"], "content": msg["text"]} for msg in messages]
    except Exception as e:
        logger.error(f"Invalid input data: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    # Insert system prompt
    system_prompt = {"role": "system", "content": Config.SYSTEM_PROMPT_CONTENT}
    messages.insert(0, system_prompt)

    phrase_queue = asyncio.Queue()
    audio_queue = queue.Queue()

    # Start processing streams
    asyncio.create_task(process_streams(
        phrase_queue=phrase_queue,
        audio_queue=audio_queue,
        request_timestamp=request_timestamp
    ))

    # Return streaming response
    return StreamingResponse(
        stream_completion(
            messages=messages,
            phrase_queue=phrase_queue,
            request_timestamp=request_timestamp,
            model=Config.RESPONSE_MODEL  # Using model from Config.RESPONSE_MODEL directly
        ),
        media_type='text/plain'
    )

async def text_to_speech_processor(
    phrase_queue: asyncio.Queue,
    audio_queue: queue.Queue,
    openai_client: Optional[AsyncOpenAI] = None
):
    """
    Processes phrases into speech using the OpenAI TTS model.
    """
    openai_client = openai_client or get_openai_client()
    try:
        while True:
            phrase = await phrase_queue.get()
            if phrase is None:
                audio_queue.put(None)
                return

            async with openai_client.audio.speech.with_streaming_response.create(
                model=Config.TTS_MODEL,
                voice=Config.TTS_VOICE,
                input=phrase,
                speed=Config.TTS_SPEED,
                response_format=Config.AUDIO_RESPONSE_FORMAT
            ) as response:
                async for audio_chunk in response.iter_bytes(Config.TTS_CHUNK_SIZE):
                    audio_queue.put(audio_chunk)
            # Add a small pause between phrases
            audio_queue.put(b'\x00' * 2400)
    except Exception as e:
        logger.error(f"Error in TTS processing: {e}")
        audio_queue.put(None)


def audio_player(audio_queue: queue.Queue, request_timestamp: float):
    """
    Plays audio data from the audio queue using PyAudio.
    """
    stream = None
    first_audio_timestamp = None
    try:
        stream = pyaudio_instance.open(
            format=Config.AUDIO_FORMAT,
            channels=Config.CHANNELS,
            rate=Config.RATE,
            output=True
        )

        while True:
            audio_data = audio_queue.get()
            if audio_data is None:
                break

            if first_audio_timestamp is None:
                first_audio_timestamp = time.time()
                elapsed_time = first_audio_timestamp - request_timestamp
                logger.info(f"Time to first audio: {elapsed_time:.2f} seconds")

            stream.write(audio_data)
    except Exception as e:
        logger.error(f"Error in audio player: {e}")
    finally:
        if stream:
            stream.stop_stream()
            stream.close()


def start_audio_player(audio_queue: queue.Queue, request_timestamp: float):
    threading.Thread(target=audio_player, args=(audio_queue, request_timestamp), daemon=True).start()


async def process_streams(
    phrase_queue: asyncio.Queue,
    audio_queue: queue.Queue,
    request_timestamp: float
):
    """
    Manages the processing of text-to-speech and audio playback.
    """
    try:
        tts_task = asyncio.create_task(text_to_speech_processor(phrase_queue, audio_queue))
        start_audio_player(audio_queue, request_timestamp)
        await tts_task
    except Exception as e:
        logger.error(f"Error in processing streams: {e}")


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)