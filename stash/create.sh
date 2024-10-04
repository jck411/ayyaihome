#!/bin/bash

# Define the base directory
BASE_DIR="/home/jack/ayyaihome/backend"

# Create directories
mkdir -p "$BASE_DIR/endpoints"
mkdir -p "$BASE_DIR/services"
mkdir -p "$BASE_DIR/utils"

# Create init.py
cat > "$BASE_DIR/init.py" <<'EOL'
import os
import threading
import pyaudio
from dotenv import load_dotenv
from openai import AsyncOpenAI

# Load environment variables from a .env file
load_dotenv()

# Global stop event
stop_event = threading.Event()

# Constants used throughout the application
CONSTANTS = {
    "MINIMUM_PHRASE_LENGTH": 25,
    "TTS_CHUNK_SIZE": 1024,
    "DEFAULT_RESPONSE_MODEL": "gpt-4o-mini",
    "DEFAULT_TTS_MODEL": "tts-1",
    "DEFAULT_VOICE": "alloy",
    "AUDIO_FORMAT": pyaudio.paInt16,
    "CHANNELS": 1,
    "RATE": 24000,
    "TTS_SPEED": 1.0,
    "TEMPERATURE": 1.0,
    "TOP_P": 1.0,
    "DELIMITERS": [".", "?", "!"],
    "SYSTEM_PROMPT": {"role": "system", "content": "You are a dry but witty AI assistant"}
}

# Initialize the OpenAI API client
aclient = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize PyAudio for audio playback
p = pyaudio.PyAudio()
EOL

# Create app.py
cat > "$BASE_DIR/app.py" <<'EOL'
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from endpoints.openai import openai_router
from endpoints.stop import stop_router

# Initialize the FastAPI app
app = FastAPI()

# Add CORS middleware to allow requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(openai_router)
app.include_router(stop_router)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
EOL

# Create openai.py endpoint
cat > "$BASE_DIR/endpoints/openai.py" <<'EOL'
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from init import stop_event, CONSTANTS, aclient
import asyncio
import queue
from services.audio_player import process_streams
from utils.helpers import find_next_phrase_end

openai_router = APIRouter()

@openai_router.post("/api/openai")
async def openai_stream(request: Request):
    stop_event.set()
    await asyncio.sleep(0.1)
    stop_event.clear()
    data = await request.json()
    messages = [{"role": msg["sender"], "content": msg["text"]} for msg in data.get('messages', [])]
    messages.insert(0, CONSTANTS["SYSTEM_PROMPT"])
    phrase_queue, audio_queue = asyncio.Queue(), queue.Queue()
    asyncio.create_task(process_streams(phrase_queue, audio_queue))
    return StreamingResponse(stream_completion(messages, phrase_queue), media_type='text/plain')

async def stream_completion(messages: list, phrase_queue: asyncio.Queue, model: str = CONSTANTS["DEFAULT_RESPONSE_MODEL"]):
    try:
        response = await aclient.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
            temperature=CONSTANTS["TEMPERATURE"],
            top_p=CONSTANTS["TOP_P"],
        )
        working_string = ""
        in_code_block = False
        async for chunk in response:
            if stop_event.is_set():
                await phrase_queue.put(None)
                break
            content = ""
            if chunk.choices and hasattr(chunk.choices[0].delta, 'content'):
                content = chunk.choices[0].delta.content or ""
            if content:
                yield content
                working_string += content
                while True:
                    code_block_start = working_string.find("```")
                    if in_code_block:
                        code_block_end = working_string.find("```", 3)
                        if code_block_end != -1:
                            working_string = working_string[code_block_end + 3:]
                            await phrase_queue.put("Code presented on screen")
                            in_code_block = False
                        else:
                            break
                    else:
                        if code_block_start != -1:
                            phrase, working_string = working_string[:code_block_start], working_string[code_block_start:]
                            if phrase.strip():
                                await phrase_queue.put(phrase.strip())
                            in_code_block = True
                        else:
                            next_phrase_end = find_next_phrase_end(working_string)
                            if next_phrase_end == -1:
                                break
                            phrase, working_string = working_string[:next_phrase_end + 1].strip(), working_string[next_phrase_end + 1:]
                            await phrase_queue.put(phrase)
        if working_string.strip() and not in_code_block:
            await phrase_queue.put(working_string.strip())
        await phrase_queue.put(None)
    except Exception as e:
        print(f"Error in stream_completion: {e}")
        await phrase_queue.put(None)
        yield f"Error: {e}"
EOL

# Create stop.py endpoint
cat > "$BASE_DIR/endpoints/stop.py" <<'EOL'
from fastapi import APIRouter
from init import stop_event

stop_router = APIRouter()

@stop_router.post("/api/stop")
async def stop_tts():
    stop_event.set()
    return {"status": "Stopping"}
EOL

# Create audio_player.py service
cat > "$BASE_DIR/services/audio_player.py" <<'EOL'
import asyncio
import queue
from init import p, stop_event, CONSTANTS
import threading

def audio_player(audio_queue: queue.Queue):
    stream = None
    try:
        stream = p.open(
            format=CONSTANTS["AUDIO_FORMAT"],
            channels=CONSTANTS["CHANNELS"],
            rate=CONSTANTS["RATE"],
            output=True,
            frames_per_buffer=2048
        )
        stream.write(b'\x00' * 2048)
        while not stop_event.is_set():
            audio_data = audio_queue.get()
            if audio_data is None:
                break
            stream.write(audio_data)
    except Exception as e:
        print(f"Error in audio player: {e}")
    finally:
        if stream:
            stream.stop_stream()
            stream.close()

def start_audio_player(audio_queue: queue.Queue):
    threading.Thread(target=audio_player, args=(audio_queue,)).start()

async def process_streams(phrase_queue: asyncio.Queue, audio_queue: queue.Queue):
    tts_task = asyncio.create_task(text_to_speech_processor(phrase_queue, audio_queue))
    start_audio_player(audio_queue)
    await tts_task

async def text_to_speech_processor(phrase_queue: asyncio.Queue, audio_queue: queue.Queue):
    try:
        while not stop_event.is_set():
            phrase = await phrase_queue.get()
            if phrase is None:
                audio_queue.put(None)
                return
            async with aclient.audio.speech.with_streaming_response.create(
                model=CONSTANTS["DEFAULT_TTS_MODEL"],
                voice=CONSTANTS["DEFAULT_VOICE"],
                input=phrase,
                speed=CONSTANTS["TTS_SPEED"],
                response_format="pcm"
            ) as response:
                async for audio_chunk in response.iter_bytes(CONSTANTS["TTS_CHUNK_SIZE"]):
                    if stop_event.is_set():
                        return
                    audio_queue.put(audio_chunk)
            audio_queue.put(b'\x00' * 2400)
    except Exception as e:
        print(f"Error in TTS processing: {e}")
        audio_queue.put(None)
EOL

# Create helpers.py
cat > "$BASE_DIR/utils/helpers.py" <<'EOL'
from init import CONSTANTS

def find_next_phrase_end(text: str) -> int:
    sentence_delim_pos = [text.find(d, CONSTANTS["MINIMUM_PHRASE_LENGTH"]) for d in CONSTANTS["DELIMITERS"]]
    sentence_delim_pos = [pos for pos in sentence_delim_pos if pos != -1]
    return min(sentence_delim_pos, default=-1)
EOL

echo "Project structure created at $BASE_DIR"