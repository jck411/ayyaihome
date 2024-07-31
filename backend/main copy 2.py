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
from functools import reduce
from typing import Callable, List

# Load environment variables from .env file
load_dotenv()

# Constants
DELIMITERS = [".", "?", "!"]
MINIMUM_PHRASE_LENGTH = 100
TTS_CHUNK_SIZE = 1024
DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_TTS_MODEL = "tts-1"
DEFAULT_VOICE = "alloy"
AUDIO_FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 24000

# Initialize OpenAI client
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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

def apply_transformers(s: str, transformers: List[Callable[[str], str]]) -> str:
    return reduce(lambda c, transformer: transformer(c), transformers, s)

def stream_delimited_completion(messages: List[dict], model: str = DEFAULT_MODEL):
    """Generates delimited phrases from OpenAI's chat completions."""
    working_string = ""
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        stream=True,
    )

    for chunk in response:
        if stop_event.is_set():
            yield None
            return

        content = chunk.choices[0].delta.content or ""
        if content:
            working_string += content
            while len(working_string) >= MINIMUM_PHRASE_LENGTH:
                delimiter_index = -1
                for delimiter in DELIMITERS:
                    index = working_string.find(delimiter, MINIMUM_PHRASE_LENGTH)
                    if index != -1 and (delimiter_index == -1 or index < delimiter_index):
                        delimiter_index = index

                if delimiter_index == -1:
                    break

                phrase, working_string = (
                    working_string[: delimiter_index + len(delimiter)],
                    working_string[delimiter_index + len(delimiter) :],
                )
                yield phrase.strip()

    if working_string.strip():
        yield working_string.strip()

    yield None  # Sentinel value to signal "no more coming"

def text_to_speech_processor(phrase_queue: queue.Queue, audio_queue: queue.Queue):
    while not stop_event.is_set():
        phrase = phrase_queue.get()
        if phrase is None:
            audio_queue.put(None)
            return

        try:
            response = client.audio.speech.create(
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

def generate_text_and_enqueue_tts(messages: List[dict], phrase_queue: queue.Queue):
    for phrase in stream_delimited_completion(messages):
        if phrase:
            phrase_queue.put(phrase)
        else:
            phrase_queue.put(None)

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

    async def text_stream():
        for phrase in stream_delimited_completion(formatted_messages):
            if phrase:
                phrase_queue.put(phrase)
                yield phrase + '\n'
            else:
                phrase_queue.put(None)
                break

    return StreamingResponse(text_stream(), media_type='text/plain')

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000, reload=True)