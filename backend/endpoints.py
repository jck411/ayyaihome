#/home/jack/ayyaihome/backend/endpoints.py
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
from backend.text_generation.deepinfra_chat_completions import stream_deepinfra_completion
from backend.text_generation.openrouter_chat_completions import stream_openrouter_completion
from backend.text_generation.groq_chat_completions import stream_groq_completion

from backend.stream_processing import process_streams
from backend.utils.request_utils import (
    validate_and_prepare_for_anthropic,
    validate_and_prepare_for_openai_completion,
    validate_and_prepare_for_google_completion,
    validate_and_prepare_for_mistral_completion,
    validate_and_prepare_for_grok_completion,
    validate_and_prepare_for_deepinfra,
    validate_and_prepare_for_openrouter,
    validate_and_prepare_for_groq_completion
)

logger = logging.getLogger(__name__)

# Initialize FastAPI router for defining endpoints
router = APIRouter()


# Generalized handler for streaming requests
async def handle_streaming_request(
    request: Request,
    validate_and_prepare_fn,
    stream_completion_fn,
):
    try:
        # Validate and prepare messages
        messages = await validate_and_prepare_fn(request)

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
            stream_completion_fn(
                messages=messages,
                phrase_queue=phrase_queue,
            ),
            media_type="text/plain",
        )

    except Exception as e:
        logger.error(f"Error in streaming request: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")


# Define individual endpoints using the generalized handler
@router.post("/api/anthropic")
async def chat_with_anthropic(request: Request):
    """
    Endpoint for handling chat requests with Anthropic's API.
    """
    return await handle_streaming_request(
        request,
        validate_and_prepare_fn=validate_and_prepare_for_anthropic,
        stream_completion_fn=stream_anthropic_completion,
    )


@router.post("/api/openai")
async def openai_stream(request: Request):
    """
    Endpoint for handling chat requests with OpenAI's API.
    """
    return await handle_streaming_request(
        request,
        validate_and_prepare_fn=validate_and_prepare_for_openai_completion,
        stream_completion_fn=stream_openai_completion,
    )


@router.post("/api/google")
async def google_stream(request: Request):
    """
    Endpoint for handling chat requests with Google's Gemini API.
    """
    return await handle_streaming_request(
        request,
        validate_and_prepare_fn=validate_and_prepare_for_google_completion,
        stream_completion_fn=stream_google_completion,
    )


@router.post("/api/mistral")
async def mistral_stream(request: Request):
    """
    Endpoint for handling chat requests with Mistral's API.
    """
    return await handle_streaming_request(
        request,
        validate_and_prepare_fn=validate_and_prepare_for_mistral_completion,
        stream_completion_fn=stream_mistral_completion,
    )


@router.post("/api/grok")
async def grok_stream(request: Request):
    """
    Endpoint for handling chat requests with Grok's API.
    """
    return await handle_streaming_request(
        request,
        validate_and_prepare_fn=validate_and_prepare_for_grok_completion,
        stream_completion_fn=stream_grok_completion,
    )


@router.post("/api/deepinfra")
async def deepinfra_stream(request: Request):
    """
    Endpoint for handling chat requests with DeepInfra's API.
    """
    return await handle_streaming_request(
        request,
        validate_and_prepare_fn=validate_and_prepare_for_deepinfra,
        stream_completion_fn=stream_deepinfra_completion,
    )


@router.post("/api/openrouter")
async def openrouter_stream(request: Request):
    """
    Endpoint for handling chat requests with OpenRouter's API.
    """
    return await handle_streaming_request(
        request,
        validate_and_prepare_fn=validate_and_prepare_for_openrouter,
        stream_completion_fn=stream_openrouter_completion,
    )


@router.post("/api/groq")
async def groq_stream(request: Request):
    """
    Endpoint for handling chat requests with GROQ's API.
    """
    return await handle_streaming_request(
        request,
        validate_and_prepare_fn=validate_and_prepare_for_groq_completion,
        stream_completion_fn=stream_groq_completion,
    )
