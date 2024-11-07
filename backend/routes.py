from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
import asyncio
import threading
from backend.TTS.RTTTS_openai import play_text_stream
from backend.text_clients.openai_chat_sync import generate_text_stream_sync
from backend.text_clients.openai_chat_async import generate_text_stream_async
import queue
import time
from functools import reduce
from typing import Callable

router = APIRouter()

@router.post("/api/openai")
async def openai_playback(request: Request):
    """
    Endpoint to handle OpenAI text generation, TTS playback, and return the text stream.

    Request payload should include:
        - messages (list): List of message dictionaries with "sender" and "text".
        - use_async (bool): If True, uses async OpenAI client and TTS playback.

    Returns:
        StreamingResponse with the text stream content.
    """
    # Parse JSON request data
    data = await request.json()
    messages = [
        {"role": msg["sender"], "content": msg["text"]}
        for msg in data.get("messages", [])
    ]
    messages.insert(0, {"role": "system", "content": "You are a helpful assistant."})

    # Determine whether to use async client and async playback
    use_async = data.get("use_async", False)

    if use_async:
        # Async version
        # Create a single text stream generator
        text_stream = generate_text_stream_async(messages)

        # Create queue for frontend streaming
        queue_frontend = asyncio.Queue()

        # Producer coroutine: reads from text_stream and puts chunks into the queue
        async def producer():
            async for text_chunk in text_stream:
                await queue_frontend.put(text_chunk)
            # Signal that the stream is over
            await queue_frontend.put(None)

        # Generator for frontend streaming
        async def text_stream_generator():
            while True:
                text_chunk = await queue_frontend.get()
                if text_chunk is None:
                    break
                yield text_chunk

        # Start the producer coroutine
        asyncio.create_task(producer())

        # Since TTS is not set up yet, we won't process TTS in async version
        # You can implement TTS processing here in the future

        return StreamingResponse(text_stream_generator(), media_type="text/plain")

    else:
        # Synchronous version
        # Create a single text stream generator
        text_stream = generate_text_stream_sync(messages)

        # Create queues for TTS and frontend streaming
        queue_tts = queue.Queue()
        queue_frontend = queue.Queue()

        # Producer thread: reads from text_stream and puts chunks into both queues
        def producer():
            for text_chunk in text_stream:
                queue_tts.put(text_chunk)
                queue_frontend.put(text_chunk)
            # Signal that the stream is over
            queue_tts.put(None)
            queue_frontend.put(None)

        # Helper function to apply transformers
        def apply_transformers(s: str, transformers: list[Callable[[str], str]]) -> str:
            return reduce(lambda c, transformer: transformer(c), transformers, s)

        # TTS playback thread with improved buffering
        def tts_playback():
            buffer = ''
            DELIMITERS = [". ", "? ", "! ", "\n"]
            MINIMUM_PHRASE_LENGTH = 80  # Adjust as needed

            content_transformers = [
                lambda c: c.replace("\n", " "),
            ]
            phrase_transformers = [
                lambda p: p.strip(),
            ]

            while True:
                text_chunk = queue_tts.get()
                if text_chunk is None:
                    # Process any remaining text
                    if buffer.strip():
                        phrase = apply_transformers(buffer, phrase_transformers)
                        play_text_stream(phrase)
                    break

                # Apply content transformers
                content = apply_transformers(text_chunk, content_transformers)
                buffer += content

                # Check if buffer contains a phrase
                while True:
                    delimiter_index = -1
                    for delimiter in DELIMITERS:
                        index = buffer.find(delimiter)
                        if index != -1 and (delimiter_index == -1 or index < delimiter_index):
                            delimiter_index = index + len(delimiter)
                    if delimiter_index == -1 or len(buffer[:delimiter_index]) < MINIMUM_PHRASE_LENGTH:
                        break

                    # Extract phrase up to the delimiter
                    phrase = buffer[:delimiter_index]
                    buffer = buffer[delimiter_index:]

                    # Apply phrase transformers
                    phrase = apply_transformers(phrase, phrase_transformers)

                    # Send phrase to TTS
                    play_text_stream(phrase)

        # Generator for frontend streaming
        async def text_stream_generator():
            while True:
                text_chunk = queue_frontend.get()
                if text_chunk is None:
                    break
                yield text_chunk

        # Start producer and TTS playback threads
        threading.Thread(target=producer).start()
        threading.Thread(target=tts_playback).start()

        return StreamingResponse(text_stream_generator(), media_type="text/plain")
