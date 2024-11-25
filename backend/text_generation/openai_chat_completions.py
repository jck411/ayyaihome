# backend/text_generation/openai_chat_completions.py

import asyncio
from typing import List, Dict, Optional, AsyncIterator
from openai import AsyncOpenAI
from fastapi import HTTPException
from backend.config import Config, get_openai_client
from backend.phrase_accumulator import PhraseAccumulator
from backend.text_generation.stream_handler import handle_streaming, extract_content_from_openai_chunk

async def stream_completion(
    messages: List[Dict[str, str]],
    phrase_queue: asyncio.Queue,
    openai_client: Optional[AsyncOpenAI] = None
) -> AsyncIterator[str]:
    """
    Streams OpenAI chat completions to the frontend and processes phrases.

    Args:
        messages (List[Dict[str, str]]): The chat messages.
        phrase_queue (asyncio.Queue): The queue to dispatch processed phrases.
        openai_client (Optional[AsyncOpenAI]): The OpenAI client.

    Yields:
        AsyncIterator[str]: The streamed content strings.
    """
    openai_client = openai_client or get_openai_client()
    accumulator = PhraseAccumulator(Config, phrase_queue)

    try:
        response = await openai_client.chat.completions.create(
            model=Config.RESPONSE_MODEL,
            messages=messages,
            stream=True,
            temperature=Config.TEMPERATURE,
            top_p=Config.TOP_P,
            stream_options={"include_usage": True},
        )

        async for content in handle_streaming(
            response,
            accumulator,
            content_extractor=extract_content_from_openai_chunk,
            api_name="OpenAI"
        ):
            yield content

    except Exception as e:
        await phrase_queue.put(None)
        raise HTTPException(status_code=500, detail=f"Error calling OpenAI API: {e}")
