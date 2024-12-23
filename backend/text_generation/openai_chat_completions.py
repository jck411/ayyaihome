# /home/jack/ayyaihome/backend/text_generation/openai_chat_completions.py

import asyncio
import json
import re
from typing import Any, AsyncIterator, Dict, List, Optional, Sequence, Union

from fastapi import HTTPException
from openai import AsyncOpenAI

# Local imports
from .logging_config import logger
from .function_call_handler import (
    _stream_response_and_detect_function_call,
    FunctionCallDetected,
)
from .function_dispatcher import _call_function_locally

# Your config imports
from backend.config import Config
from backend.config.clients import get_openai_client

# Import schemas from modularized files
from backend.functions.get_weather import get_weather_schema
from backend.functions.get_time import get_time_schema

# Assemble the functions list
functions = [get_weather_schema, get_time_schema]


def extract_content_from_openai_chunk(chunk: Any) -> Optional[str]:
    """
    Extracts the text content from a response chunk returned by OpenAI.
    """
    logger.debug(f"Extracting content from chunk: {chunk}")
    try:
        content = chunk.choices[0].delta.content
        logger.debug(f"Extracted content: {content}")
        return content
    except (IndexError, AttributeError) as e:
        logger.warning(f"Unexpected chunk format: {chunk}. Error: {e}")
        return None


def compile_delimiter_pattern(delimiters: List[str]) -> Optional[re.Pattern]:
    """
    Compiles a regex pattern to match any of the provided delimiters.
    """
    logger.debug(f"Compiling delimiter pattern from delimiters: {delimiters}")
    if not delimiters:
        logger.debug("No delimiters provided, returning None.")
        return None
    sorted_delimiters = sorted(delimiters, key=len, reverse=True)
    escaped_delimiters = map(re.escape, sorted_delimiters)
    pattern = re.compile("|".join(escaped_delimiters))
    logger.debug(f"Compiled delimiter pattern: {pattern.pattern}")
    return pattern


async def process_chunks(
    chunk_queue: asyncio.Queue,
    phrase_queue: asyncio.Queue,
    delimiter_pattern: Optional[re.Pattern],
    use_segmentation: bool,
    character_max: int
):
    """
    Processes chunks of text from the chunk_queue and segments them into phrases.
    """
    logger.info("Started process_chunks coroutine.")
    working_string = ""
    chars_processed_in_segmentation = 0
    segmentation_active = use_segmentation

    while True:
        chunk = await chunk_queue.get()
        logger.debug(f"Received chunk in process_chunks: {chunk}")
        if chunk is None:
            logger.debug("Received termination signal in process_chunks.")
            if working_string.strip():
                phrase = working_string.strip()
                logger.debug(f"Enqueuing final phrase: {phrase}")
                await phrase_queue.put(phrase)
            await phrase_queue.put(None)
            break

        content = extract_content_from_openai_chunk(chunk)
        if content:
            working_string += content
            logger.debug(f"Updated working_string: {working_string}")
            if segmentation_active and delimiter_pattern:
                while True:
                    match = delimiter_pattern.search(working_string)
                    if match:
                        end_index = match.end()
                        phrase = working_string[:end_index].strip()
                        if phrase:
                            logger.debug(f"Enqueuing segmented phrase: {phrase}")
                            await phrase_queue.put(phrase)
                            chars_processed_in_segmentation += len(phrase)
                        working_string = working_string[end_index:]
                        logger.debug(f"Remaining working_string after segmentation: {working_string}")
                        if chars_processed_in_segmentation >= character_max:
                            logger.info("Character max reached. Disabling segmentation.")
                            segmentation_active = False
                            break
                    else:
                        break

    logger.info("Exiting process_chunks coroutine.")


