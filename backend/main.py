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

# Load environment variables from a .env file
load_dotenv()

# Global stop event
stop_event = threading.Event()

# Constants used throughout the application
CONSTANTS = {
    "MINIMUM_PHRASE_LENGTH": 25,  # Minimum length for a phrase before it's processed for TTS
    "TTS_CHUNK_SIZE": 1024,  # Size of audio chunks for TTS
    "DEFAULT_RESPONSE_MODEL": "gpt-4o-mini",  # Default OpenAI model for text generation
    "DEFAULT_TTS_MODEL": "tts-1",  # Default model for text-to-speech
    "DEFAULT_VOICE": "alloy",  # Default voice for TTS
    "AUDIO_FORMAT": pyaudio.paInt16,  # Audio format for playback
    "CHANNELS": 1,  # Number of audio channels
    "RATE": 24000,  # Sample rate for audio playback
    "TTS_SPEED": 1.0,  # Speed for TTS output
    "TEMPERATURE": 1.0,  # Temperature for text generation (controls creativity)
    "TOP_P": 1.0,  # Top-p sampling parameter for text generation
    "DELIMITERS": [".", "?", "!"],  # Delimiters to determine phrase boundaries
    "SYSTEM_PROMPT": {"role": "system", "content": "You are a dry but witty AI assistant"}  # System prompt for the OpenAI model
}

# Initialize the OpenAI API client
aclient = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize the FastAPI app
app = FastAPI()

# Add CORS middleware to allow requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize PyAudio for audio playback
p = pyaudio.PyAudio()

@app.post("/api/openai")
async def openai_stream(request: Request):
    """
    Endpoint to handle OpenAI streaming requests.
    Receives a JSON payload, processes it, and returns a streamed response.
    """
    stop_event.set()  # Trigger the stop event to halt any ongoing processes

    # Ensure ongoing processes are fully stopped
    await asyncio.sleep(0.1)  # Brief delay to ensure the stop signal is fully processed

    stop_event.clear()  # Clear the stop event for the new request

    data = await request.json()  # Parse JSON data from the request
    messages = [{"role": msg["sender"], "content": msg["text"]} for msg in data.get('messages', [])]  # Extract messages
    messages.insert(0, CONSTANTS["SYSTEM_PROMPT"])  # Add system prompt to the beginning of messages

    # Initialize queues for phrases and audio data
    phrase_queue, audio_queue = asyncio.Queue(), queue.Queue()  # Use asyncio.Queue for async tasks, queue.Queue for threads
    asyncio.create_task(process_streams(phrase_queue, audio_queue))  # Start the stream processing task

    # Return a StreamingResponse with generated text from OpenAI
    return StreamingResponse(stream_completion(messages, phrase_queue), media_type='text/plain')

async def stream_completion(messages: List[dict], phrase_queue: asyncio.Queue, model: str = CONSTANTS["DEFAULT_RESPONSE_MODEL"]):
    try:
        response = await aclient.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
            temperature=CONSTANTS["TEMPERATURE"],
            top_p=CONSTANTS["TOP_P"],
        )

        working_string = ""
        in_code_block = False  # State to track if we are inside a code block
        async for chunk in response:
            if stop_event.is_set():
                await phrase_queue.put(None)
                break

            content = ""
            if chunk.choices and hasattr(chunk.choices[0].delta, 'content'):
                content = chunk.choices[0].delta.content or ""

            if content:
                yield content  # Stream actual content to the frontend

                working_string += content
                while True:
                    if in_code_block:
                        # We're inside a code block, look for the closing delimiter
                        code_block_end = working_string.find("```", 3)
                        if code_block_end != -1:
                            # Found the end of the code block
                            working_string = working_string[code_block_end + 3:]  # Remove the code block from the buffer
                            await phrase_queue.put("Code presented on screen")
                            in_code_block = False
                        else:
                            break  # Wait for more content to complete the code block
                    else:
                        # Check for the start of a code block
                        code_block_start = working_string.find("```")
                        if code_block_start != -1:
                            # Found the start of a code block
                            phrase, working_string = working_string[:code_block_start], working_string[code_block_start:]
                            if phrase.strip():
                                await phrase_queue.put(phrase.strip())
                            in_code_block = True
                        else:
                            # No code block, process regular text
                            next_phrase_end = find_next_phrase_end(working_string)
                            if next_phrase_end == -1:
                                break

                            phrase, working_string = working_string[:next_phrase_end + 1].strip(), working_string[next_phrase_end + 1:]
                            await phrase_queue.put(phrase)

        # Handle any remaining text in working_string as the final phrase
        if working_string.strip() and not in_code_block:
            await phrase_queue.put(working_string.strip())
        await phrase_queue.put(None)

    except Exception as e:
        print(f"Error in stream_completion: {e}")
        await phrase_queue.put(None)
        yield f"Error: {e}"

