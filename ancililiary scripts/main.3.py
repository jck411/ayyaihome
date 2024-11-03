import os
import asyncio
import time  # Import time module to measure elapsed time
from typing import List
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import pyaudio
from dotenv import load_dotenv
from openai import AsyncOpenAI
import threading
import queue

# Load environment variables from a .env file
load_dotenv()

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
    "DELIMITERS": [f"{d} " for d in (".", "?", "!")],
    "SYSTEM_PROMPT": {"role": "system", "content": "You are a helpful but witty and dry assistant"}
}

# Initialize the OpenAI API client
aclient = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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

# Initialize PyAudio for audio playback
p = pyaudio.PyAudio()
first_audio_timestamp = None  # Global variable to store the first audio timestamp

@app.post("/api/openai")
async def openai_stream(request: Request):
    """
    Endpoint to handle OpenAI streaming requests.
    """
    global first_audio_timestamp  # Access the global variable to reset on each request
    first_audio_timestamp = None  # Reset the timestamp for each request
    
    data = await request.json()
    messages = [{"role": msg["sender"], "content": msg["text"]} for msg in data.get('messages', [])]
    messages.insert(0, CONSTANTS["SYSTEM_PROMPT"])

    phrase_queue, audio_queue = asyncio.Queue(), queue.Queue()
    asyncio.create_task(process_streams(phrase_queue, audio_queue))
    
    return StreamingResponse(stream_completion(messages, phrase_queue), media_type='text/plain')

async def stream_completion(messages: List[dict], phrase_queue: asyncio.Queue, model: str = CONSTANTS["DEFAULT_RESPONSE_MODEL"]):
    try:
        response = await aclient.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
            temperature=CONSTANTS["TEMPERATURE"],
            top_p=CONSTANTS["TOP_P"],
            stream_options={"include_usage": True},
        )

        working_string = ""
        async for chunk in response:
            if chunk.choices and hasattr(chunk.choices[0].delta, 'content'):
                content = chunk.choices[0].delta.content or ""
                
                if content:
                    yield content
                    working_string += content
                    while len(working_string) >= CONSTANTS["MINIMUM_PHRASE_LENGTH"]:
                        delimiter_index = next(
                            (working_string.find(d, CONSTANTS["MINIMUM_PHRASE_LENGTH"]) for d in CONSTANTS["DELIMITERS"] 
                             if working_string.find(d, CONSTANTS["MINIMUM_PHRASE_LENGTH"]) != -1), -1)
                        if delimiter_index == -1:
                            break
                        phrase, working_string = working_string[:delimiter_index + 1].strip(), working_string[delimiter_index + 1:]
                        await phrase_queue.put(phrase)
        
        if working_string.strip():
            await phrase_queue.put(working_string.strip())
        await phrase_queue.put(None)
    
    except Exception as e:
        print(f"Error in stream_completion: {e}")
        await phrase_queue.put(None)
        yield f"Error: {e}"

async def text_to_speech_processor(phrase_queue: asyncio.Queue, audio_queue: queue.Queue):
    """
    Processes phrases into speech using the OpenAI TTS model.
    """
    try:
        while True:
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
                    audio_queue.put(audio_chunk)
            audio_queue.put(b'\x00' * 2400)
    except Exception as e:
        print(f"Error in TTS processing: {e}")
        audio_queue.put(None)

def audio_player(audio_queue: queue.Queue):
    """
    Plays audio data from the audio queue using PyAudio.
    """
    global first_audio_timestamp
    
    stream = None
    try:
        stream = p.open(
            format=CONSTANTS["AUDIO_FORMAT"],
            channels=CONSTANTS["CHANNELS"],
            rate=CONSTANTS["RATE"],
            output=True
        )
        
        while True:
            audio_data = audio_queue.get()
            if audio_data is None:
                break

            if first_audio_timestamp is None:
                first_audio_timestamp = time.time()
                print(f"Time to first audio: {first_audio_timestamp - request_timestamp:.2f} seconds")

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
    global request_timestamp
    request_timestamp = time.time()  # Capture request time
    
    tts_task = asyncio.create_task(text_to_speech_processor(phrase_queue, audio_queue))
    start_audio_player(audio_queue)
    await tts_task

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
