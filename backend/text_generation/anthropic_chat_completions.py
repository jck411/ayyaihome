# /path/to/your/project/text_generation/anthropic_chat_completions.py

import asyncio
from anthropic import AsyncAnthropic
from fastapi import HTTPException
from backend.config import Config, get_anthropic_client
from backend.TTS.phrase_preparation.phrase_segmentation import segment_and_dispatch_phrases 

async def stream_anthropic_completion(
    messages: list,
    phrase_queue: asyncio.Queue,
    client: AsyncAnthropic = None
):
    """
    Streams responses from the Anthropic API and handles phrase segmentation.

    Args:
        messages (list): The list of message dicts with 'role' and 'content' keys.
        phrase_queue (asyncio.Queue): The queue to hold phrases for processing.
        client (AsyncAnthropic): Optional Anthropic client instance.
    """
    # Use provided client or initialize default
    client = client or get_anthropic_client()

    try:
        working_string = ""

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

                    # Use the shared utility function
                    working_string = await segment_and_dispatch_phrases(
                        working_string,
                        content,
                        phrase_queue,
                        Config
                    )

        # Handle any remaining content
        if working_string.strip():
            await phrase_queue.put(working_string.strip())
        await phrase_queue.put(None)

    except Exception as e:
        await phrase_queue.put(None)
        raise HTTPException(status_code=500, detail=f"Error calling Anthropic API: {e}")
