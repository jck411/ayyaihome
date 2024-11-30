import asyncio
import logging
from typing import List, Dict, Union, Optional, AsyncIterator, Sequence, Any

from anthropic import AsyncAnthropic
from fastapi import HTTPException

from backend.config import Config
from backend.config.clients import get_anthropic_client
from backend.text_generation.stream_handler import extract_content_from_anthropic_chunk

logger = logging.getLogger(__name__)

def find_earliest_delimiter(working_string: str, delimiters: List[str]) -> Optional[int]:
    """
    Find the earliest occurrence of any delimiter in the string.
    
    Args:
        working_string: String to search for delimiters
        delimiters: List of delimiter strings
    
    Returns:
        Index of the earliest delimiter or None if no delimiter found
    """
    earliest_index = float('inf')
    for delimiter in delimiters:
        index = working_string.find(delimiter)
        if index != -1:
            earliest_index = min(earliest_index, index)
    return earliest_index if earliest_index != float('inf') else None

async def process_chunks(
    chunk_queue: asyncio.Queue,
    phrase_queue: asyncio.Queue,
    delimiters: List[str]
):
    """
    Process incoming chunks, extracting phrases based on specified delimiters.
    
    Args:
        chunk_queue: Queue of incoming text chunks
        phrase_queue: Queue to send extracted phrases
        delimiters: List of phrase-ending delimiters
    """
    working_string = ""
    delimiter_logic_on = True

    while True:
        chunk = await chunk_queue.get()
        
        if chunk is None:
            # End of stream processing
            if delimiter_logic_on and working_string.strip():
                logger.debug(f"Final phrase: {working_string.strip()}")
                print(f"Final phrase: {working_string.strip()}")  # Print final phrase
                await phrase_queue.put(working_string.strip())
            await phrase_queue.put(None)
            break

        content = extract_content_from_anthropic_chunk(chunk)
        if content:
            working_string += content

            while delimiter_logic_on:
                # Use synchronous function call without await
                delimiter_index = find_earliest_delimiter(working_string, delimiters)
                
                if delimiter_index is None:
                    break

                phrase = working_string[:delimiter_index + 1]
                working_string = working_string[delimiter_index + 1:]

                logger.debug(f"Extracted phrase: {phrase.strip()}")
                print(f"Extracted phrase: {phrase.strip()}")  # Print each extracted phrase
                await phrase_queue.put(phrase.strip())

async def stream_anthropic_completion(
    messages: Sequence[Dict[str, Union[str, Any]]],
    phrase_queue: asyncio.Queue,
    client: Optional[AsyncAnthropic] = None
) -> AsyncIterator[str]:
    """
    Stream Anthropic completion with delimiter-based phrase extraction.
    
    Args:
        messages: Conversation messages
        phrase_queue: Queue for extracted phrases
        client: Optional Anthropic client
    
    Returns:
        Async iterator of streaming text chunks
    
    Raises:
        HTTPException: If there's an error calling the Anthropic API
    """
    client = client or get_anthropic_client()
    delimiters = Config.DELIMITERS
    chunk_queue = asyncio.Queue()

    # Start the chunk processing task
    chunk_processor_task = asyncio.create_task(process_chunks(chunk_queue, phrase_queue, delimiters))

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
            async for chunk in stream.text_stream:
                yield chunk
                await chunk_queue.put(chunk)

        await chunk_queue.put(None)
        await chunk_processor_task

    except Exception as e:
        logger.error(f"Error calling Anthropic API: {e}")
        await phrase_queue.put(None)
        raise HTTPException(status_code=500, detail=f"Error calling Anthropic API: {e}")
