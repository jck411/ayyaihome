import asyncio
import logging
from typing import List, Any, Optional, AsyncIterator
from anthropic import AsyncAnthropic
from fastapi import HTTPException

from backend.config import Config

from backend.config.clients import get_anthropic_client

from backend.phrase_accumulator import PhraseAccumulator
from backend.text_generation.stream_handler import handle_streaming, extract_content_from_anthropic_chunk


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def stream_anthropic_completion(
    messages: List[Any],
    phrase_queue: asyncio.Queue,
    client: Optional[AsyncAnthropic] = None
) -> AsyncIterator[str]:
    """
    Streams Anthropic chat completions to the frontend and processes phrases.

    Args:
        messages (List[Any]): The chat messages.
        phrase_queue (asyncio.Queue): The queue to dispatch processed phrases.
        client (Optional[AsyncAnthropic]): The Anthropic client.

    Yields:
        AsyncIterator[str]: The streamed content strings.
    """
    client = client or get_anthropic_client()
    accumulator = PhraseAccumulator(Config, phrase_queue)

    try:
        async with client.messages.stream(
            max_tokens=Config.ANTHROPIC_MAX_TOKENS,
            messages=messages,
            model=Config.ANTHROPIC_RESPONSE_MODEL,
            system=Config.ANTHROPIC_SYSTEM_PROMPT,
            temperature=Config.ANTHROPIC_TEMPERATURE,
            top_p=Config.ANTHROPIC_TOP_P,
            stop_sequences=Config.ANTHROPIC_STOP_SEQUENCES,
        ) as stream:
            async for content in handle_streaming(
                stream.text_stream,
                accumulator,
                content_extractor=extract_content_from_anthropic_chunk,
                api_name="Anthropic"
            ):
                # Log the streamed content
                logger.info(f"Streamed content: {content}")  # Log content as INFO
                yield content

    except Exception as e:
        # Log the exception
        logger.error(f"Error calling Anthropic API: {e}")
        await phrase_queue.put(None)
        raise HTTPException(status_code=500, detail=f"Error calling Anthropic API: {e}")
