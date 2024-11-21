# /home/jack/ayyaihome/backend/text_generation/anthropic_chat_completions.py

import asyncio
from anthropic import AsyncAnthropic
from fastapi import HTTPException
from backend.config import Config, get_anthropic_client
from backend.TTS.phrase_preparation.phrase_segmentation import segment_and_dispatch_phrases
from backend.TTS.phrase_preparation.phrase_dispatchers import (
    dispatch_to_phrase_queue,
    dispatch_to_other_module
)

async def stream_anthropic_completion(
    messages: list,
    phrase_queue: asyncio.Queue,
    client: AsyncAnthropic = None
):
    """
    Streams responses from the Anthropic API and handles phrase segmentation and processing.

    Args:
        messages (list): The list of message dicts with 'role' and 'content' keys.
        phrase_queue (asyncio.Queue): The queue to hold phrases for processing.
        client (AsyncAnthropic): Optional Anthropic client instance.
    """
    # Use provided client or initialize default
    client = client or get_anthropic_client()
    working_string = ""

    try:
        # Determine dispatch function based on configuration
        if Config.PHRASE_PROCESSING_MODULE == 'phrase_queue':
            dispatch_function = dispatch_to_phrase_queue
        elif Config.PHRASE_PROCESSING_MODULE == 'other_module':
            dispatch_function = dispatch_to_other_module
        else:
            raise ValueError(f"Unknown PHRASE_PROCESSING_MODULE: {Config.PHRASE_PROCESSING_MODULE}")

        async with client.messages.stream(
            max_tokens=Config.ANTHROPIC_MAX_TOKENS,
            messages=messages,
            model=Config.ANTHROPIC_RESPONSE_MODEL,
            system=Config.ANTHROPIC_SYSTEM_PROMPT,
            temperature=Config.ANTHROPIC_TEMPERATURE,
            top_p=Config.ANTHROPIC_TOP_P,
            stop_sequences=Config.ANTHROPIC_STOP_SEQUENCES,
        ) as stream:
            async for text_chunk in stream.text_stream:
                content = text_chunk or ""

                if content:
                    yield content  # Stream to front end immediately

                    if Config.USE_PHRASE_SEGMENTATION:
                        # Use the shared utility function with the dispatch function
                        working_string = await segment_and_dispatch_phrases(
                            working_string,
                            content,
                            dispatch_function,
                            phrase_queue,
                            Config
                        )
                    else:
                        # Accumulate content without segmentation
                        working_string += content

        # After streaming is complete
        if not Config.USE_PHRASE_SEGMENTATION:
            # Process the whole text
            await dispatch_function(working_string.strip(), phrase_queue)
        else:
            # Handle any remaining content
            if working_string.strip():
                await dispatch_function(working_string.strip(), phrase_queue)

        # Signal that processing is complete
        await phrase_queue.put(None)

    except Exception as e:
        await phrase_queue.put(None)
        raise HTTPException(status_code=500, detail=f"Error calling Anthropic API: {e}")
