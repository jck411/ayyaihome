import os
import asyncio
from typing import List
from fastapi import FastAPI, Request
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

logger = logging.getLogger(__name__)

# Configuration constants
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
    DELIMITERS = [".", "?", "!"]
    SYSTEM_PROMPT = {"role": "system", "content": "You are a helpful but witty and dry assistant"}

# Initialize FastAPI app and OpenAI client
app = FastAPI()
aclient = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# CORS settings for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize audio and queues
p = pyaudio.PyAudio()
stop_event = asyncio.Event()  # Async event instead of threading.Event

@app.post("/api/openai")
async def openai_stream(request: Request):
    stop_event.set()  # Signal to stop any ongoing processing
    await asyncio.sleep(0.1)  # Ensure the stop event is handled
    stop_event.clear()  # Clear for new request

    data = await request.json()
    messages = [{"role": msg["sender"], "content": msg["text"]} for msg in data.get("messages", [])]
    messages.insert(0, Config.SYSTEM_PROMPT)  # Add system prompt

    phrase_queue = asyncio.Queue()
    audio_queue = queue.Queue()  # For synchronous audio playback in threads
    asyncio.create_task(process_streams(phrase_queue, audio_queue))

    return StreamingResponse(
        stream_completion(messages, phrase_queue),
        media_type="text/plain"
    )

async def stream_completion(messages: List[dict], phrase_queue: asyncio.Queue):
    try:
        response = await aclient.chat.completions.create(
            model=Config.DEFAULT_RESPONSE_MODEL,
            messages=messages,
            stream=True,
            temperature=Config.TEMPERATURE,
            top_p=Config.TOP_P,
        )

        working_string, in_code_block = "", False
        async for chunk in response:
            if stop_event.is_set():
                await phrase_queue.put(None)
                break

            content = getattr(chunk.choices[0].delta, 'content', "") if chunk.choices else ""
            if content:
                yield content
                working_string += content

                while True:
                    if in_code_block:
                        code_block_end = working_string.find("```", 3)
                        if code_block_end != -1:
                            working_string = working_string[code_block_end + 3:]
                            await phrase_queue.put("Code presented on screen")
                            in_code_block = False
                        else:
                            break
                    else:
                        code_block_start = working_string.find("```")
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
        logger.error(f"Error in stream_completion: {e}")
        await phrase_queue.put(None)
        yield f"Error: {e}"

def find_next_phrase_end(text: str) -> int:
    sentence_delim_pos = [text.find(d, Config.MINIMUM_PHRASE_LENGTH) for d in Config.DELIMITERS]
    sentence_delim_pos = [pos for pos in sentence_delim_pos if pos != -1]
    return min(sentence_delim_pos, default=-1)

async def text_to_speech_processor(phrase_queue: asyncio.Queue, audio_queue: queue.Queue):
    try:
        while not stop_event.is_set():
            phrase = await phrase_queue.get()
            if phrase is None:
                audio_queue.put(None)
                return

            async with aclient.audio.speech.with_streaming_response.create(
                model=Config.DEFAULT_TTS_MODEL,
                voice=Config.DEFAULT_VOICE,
                input=phrase,
                speed=Config.TTS_SPEED,
                response_format="pcm"
            ) as response:
                async for audio_chunk in response.iter_bytes(Config.TTS_CHUNK_SIZE):
                    if stop_event.is_set():
                        return
                    audio_queue.put(audio_chunk)
            audio_queue.put(b'\x00' * 2400)

    except Exception as e:
        logger.error(f"Error in TTS processing: {e}")
        audio_queue.put(None)

def audio_player(audio_queue: queue.Queue):
    stream = None
    try:
        stream = p.open(
            format=Config.AUDIO_FORMAT,
            channels=Config.CHANNELS,
            rate=Config.RATE,
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
        logger.error(f"Error in audio player: {e}")
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

@app.post("/api/stop")
async def stop_tts():
    stop_event.set()
    return {"status": "Stopping"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
