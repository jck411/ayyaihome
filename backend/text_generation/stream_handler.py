# backend/text_generation/stream_handler.py

import asyncio
from fastapi import HTTPException
from typing import AsyncIterator, Any, Callable, Optional
from backend.phrase_accumulator import PhraseAccumulator

def extract_content_from_openai_chunk(chunk: Any) -> Optional[str]:
    """
    Extracts the content string from an OpenAI ChatCompletionChunk.

    Args:
        chunk (Any): The chunk object from OpenAI's streaming response.

    Returns:
        Optional[str]: The extracted content string or None if not available.
    """
    try:
        if chunk.choices and hasattr(chunk.choices[0].delta, 'content'):
            return chunk.choices[0].delta.content or ""
    except (AttributeError, IndexError):
        pass
    return None

def extract_content_from_anthropic_chunk(chunk: Any) -> Optional[str]:
    """
    Extracts the content string from Anthropic's streaming response.

    Args:
        chunk (Any): The chunk object from Anthropic's streaming response.

    Returns:
        Optional[str]: The extracted content string or None if not available.
    """
    # Assuming Anthropic's stream yields strings directly
    if isinstance(chunk, str):
        return chunk
    return None

async def handle_streaming(
    stream_iterator: AsyncIterator[Any],
    accumulator: PhraseAccumulator,
    content_extractor: Callable[[Any], Optional[str]],
    api_name: str = "API"  # For error messages
) -> AsyncIterator[str]:
    """
    Handles streaming from an API, extracting content and dispatching phrases.

    Args:
        stream_iterator (AsyncIterator[Any]): The async iterator from the API stream.
        accumulator (PhraseAccumulator): The accumulator for handling phrases.
        content_extractor (Callable[[Any], Optional[str]]): Function to extract content from a chunk.
        api_name (str): Name of the API (for error messages).

    Yields:
        AsyncIterator[str]: The extracted content strings.
    """
    try:
        async for chunk in stream_iterator:
            content = content_extractor(chunk)
            if content:
                # Stream chunk directly to frontend
                yield content

                # Add content to accumulator and process phrases
                await accumulator.add_content(content)

        # Finalize and process remaining content
        await accumulator.finalize()

    except asyncio.CancelledError:
        # Handle client disconnect gracefully
        await accumulator.phrase_queue.put(None)
        raise
    except Exception as e:
        # Ensure that the phrase queue is signaled to prevent hanging consumers
        await accumulator.phrase_queue.put(None)
        raise HTTPException(status_code=500, detail=f"Error calling {api_name} API: {e}")
