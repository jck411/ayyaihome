import os
import asyncio
import logging
from typing import List

import openai
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import pyaudio
import threading
from dotenv import load_dotenv
from openai import AsyncOpenAI

# Load environment variables and initialize constants
load_dotenv()

MINIMUM_PHRASE_LENGTH = 100
TTS_CHUNK_SIZE = 1024
DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_TTS_MODEL = "tts-1"
DEFAULT_VOICE = "alloy"
AUDIO_FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 24000
PHRASE_QUEUE_SIZE = 1000

# Initialize OpenAI client and global stop event
aclient = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
stop_event = threading.Event()

# Create FastAPI app and configure CORS
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def stream_completion(messages: List[dict], phrase_queue: asyncio.Queue, text_queue: asyncio.Queue, model: str = DEFAULT_MODEL):
    try:
        response = await aclient.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
        )

        working_string = ""

        async for chunk in response:
            if stop_event.is_set():
                return
            content = chunk.choices[0].delta.content or ""
            if content:
                await text_queue.put(content)  # Put content in text queue for immediate streaming
                working_string += content
                while len(working_string) >= MINIMUM_PHRASE_LENGTH:
                    delimiter_index = next(
                        (working_string.find(d, MINIMUM_PHRASE_LENGTH) for d in [".", "?", "!"] if working_string.find(d, MINIMUM_PHRASE_LENGTH) != -1),
                        -1
                    )
                    if delimiter_index == -1:
                        break
                    phrase, working_string = working_string[:delimiter_index + 1], working_string[delimiter_index + 1:]
                    await phrase_queue.put(phrase.strip())  # Queue complete phrases for TTS

        if working_string.strip():
            await phrase_queue.put(working_string.strip())

        await phrase_queue.put(None)  # Signal end of phrase stream
        await text_queue.put(None)  # Signal end of text stream
    except Exception as e:
        logger.error(f"Error during OpenAI API call: {e}")
        await text_queue.put(f"Error: {e}")

async def text_streamer(text_queue: asyncio.Queue):
    while True:
        content = await text_queue.get()
        if content is None:
            break
        yield content

async def text_to_speech_processor(phrase_queue: asyncio.Queue, audio_queue: asyncio.Queue):
    while not stop_event.is_set():
        try:
            phrase = await asyncio.wait_for(phrase_queue.get(), timeout=1.0)
            if phrase is None:
                await audio_queue.put(None)
                return

            logger.info(f"Processing phrase for TTS: {phrase}")
            response = await aclient.audio.speech.create(
                model=DEFAULT_TTS_MODEL,
                voice=DEFAULT_VOICE,
                input=phrase,
                response_format="pcm"
            )

            audio_data = b''
            
            # Assuming response.iter_bytes() is a synchronous generator
            async for chunk in async_iter(response.iter_bytes(chunk_size=TTS_CHUNK_SIZE)):
                audio_data += chunk

            for i in range(0, len(audio_data), TTS_CHUNK_SIZE):
                audio_chunk = audio_data[i:i + TTS_CHUNK_SIZE]
                await audio_queue.put(audio_chunk)

            logger.info("TTS processing complete")
        except asyncio.TimeoutError:
            continue  # Continue the loop if no phrase is available
        except Exception as e:
            logger.error(f"Error in text-to-speech processing: {e}")

# Helper function to convert synchronous generator to asynchronous
async def async_iter(sync_gen):
    for item in sync_gen:
        yield item

async def audio_player(audio_queue: asyncio.Queue):
    p = pyaudio.PyAudio()
    player_stream = p.open(format=AUDIO_FORMAT, channels=CHANNELS, rate=RATE, output=True)

    try:
        while not stop_event.is_set():
            audio_data = await audio_queue.get()
            if audio_data is None:
                break
            logger.info("Playing audio chunk")
            player_stream.write(audio_data)
    except Exception as e:
        logger.error(f"Error in audio playback: {e}")
    finally:
        player_stream.stop_stream()
        player_stream.close()
        p.terminate()

@app.post("/api/openai")
async def openai_stream(request: Request):
    data = await request.json()
    messages = data.get('messages', [])

    system_message = {"role": "system", "content": "You are a witty but dry assistant."}
    formatted_messages = [{"role": msg["sender"], "content": msg["text"]} for msg in messages]
    formatted_messages.insert(0, system_message)

    phrase_queue = asyncio.Queue(maxsize=PHRASE_QUEUE_SIZE)
    audio_queue = asyncio.Queue()
    text_queue = asyncio.Queue()

    async def process_streams():
        await asyncio.gather(
            stream_completion(formatted_messages, phrase_queue, text_queue),
            text_to_speech_processor(phrase_queue, audio_queue),
            audio_player(audio_queue)
        )

    # Start the processing tasks in the background
    asyncio.create_task(process_streams())

    return StreamingResponse(text_streamer(text_queue), media_type='text/plain')

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000) 