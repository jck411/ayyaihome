import time
import os
import asyncio
import queue
import logging
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse

from backend.config import Config  # Import configuration settings

from backend.text_generation.openai_chat_completions import stream_completion  # Import OpenAI streaming function
from backend.text_generation.anthropic_chat_completions import stream_anthropic_completion  # Import Anthropic streaming function

from backend.stream_processing import process_streams  # Import stream processing function
from anthropic import AsyncAnthropic  # Import Anthropic's asynchronous client


# Initialize logging for error tracking and debugging
logger = logging.getLogger(__name__)

# Initialize FastAPI router for defining endpoints
router = APIRouter()
# Initialize the Anthropic asynchronous client
client = AsyncAnthropic()

@router.post("/api/chat")
async def chat_with_anthropic(request: Request):
    """
    Endpoint for handling chat requests with Anthropic's API.
    """
    try:
        request_timestamp = time.time()
        payload = await request.json()
        user_messages = payload.get("messages")

        # Validate message format
        if not user_messages or not isinstance(user_messages, list) or not all(
            isinstance(msg, dict) and "role" in msg and "content" in msg and isinstance(msg["content"], str)
            for msg in user_messages):
            raise HTTPException(status_code=400, detail="Invalid message format.")

        # Initialize async and synchronous queues for processing streams
        phrase_queue = asyncio.Queue()
        audio_queue = queue.Queue()

        # Start the process_streams task to handle real-time streaming
        asyncio.create_task(process_streams(
            phrase_queue=phrase_queue,
            audio_queue=audio_queue,
            request_timestamp=request_timestamp
        ))

        # Return the streaming response with the phrase_queue
        return StreamingResponse(
            stream_anthropic_completion(
                messages=user_messages,
                phrase_queue=phrase_queue,
                request_timestamp=request_timestamp
            ),
            media_type='text/plain'
        )

    except Exception as e:
        logger.error(f"Error in Anthropic API: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

#@router.post("/api/chat")
async def openai_stream(request: Request):
    """
    Endpoint to handle OpenAI streaming requests.
    """
    # Input validation for OpenAI streaming request
    try:
        # Parse the JSON payload from the request
        data = await request.json()
        messages = data.get('messages', [])  # Extract messages from payload
        if not isinstance(messages, list):
            # Raise error if messages are not in list format
            raise ValueError("Messages must be a list.")
        # Reformat messages to match OpenAI's expected input format
        messages = [{"role": msg["sender"], "content": msg["text"]} for msg in messages]
    except Exception as e:
        # Log error details if an exception occurs and raise a 400 error
        logger.error(f"Invalid input data: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    # Insert a system prompt at the beginning of the messages list
    system_prompt = {"role": "system", "content": Config.SYSTEM_PROMPT_CONTENT}
    messages.insert(0, system_prompt)

    # Initialize async and synchronous queues for processing streams
    phrase_queue = asyncio.Queue()
    audio_queue = queue.Queue()

    # Start the process_streams task to handle real-time streaming
    asyncio.create_task(process_streams(
        phrase_queue=phrase_queue,
        audio_queue=audio_queue
    ))

    # Return the streaming response without specifying the `model` argument
    return StreamingResponse(
        stream_completion(
            messages=messages,
            phrase_queue=phrase_queue
        ),
        media_type='text/plain'
    )
