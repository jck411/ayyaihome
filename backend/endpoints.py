import time
import asyncio
import queue
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
import logging

from backend.config import Config
from backend.text_generation.openai_chat_completions import stream_completion
from backend.stream_processing import process_streams  # Updated import for process_streams

# Initialize logging
logger = logging.getLogger(__name__)

# Create a FastAPI router instance for endpoints
router = APIRouter()

@router.post("/api/openai")
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
