import asyncio
import logging
import re
from typing import Any, AsyncIterator, Dict, List, Optional, Sequence, Union

from groq import AsyncGroq
from fastapi import HTTPException

from backend.config import Config
from backend.config.clients import get_groq_client

# Initialize a logger for the module
logger = logging.getLogger(__name__)

def extract_content_from_groq_chunk(chunk: Any) -> Optional[str]:
    """
    Extracts the content string from GROQ's ChatCompletionChunk.

    Args:
        chunk (Any): The chunk object from GROQ's streaming response.

    Returns:
        Optional[str]: The extracted content string or None if not available.
    """
    try:
        # Access the first choice's delta content directly
        return chunk.choices[0].delta.content
    except (IndexError, AttributeError) as e:
        logger.warning(f"Unexpected chunk format: {chunk}. Error: {e}")
        return None


def compile_delimiter_pattern(delimiters: List[str]) -> Optional[re.Pattern]:
    """
    Compile a regex pattern for a list of delimiters, optimized for speed.

    Args:
        delimiters (List[str]): List of delimiter strings.

    Returns:
        Optional[re.Pattern]: Precompiled regex pattern or None if no delimiters are provided.

    This function processes the list of delimiters by:
    1. Sorting them by length in descending order to ensure longer delimiters are matched first.
    2. Escaping special characters in each delimiter to ensure they are treated as literal strings in the regex.
    3. Joining the processed delimiters with '|' for alternation, enabling the regex engine to match any of them.
    """
    if not delimiters:
        return None

    # Sort delimiters by length (descending) to prioritize longer matches
    sorted_delimiters = sorted(delimiters, key=len, reverse=True)

    # Escape special characters in each delimiter
    escaped_delimiters = map(re.escape, sorted_delimiters)

    # Join the escaped delimiters with '|' for regex alternation and compile
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
        content = extract_content_from_groq_chunk(chunk)
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

async def stream_groq_completion(
    messages: Sequence[Dict[str, Union[str, Any]]],
    phrase_queue: asyncio.Queue,
    client: Optional[AsyncGroq] = None
) -> AsyncIterator[str]:
    """
    Stream GROQ completion and process chunks for phrase extraction.

    Args:
        messages (Sequence[Dict[str, Union[str, Any]]]): List of conversation messages to send to GROQ.
        phrase_queue (asyncio.Queue): Queue to enqueue extracted phrases for downstream processing.
        client (Optional[Groq]): Optional GROQ client for making API requests.

    Returns:
        AsyncIterator[str]: Async iterator of streaming text chunks.

    This function handles GROQ's streaming response by:
    1. Sending the conversation messages to GROQ's API.
    2. Streaming chunks of text from the response.
    3. Extracting content from each chunk and yielding it to the frontend.
    4. Enqueuing raw chunks for further processing (e.g., segmentation).
    """
    # Use the provided client or retrieve the default one
    client = client or get_groq_client()

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
        # Send the request to GROQ's API and begin streaming the response
        response = await client.chat.completions.create(
            model=Config.GROQ_RESPONSE_MODEL,
            messages=[{"role": "system", "content": Config.GROQ_SYSTEM_PROMPT}] + messages,
            stream=True,
            temperature=Config.GROQ_TEMPERATURE,
            top_p=Config.GROQ_TOP_P,
            max_tokens=Config.GROQ_MAX_TOKENS,
            stop=Config.GROQ_STOP
        )
        logger.info("GROQ streaming response started.")

        # Stream chunks from the response
        async for chunk in response:
            # Extract and yield the content to the frontend
            content = extract_content_from_groq_chunk(chunk)
            if content:
                yield content
            # Enqueue the raw chunk for processing
            await chunk_queue.put(chunk)

        # Signal the end of the chunk queue and wait for processing to complete
        await chunk_queue.put(None)
        await chunk_processor_task

    except Exception as e:
        # Log any errors and terminate the phrase queue
        logger.error(f"Error during GROQ streaming: {e}")
        await chunk_queue.put(None)  # Ensure processing task can terminate
        raise HTTPException(status_code=500, detail=f"GROQ API error: {e}")