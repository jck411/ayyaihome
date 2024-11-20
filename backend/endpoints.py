# backend/endpoints.py

import time
import asyncio
import queue
import logging
from typing import Optional

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse

from backend.config import Config, get_openai_client
from backend.text_generation.openai_chat_completions import stream_completion
from backend.text_generation.anthropic_chat_completions import stream_anthropic_completion
from backend.stream_processing import process_streams
from backend.utils.request_utils import (
    validate_and_prepare_for_anthropic,
    validate_and_prepare_for_openai_completion
)

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/api/anthropic")
async def chat_with_anthropic(request: Request):
    """
    Endpoint for handling chat requests with Anthropic's API.
    """
    try:
        request_timestamp = time.time()

        # Validate and prepare request
        user_messages = await validate_and_prepare_for_anthropic(request)

        # Initialize queues
        phrase_queue = asyncio.Queue()
        audio_queue = queue.Queue()

        # Start processing streams
        asyncio.create_task(process_streams(
            phrase_queue=phrase_queue,
            audio_queue=audio_queue,
            request_timestamp=request_timestamp
        ))

        # Return the streaming response
        return StreamingResponse(
            stream_anthropic_completion(
                messages=user_messages,
                phrase_queue=phrase_queue,
                request_timestamp=request_timestamp
            ),
            media_type='text/plain'
        )

    except HTTPException as he:
        logger.error(f"HTTPException in Anthropic API: {he.detail}")
        raise he
    except Exception as e:
        logger.error(f"Unexpected error in Anthropic API: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.post("/api/openai")
async def openai_stream(request: Request):
    """
    Endpoint for handling chat requests with OpenAI's API.
    """
    try:
        # Validate and prepare request
        messages = await validate_and_prepare_for_openai_completion(request)

        # Initialize queues
        phrase_queue = asyncio.Queue()
        audio_queue = queue.Queue()

        # Start processing streams
        request_timestamp = time.time()

        asyncio.create_task(process_streams(
            phrase_queue=phrase_queue,
            audio_queue=audio_queue,
            request_timestamp=request_timestamp
        ))

        # Return the streaming response
        return StreamingResponse(
            stream_completion(
                messages=messages,
                phrase_queue=phrase_queue,
                request_timestamp=request_timestamp
            ),
            media_type='text/plain'
        )

    except HTTPException as he:
        logger.error(f"HTTPException in OpenAI API: {he.detail}")
        raise he
    except Exception as e:
        logger.error(f"Unexpected error in OpenAI API: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
