# /home/jack/ayyaihome/backend/text_generation/openai_chat_completions.py

import asyncio
from typing import List, Dict, Optional
from openai import AsyncOpenAI
from fastapi import HTTPException
from backend.config import Config, get_openai_client
from backend.TTS.phrase_preparation.processing_pipeline import process_pipeline
from backend.TTS.phrase_preparation.phrase_segmentation import segment_text

async def stream_completion(
    messages: List[Dict[str, str]],
    phrase_queue: asyncio.Queue,
    openai_client: Optional[AsyncOpenAI] = None
):
    """
    Streams the completion from OpenAI and processes the text through the pipeline.

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

        async for chunk in response:
            if chunk.choices and hasattr(chunk.choices[0].delta, 'content'):
                content = chunk.choices[0].delta.content or ""

                if content:
                    yield content  # Stream to front end immediately

                    # Accumulate content
                    working_string += content

                    # Attempt to segment and dispatch phrases
                    if Config.USE_PHRASE_SEGMENTATION:
                        working_string, phrases = await segment_text(working_string, Config)
                        for phrase in phrases:
                            # Process each phrase through the pipeline
                            processed_phrase = await process_pipeline(phrase)
                            # Dispatch to phrase queue
                            await phrase_queue.put(processed_phrase)

        # After streaming is complete, process any remaining content
        if working_string.strip():
            processed_text = await process_pipeline(working_string.strip())
            await phrase_queue.put(processed_text)

        # Signal that processing is complete
        await phrase_queue.put(None)

    except Exception as e:
        await phrase_queue.put(None)
        raise HTTPException(status_code=500, detail=f"Error calling OpenAI API: {e}")
