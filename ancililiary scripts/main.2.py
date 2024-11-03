import os
import asyncio
import uuid
from typing import List, Dict
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import pyaudio
from dotenv import load_dotenv
from openai import AsyncOpenAI
import logging
from concurrent.futures import ThreadPoolExecutor
import re
from contextlib import asynccontextmanager
import time  # Add the time module to handle timing


# Load environment variables from a .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
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

    # Dynamically create the regex pattern based on DELIMITERS
    DELIMITER_REGEX = f"[{''.join(re.escape(d) for d in DELIMITERS)}]"
    DELIMITER_PATTERN = re.compile(DELIMITER_REGEX)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up application...")
    yield
    logger.info("Shutting down application...")
    await stop_all_streams()
    p.terminate()
    executor.shutdown(wait=True)
    logger.info("Shutdown complete.")

app = FastAPI(lifespan=lifespan)

aclient = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# CORS settings for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Update this as needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize PyAudio
p = pyaudio.PyAudio()

# Create a ThreadPoolExecutor for blocking I/O operations
executor = ThreadPoolExecutor(max_workers=2)

# Global registry to track active streams
active_streams: Dict[str, Dict] = {}

async def run_blocking_io(func, *args):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(executor, func, *args)

@app.post("/api/openai")
async def openai_stream(request: Request):
    logger.info("Received new /api/openai request. Stopping all existing streams...")

    # Record the start time
    start_time = time.time()

    # Stop all existing streams before starting a new one
    await stop_all_streams()

    # Generate a unique stream ID for this request
    stream_id = str(uuid.uuid4())
    logger.info(f"Starting new stream with ID: {stream_id}")

    stop_event = asyncio.Event()

    try:
        data = await request.json()
    except Exception as e:
        logger.error(f"Invalid JSON payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    messages = [{"role": msg["sender"], "content": msg["text"]} for msg in data.get("messages", [])]
    messages.insert(0, Config.SYSTEM_PROMPT)

    phrase_queue = asyncio.Queue()
    audio_queue = asyncio.Queue()

    # Pass the start_time to the process_streams task
    process_task = asyncio.create_task(process_streams(stream_id, phrase_queue, audio_queue, stop_event, start_time))

    active_streams[stream_id] = {
        "stop_event": stop_event,
        "task": process_task
    }

    return StreamingResponse(
        stream_completion(messages, phrase_queue, stop_event, stream_id),
        media_type="text/plain"
    )


async def stream_completion(messages: List[dict], phrase_queue: asyncio.Queue, stop_event: asyncio.Event, stream_id: str):
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
                logger.info(f"Stop event set for stream ID: {stream_id}. Terminating stream_completion.")
                await phrase_queue.put(None)
                break

            content = getattr(chunk.choices[0].delta, 'content', "") if chunk.choices else ""
            if content:
                yield content
                working_string += content

                while True:
                    if in_code_block:
                        code_block_end = working_string.find("\n```", 3)
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
        logger.error(f"Error in stream_completion (Stream ID: {stream_id}): {e}")
        await phrase_queue.put(None)
        yield f"Error: {e}"

    finally:
        await cleanup_stream(stream_id)

def find_next_phrase_end(text: str) -> int:
    try:
        match = Config.DELIMITER_PATTERN.search(text, pos=Config.MINIMUM_PHRASE_LENGTH)
        return match.start() if match else -1
    except Exception as e:
        logger.error(f"Error in find_next_phrase_end: {e}")
        return -1

async def text_to_speech_processor(phrase_queue: asyncio.Queue, audio_queue: asyncio.Queue, stop_event: asyncio.Event, stream_id: str, start_time: float):
    try:
        first_audio_sent = False  # Flag to track the first audio chunk

        while not stop_event.is_set():
            try:
                phrase = await asyncio.wait_for(phrase_queue.get(), timeout=60.0)
            except asyncio.TimeoutError:
                await audio_queue.put(None)
                break

            if phrase is None:
                await audio_queue.put(None)
                break

            try:
                async with aclient.audio.speech.with_streaming_response.create(
                    model=Config.DEFAULT_TTS_MODEL,
                    voice=Config.DEFAULT_VOICE,
                    input=phrase,
                    speed=Config.TTS_SPEED,
                    response_format="pcm"
                ) as response:
                    async for audio_chunk in response.iter_bytes(Config.TTS_CHUNK_SIZE):
                        if stop_event.is_set():
                            break

                        # Calculate time for the first audio chunk
                        if not first_audio_sent:
                            time_taken = time.time() - start_time
                            logger.info(f"Time taken for first audio response (Stream ID: {stream_id}): {time_taken:.2f} seconds")
                            first_audio_sent = True  # Set the flag to avoid printing again

                        await audio_queue.put(audio_chunk)
                await audio_queue.put(b'\x00' * 2400)
            except Exception as e:
                logger.error(f"Error in TTS processing (Stream ID: {stream_id}): {e}")
                await audio_queue.put(None)
                break

    except Exception as e:
        logger.error(f"Unexpected error in TTS processor (Stream ID: {stream_id}): {e}")

    finally:
        await audio_queue.put(None)

async def audio_player(audio_queue: asyncio.Queue, stop_event: asyncio.Event, stream_id: str):
    stream = None
    try:
        stream = p.open(
            format=Config.AUDIO_FORMAT,
            channels=Config.CHANNELS,
            rate=Config.RATE,
            output=True,
            frames_per_buffer=2048
        )
        await run_blocking_io(stream.write, b'\x00' * 2048)

        while not stop_event.is_set():
            try:
                audio_data = await asyncio.wait_for(audio_queue.get(), timeout=60.0)
            except asyncio.TimeoutError:
                break

            if audio_data is None:
                break

            await run_blocking_io(stream.write, audio_data)
    except Exception as e:
        logger.error(f"Error in audio player (Stream ID: {stream_id}): {e}")
    finally:
        if stream:
            await run_blocking_io(stream.stop_stream)
            await run_blocking_io(stream.close)

async def process_streams(stream_id: str, phrase_queue: asyncio.Queue, audio_queue: asyncio.Queue, stop_event: asyncio.Event, start_time: float):
    tts_task = asyncio.create_task(text_to_speech_processor(phrase_queue, audio_queue, stop_event, stream_id, start_time))
    audio_task = asyncio.create_task(audio_player(audio_queue, stop_event, stream_id))
    try:
        await asyncio.gather(tts_task, audio_task)
    except asyncio.CancelledError:
        logger.info(f"Process streams tasks cancelled (Stream ID: {stream_id})")
    except Exception as e:
        logger.error(f"Error in process_streams (Stream ID: {stream_id}): {e}")
    finally:
        await cleanup_stream(stream_id)

async def stop_all_streams():
    if not active_streams:
        logger.info("No active streams to stop.")
        return

    logger.info("Stopping all active streams...")
    for stream_id, stream_info in active_streams.items():
        stream_info["stop_event"].set()

    for stream_id, stream_info in active_streams.items():
        stream_info["task"].cancel()

    await asyncio.sleep(0.1)

    active_streams.clear()

async def cleanup_stream(stream_id: str):
    if stream_id in active_streams:
        del active_streams[stream_id]

@app.post("/api/stop_all")
async def stop_all_streams_endpoint():
    await stop_all_streams()
    return {"status": "All active streams have been stopped."}

@app.post("/api/stop/{stream_id}")
async def stop_specific_stream(stream_id: str):
    if stream_id not in active_streams:
        raise HTTPException(status_code=404, detail="Stream ID not found.")

    stream_info = active_streams[stream_id]
    stream_info["stop_event"].set()
    stream_info["task"].cancel()
    await cleanup_stream(stream_id)

    return {"status": f"Stream {stream_id} has been stopped."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