async def stream_openai_completion(
    messages: Sequence[Dict[str, Union[str, Any]]],
    phrase_queue: asyncio.Queue,
    client: Optional[AsyncOpenAI] = None
) -> AsyncIterator[str]:
    """
    Streams OpenAI completion responses, handling potential function calls.
    """
    logger.info("Started stream_openai_completion coroutine.")
    client = client or get_openai_client()

    # Prepare TTS segmentation
    delimiters = Config.TTS_CONFIG.DELIMITERS
    use_segmentation = Config.TTS_CONFIG.USE_SEGMENTATION
    character_max = Config.TTS_CONFIG.CHARACTER_MAXIMUM
    delimiter_pattern = compile_delimiter_pattern(delimiters)

    # Create a queue to hold raw chunks
    chunk_queue = asyncio.Queue()

    # Start the chunk processing task
    logger.debug("Starting chunk_processor_task.")
    chunk_processor_task = asyncio.create_task(
        process_chunks(chunk_queue, phrase_queue, delimiter_pattern, use_segmentation, character_max)
    )

    try:
        # ==========================
        # 1) First streaming call with function_call="auto"
        # ==========================
        logger.info("Making first OpenAI API call with function_call='auto'.")
        response = await client.chat.completions.create(
            model=Config.LLM_CONFIG.OPENAI_RESPONSE_MODEL,
            messages=messages,
            stream=True,
            temperature=Config.LLM_CONFIG.OPENAI_TEMPERATURE,
            top_p=Config.LLM_CONFIG.OPENAI_TOP_P,
            functions=functions,            # For function calls
            function_call="auto",          # Auto-detect function calls
        )
        logger.info("OpenAI streaming response started (function_call=auto).")

        # We'll manually catch the function call
        stream_generator = _stream_response_and_detect_function_call(response, chunk_queue)
        try:
            async for text_chunk in stream_generator:
                logger.debug(f"Yielding text_chunk: {text_chunk}")
                yield text_chunk

        except FunctionCallDetected as exc:
            # Extract info about the function call
            info = exc.info
            function_call_finished = info.get("function_call_finished", False)
            function_name = info.get("function_name")
            function_args_str = info.get("function_args", "")

            logger.info(f"Handling function call: {function_name} with args: {function_args_str}")

            # If there's a function call, parse arguments
            if function_call_finished and function_name:
                try:
                    arguments = json.loads(function_args_str) if function_args_str else {}
                    logger.debug(f"Parsed function arguments: {arguments}")
                except (json.JSONDecodeError, TypeError) as parse_error:
                    logger.error(f"Error parsing function arguments: {parse_error}", exc_info=True)
                    arguments = {}

                function_result = await _call_function_locally(function_name, arguments)
                logger.info(f"Function '{function_name}' executed with result: {function_result}")

                # Build updated messages with the function result
                updated_messages = list(messages) + [
                    {"role": "assistant", "content": info.get("full_text", "")},
                    {
                        "role": "function",
                        "name": function_name,
                        "content": json.dumps(function_result)
                    },
                    {
                        "role": "system",
                        "content": "Use the function result to provide a final user-facing answer."
                    }
                ]
                logger.debug(f"Updated messages for second API call: {updated_messages}")

                # Make second call with function_call="none"
                logger.info("Making second OpenAI API call with function_call='none'.")
                second_response = await client.chat.completions.create(
                    model=Config.LLM_CONFIG.OPENAI_RESPONSE_MODEL,
                    messages=updated_messages,
                    stream=True,
                    temperature=Config.LLM_CONFIG.OPENAI_TEMPERATURE,
                    top_p=Config.LLM_CONFIG.OPENAI_TOP_P,
                    functions=functions,    
                    function_call="none",
                )
                logger.info("OpenAI streaming response started (function_call=none).")

                async for chunk in second_response:
                    logger.debug(f"Second streaming chunk received: {chunk}")
                    delta = chunk.choices[0].delta
                    if hasattr(delta, "content") and delta.content:
                        logger.debug(f"Yielding second text chunk: {delta.content}")
                        yield delta.content
                        # Also push to TTS
                        await chunk_queue.put(chunk)

    except HTTPException as http_exc:
        logger.error(f"HTTPException during OpenAI streaming: {http_exc.detail}", exc_info=True)
        await chunk_queue.put(None)
        raise http_exc
    except Exception as e:
        logger.error(f"Unexpected error during OpenAI streaming: {e}", exc_info=True)
        await chunk_queue.put(None)
        raise HTTPException(status_code=500, detail=f"OpenAI API error: {e}")
    finally:
        # Signal the chunk processor to close
        logger.debug("Signaling chunk_processor_task to terminate.")
        await chunk_queue.put(None)
        await chunk_processor_task
        logger.info("Exiting stream_openai_completion coroutine.")