def find_next_phrase_end(text: str) -> int:
    # Find the next sentence delimiter after the minimum phrase length
    sentence_delim_pos = [text.find(d, CONSTANTS["MINIMUM_PHRASE_LENGTH"]) for d in CONSTANTS["DELIMITERS"]]
    sentence_delim_pos = [pos for pos in sentence_delim_pos if pos != -1]
    
    return min(sentence_delim_pos, default=-1)

async def text_to_speech_processor(phrase_queue: asyncio.Queue, audio_queue: queue.Queue):
    """
    Processes phrases into speech using the OpenAI TTS model.
    Streams audio chunks to the audio queue for playback.
    """
    try:
        while not stop_event.is_set():
            phrase = await phrase_queue.get()  # Get the next phrase from the queue
            if phrase is None:
                audio_queue.put(None)  # Signal the end of audio processing
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
                    audio_queue.put(audio_chunk)  # Enqueue audio chunks for playback
            audio_queue.put(b'\x00' * 2400)  # Add a short pause between sentences
    except Exception as e:
        print(f"Error in TTS processing: {e}")
        audio_queue.put(None)  # Signal an error

def audio_player(audio_queue: queue.Queue):
    """
    Plays audio data from the audio queue using PyAudio.
    Runs in a separate thread.
    """
    stream = None
    try:
        stream = p.open(
            format=CONSTANTS["AUDIO_FORMAT"],
            channels=CONSTANTS["CHANNELS"],
            rate=CONSTANTS["RATE"],
            output=True,
            frames_per_buffer=2048  # Increase this if necessary
        )

        stream.write(b'\x00' * 2048)  # Pre-fill buffer with silence

        while not stop_event.is_set():
            audio_data = audio_queue.get()  # Get the next chunk of audio data
            if audio_data is None:
                break  # Exit if there's no more audio data
            stream.write(audio_data)  # Play the audio data
    except Exception as e:
        print(f"Error in audio player: {e}")
    finally:
        if stream:
            stream.stop_stream()  # Stop the audio stream
            stream.close()  # Close the audio stream

def start_audio_player(audio_queue: queue.Queue):
    """
    Starts the audio player in a separate thread.
    """
    threading.Thread(target=audio_player, args=(audio_queue,)).start()

async def process_streams(phrase_queue: asyncio.Queue, audio_queue: queue.Queue):
    """
    Manages the processing of text-to-speech and audio playback.
    """
    tts_task = asyncio.create_task(text_to_speech_processor(phrase_queue, audio_queue))  # Start the TTS processor
    start_audio_player(audio_queue)  # Start the audio player thread
    await tts_task  # Wait for TTS processing to complete

@app.post("/api/stop")
async def stop_tts():
    """
    Endpoint to stop the TTS and audio playback gracefully.
    """
    stop_event.set()
    return {"status": "Stopping"}

def wait_for_enter():
    """
    Waits for the Enter key press to stop the TTS operation.
    """
    while True:
        input()
        stop_event.set()
        print("TTS stop triggered")

if __name__ == '__main__':
    threading.Thread(target=wait_for_enter, daemon=True).start()

    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
