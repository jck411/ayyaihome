import asyncio
import logging
import re
from typing import List, Dict, Union, Optional, AsyncIterator, Sequence, Any

from anthropic import AsyncAnthropic
from fastapi import HTTPException

from backend.config import Config
from backend.config.clients import get_anthropic_client
from backend.text_generation.stream_handler import extract_content_from_anthropic_chunk

logger = logging.getLogger(__name__)

def compile_delimiter_pattern(delimiters: List[str]) -> Optional[re.Pattern]:
    """
    Pre-compile the delimiter regex pattern for efficiency.

    Args:
        delimiters: List of delimiter strings.

    Returns:
        Compiled regex pattern or None if no delimiters provided.
    """
    if not delimiters:
        return None
    # Sort delimiters by length in descending order to match longer delimiters first
    sorted_delimiters = sorted(delimiters, key=len, reverse=True)
    pattern = '|'.join(map(re.escape, sorted_delimiters))
    return re.compile(pattern)

async def process_chunks(
    chunk_queue: asyncio.Queue,
    phrase_queue: asyncio.Queue,
    delimiter_pattern: Optional[re.Pattern],
    use_segmentation: bool,
    character_max: int
):
    """
    Process chunks from chunk_queue, extract phrases based on delimiters and segmentation settings,
    and enqueue them into phrase_queue.

    Args:
        chunk_queue: Queue containing incoming text chunks.
        phrase_queue: Queue to enqueue extracted phrases.
        delimiter_pattern: Compiled regex pattern for delimiters.
        use_segmentation: Flag indicating whether to use segmentation.
        character_max: Maximum number of characters before stopping segmentation.
    """
    working_string = ""
    chars_processed_in_segmentation = 0
    segmentation_active = use_segmentation

    while True:
        chunk = await chunk_queue.get()

        if chunk is None:
            # End of stream: enqueue any remaining phrase and signal termination
            if working_string.strip():
                phrase = working_string.strip()
                await phrase_queue.put(phrase)
            await phrase_queue.put(None)
            break

        content = extract_content_from_anthropic_chunk(chunk)
        if content:
            working_string += content

            if segmentation_active and delimiter_pattern:
                while True:
                    match = delimiter_pattern.search(working_string)
                    if match:
                        # Extract phrase up to and including the delimiter
                        end_index = match.end()
                        phrase = working_string[:end_index].strip()
                        if phrase:
                            await phrase_queue.put(phrase)
                            chars_processed_in_segmentation += len(phrase)
                        # Update working_string by removing the processed phrase
                        working_string = working_string[end_index:]

                        # Check if character_max has been reached
                        if chars_processed_in_segmentation >= character_max:
                            segmentation_active = False
                            break
                    else:
                        break


async def stream_anthropic_completion(
    messages: Sequence[Dict[str, Union[str, Any]]],
    phrase_queue: asyncio.Queue,
    client: Optional[AsyncAnthropic] = None
) -> AsyncIterator[str]:
    """
    Stream Anthropic completion and process chunks for phrase extraction.

    Args:
        messages: Conversation messages.
        phrase_queue: Queue for extracted phrases.
        client: Optional Anthropic client.

    Returns:
        Async iterator of streaming text chunks.
    """
    client = client or get_anthropic_client()
    delimiters = Config.TTS_CONFIG.DELIMITERS
    use_segmentation = Config.TTS_CONFIG.USE_SEGMENTATION
    character_max = Config.TTS_CONFIG.CHARACTER_MAXIMUM

    # Pre-compile the delimiter pattern once
    delimiter_pattern = compile_delimiter_pattern(delimiters)

    chunk_queue = asyncio.Queue()

    # Start the chunk processing task
    chunk_processor_task = asyncio.create_task(
        process_chunks(chunk_queue, phrase_queue, delimiter_pattern, use_segmentation, character_max)
    )

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
                yield chunk  # Yield raw chunk to the frontend
                await chunk_queue.put(chunk)  # Send chunk for processing

        await chunk_queue.put(None)  # Signal the end of chunks
        await chunk_processor_task  # Wait for processing to complete

    except Exception as e:
        logger.error(f"Error calling Anthropic API: {e}")
        await phrase_queue.put(None)
        raise HTTPException(status_code=500, detail=f"Error calling Anthropic API: {e}")
