import openai
import queue
import threading
import pyaudio
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from typing import List
from openai import AsyncOpenAI  # Importing AsyncOpenAI

# Load environment variables from .env file
load_dotenv()

# Constants
TTS_CHUNK_SIZE = 1024
DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_TTS_MODEL = "tts-1"
DEFAULT_VOICE = "alloy"
AUDIO_FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 24000
BUFFER_SIZE = 5  # Number of chunks to accumulate before flushing to TTS

# Initialize AsyncOpenAI client
aclient = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Global stop event
stop_event = threading.Event()

# Create an instance of the FastAPI application
app = FastAPI()

# Configure CORS
origins = ["http://localhost:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def text_to_speech_processor(phrase_queue: queue.Queue, audio_queue: queue.Queue):
    while not stop_event.is_set():
        phrase = phrase_queue.get()
        if phrase is None:
            audio_queue.put(None)
            return

        try:
            response = openai.Audio.speech.create(
                model=DEFAULT_TTS_MODEL,
                voice=DEFAULT_VOICE,
                input=phrase,
                response_format="pcm"
            )

            audio_data = b''
            for chunk in response.iter_bytes(chunk_size=TTS_CHUNK_SIZE):
                audio_data += chunk

            for i in range(0, len(audio_data), TTS_CHUNK_SIZE):
                audio_chunk = audio_data[i:i + TTS_CHUNK_SIZE]
                audio_queue.put(audio_chunk)
        except Exception as e:
            audio_queue.put(None)
            return

def audio_player(audio_queue: queue.Queue):
    p = pyaudio.PyAudio()
    player_stream = p.open(format=AUDIO_FORMAT, channels=CHANNELS, rate=RATE, output=True)

    try:
        while not stop_event.is_set():
            audio_data = audio_queue.get()
            if audio_data is None:
                break
            player_stream.write(audio_data)
    except Exception as e:
        pass
    finally:
        player_stream.stop_stream()
        player_stream.close()
        p.terminate()

@app.post("/api/openai")
async def openai_stream(request: Request):
    data = await request.json()
    messages = data.get('messages', [])

    system_message = {"role": "system", "content": "You are a witty but dry assistant."}
    
    formatted_messages = [
        {"role": msg["sender"], "content": msg["text"]} for msg in messages
    ]
    formatted_messages.insert(0, system_message)

    phrase_queue = queue.Queue()
    audio_queue = queue.Queue()

    tts_thread = threading.Thread(target=text_to_speech_processor, args=(phrase_queue, audio_queue))
    audio_thread = threading.Thread(target=audio_player, args=(audio_queue,))

    tts_thread.start()
    audio_thread.start()

    buffer = []

    async def generate():
        try:
            response = await aclient.chat.completions.create(
                model=DEFAULT_MODEL,
                messages=formatted_messages,
                stream=True
            )
            async for chunk in response:
                choice = chunk.choices[0].delta
                content = choice.content if choice else None
                if content:
                    buffer.append(content)
                    if len(buffer) >= BUFFER_SIZE:
                        phrase = ''.join(buffer)
                        phrase_queue.put(phrase)
                        buffer.clear()
                    yield content
        except Exception as e:
            yield f"Error: {e}"
        finally:
            # Flush remaining buffer to TTS queue
            if buffer:
                phrase_queue.put(''.join(buffer))
            # Signal TTS thread to stop
            phrase_queue.put(None)

    return StreamingResponse(generate(), media_type='text/plain')

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000, reload=True)
