# /home/jack/ayyaihome/backend/text_generation/openai_chat_completions.py

import asyncio
from typing import List, Dict, Optional
from openai import AsyncOpenAI
from fastapi import HTTPException
from backend.config import Config, get_openai_client
from backend.TTS.phrase_preparation.phrase_segmentation import segment_and_dispatch_phrases
from backend.TTS.phrase_preparation.phrase_dispatchers import (
    dispatch_to_phrase_queue,
    dispatch_to_other_module
)

async def stream_completion(
    messages: List[Dict[str, str]],
    phrase_queue: asyncio.Queue,
    openai_client: Optional[AsyncOpenAI] = None
):
    """
    Streams the completion from OpenAI and handles phrase segmentation and processing.

    Args:
        messages (List[Dict[str, str]]): The list of message dicts with 'role' and 'content' keys.
        phrase_queue (asyncio.Queue): The queue to hold phrases for processing.
        openai_client (Optional[AsyncOpenAI]): Optional OpenAI client instance.
    """
    openai_client = openai_client or get_openai_client()
    working_string = ""

    try:
        # Use model from Config.RESPONSE_MODEL, which loads from config.yaml
        response = await openai_client.chat.completions.create(
            model=Config.RESPONSE_MODEL,
            messages=messages,
            stream=True,
            temperature=Config.TEMPERATURE,
            top_p=Config.TOP_P,
            stream_options={"include_usage": True},
        )

        # Determine dispatch function based on configuration
        if Config.PHRASE_PROCESSING_MODULE == 'phrase_queue':
            dispatch_function = dispatch_to_phrase_queue
        elif Config.PHRASE_PROCESSING_MODULE == 'other_module':
            dispatch_function = dispatch_to_other_module
        else:
            raise ValueError(f"Unknown PHRASE_PROCESSING_MODULE: {Config.PHRASE_PROCESSING_MODULE}")

        async for chunk in response:
            if chunk.choices and hasattr(chunk.choices[0].delta, 'content'):
                content = chunk.choices[0].delta.content or ""

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
        raise HTTPException(status_code=500, detail=f"Error calling OpenAI API: {e}")
