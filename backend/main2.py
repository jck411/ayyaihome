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
    "DELIMITERS": [f"{d} " for d in (".", "?", "!")],  # Delimiters to determine phrase boundaries
    "SYSTEM_PROMPT": {"role": "system", "content": "You are a helpful but witty and dry assistant"}  # System prompt for the OpenAI model
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
            stream_options={"include_usage": True},
        )

        working_string = ""
        async for chunk in response:
            if chunk.choices and hasattr(chunk.choices[0].delta, 'content'):
                content = chunk.choices[0].delta.content or ""
                
                if content:
                    # Stream the pure text to the client
                    yield content
                    
                    # Accumulate content for phrase generation
                    working_string += content
                    
                    # Generate phrases only for audio queue
                    while len(working_string) >= CONSTANTS["MINIMUM_PHRASE_LENGTH"]:
                        delimiter_index = next(
                            (working_string.find(d, CONSTANTS["MINIMUM_PHRASE_LENGTH"]) for d in CONSTANTS["DELIMITERS"] 
                             if working_string.find(d, CONSTANTS["MINIMUM_PHRASE_LENGTH"]) != -1), -1)
                        if delimiter_index == -1:
                            break
                        phrase, working_string = working_string[:delimiter_index + 1].strip(), working_string[delimiter_index + 1:]
                        await phrase_queue.put(phrase)
        
        # Handle any remaining text in working_string as the final phrase
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
    Streams audio chunks to the audio queue for playback.
    """
    try:
        while True:
            phrase = await phrase_queue.get()  # Get the next phrase from the queue
            if phrase is None:
                audio_queue.put(None)  # Signal the end of audio processing
                return

            # Generate speech from the phrase using OpenAI's TTS
            async with aclient.audio.speech.with_streaming_response.create(
                model=CONSTANTS["DEFAULT_TTS_MODEL"],
                voice=CONSTANTS["DEFAULT_VOICE"],
                input=phrase,
                speed=CONSTANTS["TTS_SPEED"],
                response_format="pcm"
            ) as response:
                async for audio_chunk in response.iter_bytes(CONSTANTS["TTS_CHUNK_SIZE"]):
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
        # Open an audio stream
        stream = p.open(
            format=CONSTANTS["AUDIO_FORMAT"],
            channels=CONSTANTS["CHANNELS"],
            rate=CONSTANTS["RATE"],
            output=True
        )
        while True:
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

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)  # Run the FastAPI app
