import os
import asyncio
import time
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

# Load environment variables from a .env file
load_dotenv()

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration parameters
class Config:
    MINIMUM_PHRASE_LENGTH = 25
    TTS_CHUNK_SIZE = 1024
    DEFAULT_RESPONSE_MODEL = "gpt-4o-mini"
    DEFAULT_TTS_MODEL = "tts-1"
    DEFAULT_VOICE = "alloy"
    AUDIO_FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 24000
    TTS_SPEED = 1.0
    TEMPERATURE = 1.0
    TOP_P = 1.0
    DELIMITERS = [f"{d} " for d in (".", "?", "!")]
    SYSTEM_PROMPT = {"role": "system", "content": "You are a helpful but witty and dry assistant"}

# Initialize the OpenAI API client using dependency injection
def get_openai_client() -> AsyncOpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("OpenAI API key is not set.")
        raise ValueError("OpenAI API key is not set.")
    return AsyncOpenAI(api_key=api_key)

# Initialize the FastAPI app
app = FastAPI()

# Add CORS middleware to allow requests from various origins
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
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
    messages.insert(0, Config.SYSTEM_PROMPT)

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
            request_timestamp=request_timestamp  # Added here
        ),
        media_type='text/plain'
    )


async def stream_completion(
    messages: List[Dict[str, str]],
    phrase_queue: asyncio.Queue,
    request_timestamp: float,
    model: str = Config.DEFAULT_RESPONSE_MODEL,
    openai_client: Optional[AsyncOpenAI] = None
):
    """
    Streams the completion from OpenAI and handles phrase segmentation.
    """
    openai_client = openai_client or get_openai_client()
    working_string = ""
    first_text_timestamp = None  # Initialize the first text timestamp
    
    try:
        response = await openai_client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
            temperature=Config.TEMPERATURE,
            top_p=Config.TOP_P,
            stream_options={"include_usage": True},
        )

        async for chunk in response:
            if chunk.choices and hasattr(chunk.choices[0].delta, 'content'):
                content = chunk.choices[0].delta.content or ""

                if content:
                    if first_text_timestamp is None:
                        # Capture the timestamp when the first text is generated
                        first_text_timestamp = time.time()
                        elapsed_time = first_text_timestamp - request_timestamp
                        logger.info(f"Time to first text generation: {elapsed_time:.2f} seconds")

                    yield content
                    working_string += content
                    while len(working_string) >= Config.MINIMUM_PHRASE_LENGTH:
                        delimiter_index = next(
                            (working_string.find(d, Config.MINIMUM_PHRASE_LENGTH) for d in Config.DELIMITERS
                             if working_string.find(d, Config.MINIMUM_PHRASE_LENGTH) != -1), -1)
                        if delimiter_index == -1:
                            break
                        phrase, working_string = working_string[:delimiter_index + 1].strip(), working_string[delimiter_index + 1:]
                        await phrase_queue.put(phrase)

        if working_string.strip():
            await phrase_queue.put(working_string.strip())
        await phrase_queue.put(None)

    except Exception as e:
        logger.error(f"Error in stream_completion: {e}")
        await phrase_queue.put(None)
        yield f"Error: {e}"


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
                model=Config.DEFAULT_TTS_MODEL,
                voice=Config.DEFAULT_VOICE,
                input=phrase,
                speed=Config.TTS_SPEED,
                response_format="pcm"
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
    threading.Thread(target=audio_player, args=(audio_queue, request_timestamp)).start()

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
