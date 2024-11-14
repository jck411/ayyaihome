streaming endpoints for each

import os
import asyncio
import queue
import time
import logging
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse, PlainTextResponse

from backend.config import Config
from backend.text_generation.openai_chat_completions import stream_completion
from backend.stream_processing import process_streams  # Updated import for process_streams
from anthropic import AsyncAnthropic


# Initialize logging
logger = logging.getLogger(__name__)

router = APIRouter()
client = AsyncAnthropic()

@router.post("/api/chat")
async def chat_with_anthropic(request: Request):
    try:
        # Parse and log the JSON payload
        payload = await request.json()
        print("Received Payload:", payload)  # Debugging line
        user_messages = payload.get("messages")

        # Ensure messages exist and are properly formatted
        if not user_messages or not isinstance(user_messages, list) or not all(
            isinstance(msg, dict) and "role" in msg and "content" in msg and isinstance(msg["content"], str) 
            for msg in user_messages):
            raise HTTPException(status_code=400, detail="Invalid message format. Each message must be a dict with 'role' and non-empty 'content' fields.")

        # Define an async generator that streams the response
        async def event_generator():
            async with client.messages.stream(
                max_tokens=1024,
                messages=user_messages,
                model="claude-3-opus-20240229",
            ) as stream:
                async for text_chunk in stream.text_stream:
                    yield text_chunk  # Yield each chunk to the client

        # Return a StreamingResponse
        return StreamingResponse(event_generator(), media_type="text/plain")

    except Exception as e:
        print(f"Error while calling Anthropic API: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

#@router.post("/api/chat")
async def openai_stream(request: Request):
    """
    Endpoint to handle OpenAI streaming requests.
    """
    request_timestamp = time.time()

    # Input validation
    try:
        data = await request.json()
        messages = data.get('messages', [])
        if not isinstance(messages, list):
            raise ValueError("Messages must be a list.")
        messages = [{"role": msg["sender"], "content": msg["text"]} for msg in messages]
    except Exception as e:
        logger.error(f"Invalid input data: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    # Insert system prompt
    system_prompt = {"role": "system", "content": Config.SYSTEM_PROMPT_CONTENT}
    messages.insert(0, system_prompt)

    phrase_queue = asyncio.Queue()
    audio_queue = queue.Queue()

    # Start processing streams
    asyncio.create_task(process_streams(
        phrase_queue=phrase_queue,
        audio_queue=audio_queue,
        request_timestamp=request_timestamp
    ))

    # Return streaming response without the `model` argument
    return StreamingResponse(
        stream_completion(
            messages=messages,
            phrase_queue=phrase_queue,
            request_timestamp=request_timestamp
        ),
        media_type='text/plain'
    )
