import os
import asyncio
from typing import List
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import pyaudio
import threading
from dotenv import load_dotenv
from openai import AsyncOpenAI

# Load environment variables and initialize constants
load_dotenv()

# Constants
TTS_CHUNK_SIZE = 1024
DEFAULT_RESPONSE_MODEL = "gpt-4o-mini"
DEFAULT_TTS_MODEL = "tts-1"
DEFAULT_VOICE = "alloy"
AUDIO_FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 24000
TTS_SPEED = 1.0  # TTS speed multiplier

# Delimiters to determine where one phrase ends
DELIMITERS = [f"{d} " for d in (".", "?", "!")]  # Sentence-ending characters followed by a space

# System prompt constant
SYSTEM_PROMPT = {"role": "system", "content": "You are a helpful but witty and dry assistant"}

# Initialize OpenAI client and global stop event
aclient = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
stop_event = threading.Event()

# Create FastAPI app and configure CORS
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Adjust as needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def stream_completion(messages: List[dict], phrase_queue: asyncio.Queue, model: str = DEFAULT_RESPONSE_MODEL):
    """
    Streams completion from OpenAI and pushes complete phrases to phrase_queue based on delimiters.
    """
    try:
        response = await aclient.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
            stream_options={"include_usage": True},
        )

        working_string = ""
        last_chunk = None

        async for chunk in response:
            if stop_event.is_set():
                return

            last_chunk = chunk  # Keep track of the last chunk

            if chunk.choices and hasattr(chunk.choices[0].delta, 'content'):
                content = chunk.choices[0].delta.content or ""
                if content:
                    working_string += content
                    yield content  # Stream raw text directly

                    # Process complete phrases using delimiters
                    while True:
                        delimiter_index = -1
                        for delimiter in DELIMITERS:
                            index = working_string.find(delimiter)
                            if index != -1 and (delimiter_index == -1 or index < delimiter_index):
                                delimiter_index = index

                        if delimiter_index == -1:
                            break  # No complete phrase found, wait for more content

                        # Split the phrase and update working_string
                        phrase, working_string = (
                            working_string[: delimiter_index + len(delimiter)],
                            working_string[delimiter_index + len(delimiter):],
                        )
                        await phrase_queue.put(phrase.strip())  # Push the phrase to the queue

        if last_chunk:
            print("****************")
            print(f"Final Chunk - Choices: {last_chunk.choices}")
            print(f"Final Chunk - Usage: {last_chunk.usage}")

        # Push any remaining content at the end of the stream
        if working_string.strip():
            await phrase_queue.put(working_string.strip())

        await phrase_queue.put(None)  # Signal end of phrase stream
    except Exception as e:
        yield f"Error: {e}"

async def text_to_speech_processor(phrase_queue: asyncio.Queue, audio_queue: asyncio.Queue, model: str = DEFAULT_TTS_MODEL, voice: str = DEFAULT_VOICE):
    """
    Processes phrases from phrase_queue using TTS and pushes audio chunks to audio_queue.
    """
    while not stop_event.is_set():
        phrase = await phrase_queue.get()
        if phrase is None:
            await audio_queue.put(None)
            return

        try:
            # Use the client.audio.speech.with_streaming_response.create method for streaming TTS
            async with aclient.audio.speech.with_streaming_response.create(
                model=model,
                voice=voice,
                input=phrase,
                speed=TTS_SPEED,  # Using the constant speed
                response_format="pcm"
            ) as response:
                
                # Stream audio chunks asynchronously
                async for audio_chunk in response.iter_bytes(TTS_CHUNK_SIZE):
                    await audio_queue.put(audio_chunk)

            # Add a short silence after each phrase if needed
            await audio_queue.put(b'\x00' * 2400)  # 0.05 seconds of silence at 24000 Hz

        except Exception as e:
            await audio_queue.put(None)
            print(f"Error in TTS processing: {e}")
            return

async def audio_player(audio_queue: asyncio.Queue):
    """
    Plays audio chunks from audio_queue using PyAudio in a separate thread to avoid blocking.
    """
    p = pyaudio.PyAudio()
    player_stream = p.open(format=AUDIO_FORMAT, channels=CHANNELS, rate=RATE, output=True)

    try:
        while not stop_event.is_set():
            audio_data = await audio_queue.get()
            if audio_data is None:
                break
            # Run the blocking write operation in a separate thread
            await asyncio.to_thread(player_stream.write, audio_data)
    finally:
        player_stream.stop_stream()
        player_stream.close()
        p.terminate()

@app.post("/api/openai")
async def openai_stream(request: Request):
    """
    Endpoint to handle streaming requests to OpenAI, converting responses to speech and playing audio.
    """
    data = await request.json()
    messages = data.get('messages', [])

    # Format messages for OpenAI API
    formatted_messages = [{"role": msg["sender"], "content": msg["text"]} for msg in messages]
    formatted_messages.insert(0, SYSTEM_PROMPT)

    # Create queues for phrases and audio chunks
    phrase_queue = asyncio.Queue()
    audio_queue = asyncio.Queue()

    async def process_streams():
        """
        Gathers the TTS processor and audio player tasks.
        """
        await asyncio.gather(
            text_to_speech_processor(phrase_queue, audio_queue, model=DEFAULT_TTS_MODEL, voice=DEFAULT_VOICE),
            audio_player(audio_queue)
        )

    # Start the processing tasks in the background
    asyncio.create_task(process_streams())

    # Return the streaming response
    return StreamingResponse(
        stream_completion(formatted_messages, phrase_queue, model=DEFAULT_RESPONSE_MODEL),
        media_type='text/plain'
    )

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
