import asyncio
from typing import List, Dict, Optional, AsyncIterator
from openai import AsyncOpenAI
from fastapi import HTTPException

from backend.config import Config
from backend.config.clients import get_anthropic_client, get_openai_client

from backend.phrase_accumulator import PhraseAccumulator
from backend.text_generation.stream_handler import handle_streaming, extract_content_from_openai_chunk
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    logger.info("Starting stream_completion...")  # Log function start

    try:
        # Get the OpenAI client if not provided
        openai_client = openai_client or get_openai_client()
        logger.info("OpenAI client initialized.")

        # Fetch configuration values dynamically from Config
        model = Config.LLM_CONFIG.OPENAI_RESPONSE_MODEL
        temperature = Config.LLM_CONFIG.OPENAI_TEMPERATURE
        top_p = Config.LLM_CONFIG.OPENAI_TOP_P
        stream_options = Config.LLM_CONFIG.OPENAI_STREAM_OPTIONS

        logger.info(f"Using OpenAI model: {model}")
        logger.debug(f"Temperature: {temperature}, Top P: {top_p}, Stream options: {stream_options}")

        # Construct the PhraseAccumulator
        accumulator = PhraseAccumulator(Config, phrase_queue)
        logger.info("PhraseAccumulator initialized.")

        # Make the API call to OpenAI
        logger.info("Sending request to OpenAI API for chat completions...")
        response = await openai_client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
            temperature=temperature,
            top_p=top_p,
            stream_options=stream_options,
        )
        logger.info("OpenAI API request successful. Streaming response...")

        # Process the stream and yield content
        async for content in handle_streaming(
            response,
            accumulator,
            content_extractor=extract_content_from_openai_chunk,
            api_name="OpenAI"
        ):
            logger.info(f"Streamed content: {content}")  # Log streamed content
            yield content

    except Exception as e:
        await phrase_queue.put(None)
        logger.error(f"Exception occurred in stream_completion: {e}")
        raise HTTPException(status_code=500, detail=f"Error calling OpenAI API: {e}")
    finally:
        logger.info("Finished stream_completion.")  # Log function end
