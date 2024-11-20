# backend/text_generation/anthropic_chat_completions.py

import asyncio
import time
import logging
from typing import List, Dict, Optional

from anthropic import AsyncAnthropic
from fastapi import HTTPException

from backend.config import Config

logger = logging.getLogger(__name__)

async def stream_anthropic_completion(
    messages: List[Dict[str, str]],
    phrase_queue: asyncio.Queue,
    request_timestamp: float,
    anthropic_client: Optional[AsyncAnthropic] = None,
    tts_process_chunk: Optional[callable] = None  # TTS processing function
):
    """
    Streams responses from the Anthropic API with real-time TTS.

    Args:
        messages (List[Dict[str, str]]): List of message dicts with 'role' and 'content'.
        phrase_queue (asyncio.Queue): Queue to hold segmented phrases.
        request_timestamp (float): Timestamp when the request was received.
        anthropic_client (Optional[AsyncAnthropic]): Anthropic client instance.
        tts_process_chunk (Optional[callable]): Function to process each chunk for TTS.
    """
    anthropic_client = anthropic_client or AsyncAnthropic()
    working_string = ""
    first_text_timestamp = None

    try:
        async with anthropic_client.messages.stream(
            max_tokens=Config.ANTHROPIC_LLM.get('MAX_TOKENS', 1024),
            messages=messages,
            model=Config.ANTHROPIC_LLM.get('RESPONSE_MODEL', 'claude-3'),
            system=Config.ANTHROPIC_LLM.get('SYSTEM_PROMPT', "You are a helpful assistant."),
            temperature=Config.ANTHROPIC_LLM.get('TEMPERATURE', 0.7),
            top_p=Config.ANTHROPIC_LLM.get('TOP_P', 0.9),
            stop_sequences=Config.ANTHROPIC_LLM.get('STOP_SEQUENCES', None),
        ) as stream:
            async for text_chunk in stream.text_stream:
                content = text_chunk or ""
                logger.debug(f"Received chunk: {content}")

                if content:
                    # Log and measure time to first text generation
                    if first_text_timestamp is None:
                        first_text_timestamp = time.time()
                        elapsed_time = first_text_timestamp - request_timestamp
                        logger.info(f"Time to first text generation: {elapsed_time:.2f} seconds")

                    # Yield the chunk immediately to the front end
                    yield content

                    # Send the chunk to TTS for immediate playback
                    if tts_process_chunk:
                        await tts_process_chunk(content)

                    # Append chunk to working string for segmentation
                    working_string += content

                    # Segment phrases dynamically
                    while len(working_string) >= Config.ANTHROPIC_LLM.get('MIN_PHRASE_LENGTH', 50):
                        delimiter_found = False
                        for delimiter in Config.ANTHROPIC_LLM.get('DELIMITERS', {}).keys():
                            index = working_string.find(delimiter, Config.ANTHROPIC_LLM.get('MIN_PHRASE_LENGTH', 50))
                            if index != -1:
                                phrase = working_string[:index + len(delimiter)].strip()
                                working_string = working_string[index + len(delimiter):]
                                await phrase_queue.put(phrase)
                                delimiter_found = True
                                break
                        if not delimiter_found:
                            break  # Wait for more content if no delimiter is found

        # Queue any remaining text
        if working_string.strip():
            await phrase_queue.put(working_string.strip())
        await phrase_queue.put(None)

    except Exception as e:
        logger.error(f"Error in stream_anthropic_completion: {e}")
        await phrase_queue.put(None)
        yield f"Error: {e}"
