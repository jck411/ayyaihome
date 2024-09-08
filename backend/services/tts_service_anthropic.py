import asyncio
import queue
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from init import stop_event, CONSTANTS, aclient, anthropic_client  # OpenAI TTS client (aclient) and Anthropic client
from services.audio_player import start_audio_player  # Correct import

# Define the router for Anthropic-related endpoints
anthropic_router = APIRouter()

@anthropic_router.post("/api/anthropic")
async def anthropic_chat(request: Request):
    """
    Handles POST requests to the "/api/anthropic" endpoint.
    Processes user input, sends it to the Anthropic API for response generation,
    streams the text back, and uses OpenAI TTS to convert the text to speech.
    """
    # Handle stop event to stop any ongoing tasks before starting a new request
    stop_event.set()  # Signal stop for ongoing tasks
    await asyncio.sleep(0.1)  # Small delay to ensure previous tasks are cleared
    stop_event.clear()  # Clear the event for this new request

    try:
        # Get messages from the request
        data = await request.json()
        messages = [{"role": msg["role"], "content": msg["content"]} for msg in data.get('messages', [])]

        if not messages:
            return {"error": "Prompt is required."}

        # Initialize queues for TTS processing
        phrase_queue, audio_queue = asyncio.Queue(), queue.Queue()

        # Start TTS processing in the background (OpenAI TTS)
        asyncio.create_task(process_streams(phrase_queue, audio_queue))

        # Return a streaming response from the Anthropic API
        return StreamingResponse(stream_completion(messages, phrase_queue), media_type='text/plain')

    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


async def stream_completion(messages: list, phrase_queue: asyncio.Queue, model: str = "claude-3-5-sonnet-20240620"):
    """
    Streams the response from the Anthropic API.
    Sends each chunk of the response to the phrase queue for OpenAI TTS processing.
    """
    try:
        async with anthropic_client.messages.stream(
            model=model,
            messages=messages,
            max_tokens=1024,
            temperature=0.7
        ) as stream:
            async for chunk in stream.text_stream:
                if stop_event.is_set():  # Stop streaming if the event is triggered
                    await phrase_queue.put(None)
                    return  # Exit the streaming process

                content = chunk or ""

                if content:
                    yield content  # Stream content back to client
                    await phrase_queue.put(content)  # Send content to the TTS queue for OpenAI TTS

            await phrase_queue.put(None)  # Signal the end of the stream to the TTS processor

    except Exception as e:
        print(f"Error in stream_completion: {e}")
        await phrase_queue.put(None)
        yield f"Error: {e}"


async def text_to_speech_processor(phrase_queue: asyncio.Queue, audio_queue: queue.Queue):
    """
    Processes phrases into speech using OpenAI's TTS model.
    Streams audio chunks to the audio queue for playback.
    """
    try:
        while not stop_event.is_set():  # Check stop event in TTS processor
            phrase = await phrase_queue.get()
            if phrase is None:  # If None, this signals the end of TTS processing
                audio_queue.put(None)
                return

            # Send the phrase to OpenAI's TTS API
            async with aclient.audio.speech.with_streaming_response.create(
                model=CONSTANTS["DEFAULT_TTS_MODEL"],
                voice=CONSTANTS["DEFAULT_VOICE"],
                input=phrase,
                speed=CONSTANTS["TTS_SPEED"],
                response_format="pcm"
            ) as response:
                async for audio_chunk in response.iter_bytes(CONSTANTS["TTS_CHUNK_SIZE"]):
                    if stop_event.is_set():  # Stop event triggered, exit
                        return
                    audio_queue.put(audio_chunk)  # Stream audio to the audio queue

            audio_queue.put(b'\x00' * 2400)  # Pause between sentences

    except Exception as e:
        print(f"Error in TTS processing: {e}")
        audio_queue.put(None)  # Signal the end of audio on error


async def process_streams(phrase_queue: asyncio.Queue, audio_queue: queue.Queue):
    """
    Manages the processing of text-to-speech and audio playback using OpenAI TTS.
    """
    tts_task = asyncio.create_task(text_to_speech_processor(phrase_queue, audio_queue))
    start_audio_player(audio_queue)
    await tts_task
