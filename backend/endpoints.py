import asyncio
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
import logging

from backend.config import Config
from backend.text_generation.openai_chat_completions import stream_openai_completion
from backend.text_generation.anthropic_chat_completions import stream_anthropic_completion
from backend.text_generation.google_chat_completions import stream_google_completion
from backend.text_generation.mistral_chat_completions import stream_mistral_completion
from backend.text_generation.grok_chat_completions import stream_grok_completion

from backend.stream_processing import process_streams
from backend.utils.request_utils import (
    validate_and_prepare_for_anthropic,
    validate_and_prepare_for_openai_completion,
    validate_and_prepare_for_google_completion,
    validate_and_prepare_for_mistral_completion,
    validate_and_prepare_for_grok_completion,
)

logger = logging.getLogger(__name__)

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

        # Initialize asynchronous queues
        phrase_queue = asyncio.Queue()
        audio_queue = asyncio.Queue()

        # Start the process_streams task to handle real-time streaming
        asyncio.create_task(
            process_streams(
                phrase_queue=phrase_queue,
                audio_queue=audio_queue,
            )
        )

        # Return the streaming response
        return StreamingResponse(
            stream_anthropic_completion(
                messages=user_messages,
                phrase_queue=phrase_queue,
            ),
            media_type="text/plain",
        )

    except Exception as e:
        logger.error(f"Error in chat_with_anthropic: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")


@router.post("/api/openai")
async def openai_stream(request: Request):
    """
    Endpoint for handling chat requests with OpenAI's API.
    """
    try:
        # Use the validation function
        messages = await validate_and_prepare_for_openai_completion(request)

        # Initialize asynchronous queues
        phrase_queue = asyncio.Queue()
        audio_queue = asyncio.Queue()

        # Start the process_streams task to handle real-time streaming
        asyncio.create_task(
            process_streams(
                phrase_queue=phrase_queue,
                audio_queue=audio_queue,
            )
        )

        # Return the streaming response
        return StreamingResponse(
            stream_openai_completion(
                messages=messages,
                phrase_queue=phrase_queue,
            ),
            media_type="text/plain",
        )

    except Exception as e:
        logger.error(f"Error in openai_stream: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")


@router.post("/api/google")
async def google_stream(request: Request):
    """
    Endpoint for handling chat requests with Google's Gemini API.
    """
    try:
        # Validate and prepare the request
        messages = await validate_and_prepare_for_google_completion(request)

        # Initialize asynchronous queues
        phrase_queue = asyncio.Queue()
        audio_queue = asyncio.Queue()

        # Start the process_streams task to handle real-time streaming
        asyncio.create_task(
            process_streams(
                phrase_queue=phrase_queue,
                audio_queue=audio_queue,
            )
        )

        # Stream response from Google API
        return StreamingResponse(
            stream_google_completion(
                messages=messages,
                phrase_queue=phrase_queue,
            ),
            media_type="text/plain",
        )

    except Exception as e:
        logger.error(f"Error in google_stream: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")

@router.post("/api/mistral")
async def mistral_stream(request: Request):
    """
    Endpoint for handling chat requests with Mistral's API.
    """
    try:
        # Validate and prepare the request
        messages = await validate_and_prepare_for_mistral_completion(request)

        # Initialize asynchronous queues
        phrase_queue = asyncio.Queue()
        audio_queue = asyncio.Queue()

        # Start the process_streams task to handle real-time streaming
        asyncio.create_task(
            process_streams(
                phrase_queue=phrase_queue,
                audio_queue=audio_queue,
            )
        )

        # Stream response from Mistral API
        return StreamingResponse(
            stream_mistral_completion(
                messages=messages,
                phrase_queue=phrase_queue,
            ),
            media_type="text/plain",
        )

    except Exception as e:
        logger.error(f"Error in mistral_stream: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")
    
@router.post("/api/grok")
async def grok_stream(request: Request):
    """
    Endpoint for handling chat requests with Grok's API.
    """
    try:
        # Use the validation function for Grok
        messages = await validate_and_prepare_for_grok_completion(request)

        # Initialize asynchronous queues
        phrase_queue = asyncio.Queue()
        audio_queue = asyncio.Queue()

        # Start the process_streams task to handle real-time streaming
        asyncio.create_task(
            process_streams(
                phrase_queue=phrase_queue,
                audio_queue=audio_queue,
            )
        )

        # Return the streaming response
        return StreamingResponse(
            stream_grok_completion(
                messages=messages,
                phrase_queue=phrase_queue,
            ),
            media_type="text/plain",
        )

    except Exception as e:
        logger.error(f"Error in grok_stream: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")