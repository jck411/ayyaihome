import asyncio
import logging
import time
from anthropic import AsyncAnthropic
from fastapi import HTTPException, logger
from fastapi.responses import StreamingResponse
from backend.config import Config  # Import the Config class directly


# Initialize logging
logger = logging.getLogger(__name__)

client = AsyncAnthropic()

async def stream_anthropic_completion(messages: list, phrase_queue: asyncio.Queue, request_timestamp: float):
    """
    Streams responses from the Anthropic API and handles phrase segmentation.

    Args:
        messages (list): The list of message dicts with 'role' and 'content' keys.
        phrase_queue (asyncio.Queue): The queue to hold phrases for processing.
        request_timestamp (float): The timestamp when the request was received.
    """
    try:
        working_string = ""
        first_text_timestamp = None

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
                    if first_text_timestamp is None:
                        first_text_timestamp = time.time()
                        elapsed_time = first_text_timestamp - request_timestamp
                        logger.info(f"Time to first text generation: {elapsed_time:.2f} seconds")

                    yield content
                    working_string += content
                    while len(working_string) >= Config.MINIMUM_PHRASE_LENGTH:
                        delimiter_index = next(
                            (working_string.find(d, Config.MINIMUM_PHRASE_LENGTH) for d in Config.DELIMITERS
                             if working_string.find(d, Config.MINIMUM_PHRASE_LENGTH) != -1), -1)
                        if delimiter_index == -1:
                            break
                        phrase, working_string = working_string[:delimiter_index + 1].strip(), working_string[delimiter_index + 1:]
                        await phrase_queue.put(phrase)

        if working_string.strip():
            await phrase_queue.put(working_string.strip())
        await phrase_queue.put(None)

    except Exception as e:
        await phrase_queue.put(None)
        raise HTTPException(status_code=500, detail=f"Error calling Anthropic API: {str(e)}")