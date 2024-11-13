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


from backend.config import Config, get_openai_client  # Absolute import

from backend.text_generation.openai_chat_completions import stream_completion  # Absolute import
from backend.TTS.openai_tts import text_to_speech_processor  # Adjusted import
from backend.audio_players.pyaudio import start_audio_player


# Load environment variables from a .env file
load_dotenv()

# Load configuration from YAML file
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.yaml")

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


from backend.config import Config, get_openai_client  # Absolute import

from backend.text_generation.openai_chat_completions import stream_completion  # Absolute import
from backend.TTS.openai_tts import text_to_speech_processor  # Adjusted import
from backend.audio_players.pyaudio import start_audio_player


# Load environment variables from a .env file
load_dotenv()

# Load configuration from YAML file
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.yaml")

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

    # Return streaming response without the `model` argument
    return StreamingResponse(
        stream_completion(
            messages=messages,
            phrase_queue=phrase_queue,
            request_timestamp=request_timestamp
        ),
        media_type='text/plain'
    )


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

