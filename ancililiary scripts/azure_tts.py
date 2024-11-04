import os
import asyncio
from typing import List
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import pyaudio
import threading
from dotenv import load_dotenv
import azure.cognitiveservices.speech as speechsdk
from openai import AsyncOpenAI

# Load environment variables from the .env file
load_dotenv("/home/jack/ayyaihome/ancililiary scripts/.env")

# Verify environment variables are loaded
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
speech_key = os.getenv("AZURE_SPEECH_KEY")
speech_region = os.getenv("AZURE_REGION")

# Print statements for debugging
print("OPENAI_API_KEY:", OPENAI_API_KEY)
print("AZURE_SPEECH_KEY:", speech_key)
print("AZURE_REGION:", speech_region)

# Check if any environment variable is missing
if not all([OPENAI_API_KEY, speech_key, speech_region]):
    raise EnvironmentError("One or more required environment variables are missing.")

# Initialize API clients
aclient = AsyncOpenAI(api_key=OPENAI_API_KEY)
speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=speech_region)
audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)

# Constants
MINIMUM_PHRASE_LENGTH = 150
TTS_CHUNK_SIZE = 1024
DEFAULT_RESPONSE_MODEL = "gpt-4o-mini"
DEFAULT_VOICE = "en-US-AIGenerate1Neural"
AUDIO_FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 24000
TTS_SPEED = 1.0
TEMPERATURE = 1.0
TOP_P = 1.0

DELIMITERS = [f"{d} " for d in (".", "?", "!")]
SYSTEM_PROMPT = {"role": "system", "content": "You are a helpful but witty and dry assistant"}

stop_event = threading.Event()

# FastAPI app setup
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def stream_completion(messages: List[dict], phrase_queue: asyncio.Queue, model: str = DEFAULT_RESPONSE_MODEL):
    try:
        response = await aclient.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
            temperature=TEMPERATURE,
            top_p=TOP_P,
            stream_options={"include_usage": True},
        )

        working_string = ""
        last_chunk = None

        async for chunk in response:
            if stop_event.is_set():
                return

            last_chunk = chunk

            if chunk.choices and hasattr(chunk.choices[0].delta, 'content'):
                content = chunk.choices[0].delta.content or ""
                if content:
                    yield content
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
                            working_string[delimiter_index + len(delimiter):],
                        )
                        await phrase_queue.put(phrase.strip())

        if last_chunk:
            print("Final Chunk - Choices:", last_chunk.choices)

        if working_string.strip():
            await phrase_queue.put(working_string.strip())

        await phrase_queue.put(None)
    except Exception as e:
        yield f"Error: {e}"

async def text_to_speech_processor(phrase_queue: asyncio.Queue, audio_queue: asyncio.Queue):
    while not stop_event.is_set():
        phrase = await phrase_queue.get()
        if phrase is None:
            await audio_queue.put(None)
            return

        try:
            speech_config.speech_synthesis_voice_name = DEFAULT_VOICE
            speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
            result = speech_synthesizer.speak_text_async(phrase).get()

            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                pass
            elif result.reason == speechsdk.ResultReason.Canceled:
                print(f"Speech synthesis canceled: {result.cancellation_details.reason}")
                if result.cancellation_details.reason == speechsdk.CancellationReason.Error:
                    print(f"Error details: {result.cancellation_details.error_details}")

            await audio_queue.put(b'\x00' * 2400)
        except Exception as e:
            await audio_queue.put(None)
            print(f"Error in TTS processing: {e}")
            return

async def audio_player(audio_queue: asyncio.Queue):
    p = pyaudio.PyAudio()
    player_stream = p.open(format=AUDIO_FORMAT, channels=CHANNELS, rate=RATE, output=True)

    try:
        while not stop_event.is_set():
            audio_data = await audio_queue.get()
            if audio_data is None:
                break
            player_stream.write(audio_data)
    finally:
        player_stream.stop_stream()
        player_stream.close()
        p.terminate()

@app.post("/api/openai")
async def openai_stream(request: Request):
    data = await request.json()
    messages = data.get('messages', [])

    formatted_messages = [{"role": msg["sender"], "content": msg["text"]} for msg in messages]
    formatted_messages.insert(0, SYSTEM_PROMPT)

    phrase_queue = asyncio.Queue()
    audio_queue = asyncio.Queue()

    async def process_streams():
        await asyncio.gather(
            text_to_speech_processor(phrase_queue, audio_queue),
            audio_player(audio_queue)
        )

    asyncio.create_task(process_streams())

    return StreamingResponse(stream_completion(formatted_messages, phrase_queue, model=DEFAULT_RESPONSE_MODEL), media_type='text/plain')

# Run the FastAPI app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
