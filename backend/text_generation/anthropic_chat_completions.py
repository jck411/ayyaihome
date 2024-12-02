import asyncio
import logging
import re
from typing import List, Dict, Union, Optional, AsyncIterator, Sequence, Any

from anthropic import AsyncAnthropic
from fastapi import HTTPException

from backend.config import Config
from backend.config.clients import get_anthropic_client

# Initialize a logger for the module
logger = logging.getLogger(__name__)

def extract_content_from_anthropic_chunk(chunk: Any) -> Optional[str]:
    """
    Extracts the content string from Anthropic's streaming response.

    Args:
        chunk (Any): The chunk object from Anthropic's streaming response.

    Returns:
        Optional[str]: The extracted content string or None if not available.

    This function assumes that Anthropic's streaming API yields plain text chunks directly.
    If the chunk is not a string, it returns None.
    """
    # Check if the chunk is a string, as Anthropic streams text directly
    if isinstance(chunk, str):
        return chunk
    return None

def compile_delimiter_pattern(delimiters: List[str]) -> Optional[re.Pattern]:
    """
    Compile a regex pattern for a list of delimiters, optimized for speed.

    Args:
        delimiters (List[str]): List of delimiter strings.

    Returns:
        Optional[re.Pattern]: Precompiled regex pattern or None if no delimiters are provided.

    This function processes the list of delimiters by:
    1. Sorting them by length in descending order to prioritize longer matches.
    2. Escaping special characters in each delimiter to ensure they are treated as literal strings.
    3. Joining the processed delimiters with '|' for regex alternation and compiling the pattern.
    """
    if not delimiters:
        return None

    # Sort delimiters by length (descending) to prioritize longer matches
    sorted_delimiters = sorted(delimiters, key=len, reverse=True)

    # Escape special characters in each delimiter
    escaped_delimiters = map(re.escape, sorted_delimiters)

    # Join the escaped delimiters with '|' for alternation and compile
    return re.compile("|".join(escaped_delimiters))

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
        chunk_queue (asyncio.Queue): Queue containing incoming text chunks from the streaming response.
        phrase_queue (asyncio.Queue): Queue to enqueue extracted phrases for downstream processing.
        delimiter_pattern (Optional[re.Pattern]): Precompiled regex pattern for delimiters.
        use_segmentation (bool): Whether to enable segmentation based on delimiters.
        character_max (int): Maximum number of characters to process before stopping segmentation.

    This function processes chunks iteratively, extracting phrases based on the provided delimiter pattern
    and segmentation rules. Remaining unprocessed text is retained in `working_string` until new chunks arrive.
    """
    working_string = ""
    chars_processed_in_segmentation = 0
    segmentation_active = use_segmentation

    while True:
        # Wait for the next chunk from the queue
        chunk = await chunk_queue.get()

        # If the chunk is None, it signals the end of the stream
        if chunk is None:
            # Process any remaining text in the working string
            if working_string.strip():
                phrase = working_string.strip()
                await phrase_queue.put(phrase)

            # Signal the termination of the phrase queue
            await phrase_queue.put(None)
            break

        # Extract content from the chunk
        content = extract_content_from_anthropic_chunk(chunk)
        if content:
            working_string += content

            # Apply segmentation logic if enabled
            if segmentation_active and delimiter_pattern:
                while True:
                    # Search for a delimiter match in the working string
                    match = delimiter_pattern.search(working_string)
                    if match:
                        # Extract text up to and including the matched delimiter
                        end_index = match.end()
                        phrase = working_string[:end_index].strip()
                        if phrase:
                            await phrase_queue.put(phrase)
                            chars_processed_in_segmentation += len(phrase)
                        # Update the working string by removing the processed phrase
                        working_string = working_string[end_index:]

                        # Disable segmentation if the character limit is reached
                        if chars_processed_in_segmentation >= character_max:
                            segmentation_active = False
                            break
                    else:
                        # Exit the loop if no more matches are found
                        break

async def stream_anthropic_completion(
    messages: Sequence[Dict[str, Union[str, Any]]],
    phrase_queue: asyncio.Queue,
    client: Optional[AsyncAnthropic] = None
) -> AsyncIterator[str]:
    """
    Stream Anthropic completion and process chunks for phrase extraction.

    Args:
        messages (Sequence[Dict[str, Union[str, Any]]]): List of conversation messages to send to Anthropic.
        phrase_queue (asyncio.Queue): Queue to enqueue extracted phrases for downstream processing.
        client (Optional[AsyncAnthropic]): Optional Anthropic client for making API requests.

    Returns:
        AsyncIterator[str]: Async iterator of streaming text chunks.

    This function handles Anthropic's streaming response by:
    1. Sending the conversation messages to Anthropic's API.
    2. Streaming chunks of text from the response.
    3. Yielding each chunk directly to the frontend.
    4. Enqueuing raw chunks for further processing (e.g., segmentation).
    """
    # Use the provided client or retrieve the default one
    client = client or get_anthropic_client()

    # Retrieve configuration settings for delimiters and segmentation
    delimiters = Config.TTS_CONFIG.DELIMITERS
    use_segmentation = Config.TTS_CONFIG.USE_SEGMENTATION
    character_max = Config.TTS_CONFIG.CHARACTER_MAXIMUM

    # Pre-compile the delimiter pattern once
    delimiter_pattern = compile_delimiter_pattern(delimiters)

    # Create a queue to hold raw chunks
    chunk_queue = asyncio.Queue()

    # Start the chunk processing task
    chunk_processor_task = asyncio.create_task(
        process_chunks(chunk_queue, phrase_queue, delimiter_pattern, use_segmentation, character_max)
    )

    try:
        # Send the request to Anthropic's API and begin streaming the response
        async with client.messages.stream(
            max_tokens=Config.ANTHROPIC_MAX_TOKENS,
            messages=messages,
            model=Config.ANTHROPIC_RESPONSE_MODEL,
            system=Config.ANTHROPIC_SYSTEM_PROMPT,
            temperature=Config.ANTHROPIC_TEMPERATURE,
            top_p=Config.ANTHROPIC_TOP_P,
            stop_sequences=Config.ANTHROPIC_STOP_SEQUENCES,
        ) as stream:
            # Stream chunks from the response
            async for chunk in stream.text_stream:
                yield chunk  # Yield raw chunk to the frontend
                await chunk_queue.put(chunk)  # Enqueue the chunk for processing

        # Signal the end of the chunk queue and wait for processing to complete
        await chunk_queue.put(None)
        await chunk_processor_task

    except Exception as e:
        # Log any errors and terminate the phrase queue
        logger.error(f"Error calling Anthropic API: {e}")
        await phrase_queue.put(None)
        raise HTTPException(status_code=500, detail=f"Error calling Anthropic API: {e}")
