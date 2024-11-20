# /path/to/your/project/endpoints.py

import os
import asyncio
import queue
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse

from backend.config import Config  # Import configuration settings
from backend.text_generation.openai_chat_completions import stream_completion  # Import OpenAI streaming function
from backend.text_generation.anthropic_chat_completions import stream_anthropic_completion  # Import Anthropic streaming function
from backend.stream_processing import process_streams  # Import stream processing function
from backend.utils.request_utils import (
    validate_and_prepare_for_anthropic,
    validate_and_prepare_for_openai_completion
)  # Import utility functions

# Initialize FastAPI router for defining endpoints
router = APIRouter()

@router.post("/api/anthropic")
async def chat_with_anthropic(request: Request):
    """
    Endpoint for handling chat requests with Anthropic's API.
    """
    try:
        # Validate and prepare request
        user_messages = await validate_and_prepare_for_anthropic(request)

        # Initialize async and synchronous queues for processing streams
        phrase_queue = asyncio.Queue()
        audio_queue = queue.Queue()

        # Start the process_streams task to handle real-time streaming
        asyncio.create_task(process_streams(
            phrase_queue=phrase_queue,
            audio_queue=audio_queue
        ))

        # Return the streaming response with the phrase_queue
        return StreamingResponse(
            stream_anthropic_completion(
                messages=user_messages,
                phrase_queue=phrase_queue
            ),
            media_type='text/plain'
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.post("/api/openai")
async def openai_stream(request: Request):
    try:
        # Use the validation function
        messages = await validate_and_prepare_for_openai_completion(request)

        # Initialize async and synchronous queues for processing streams
        phrase_queue = asyncio.Queue()
        audio_queue = queue.Queue()

        # Start the process_streams task to handle real-time streaming
        asyncio.create_task(process_streams(
            phrase_queue=phrase_queue,
            audio_queue=audio_queue
        ))

        # Pass the request to stream_completion
        return StreamingResponse(
            stream_completion(
                messages=messages,
                phrase_queue=phrase_queue
            ),
            media_type='text/plain'
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")
