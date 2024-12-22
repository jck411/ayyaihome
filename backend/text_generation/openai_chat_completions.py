import asyncio
import logging
import json
import re
from typing import Any, AsyncIterator, Dict, List, Optional, Sequence, Union

from fastapi import HTTPException
from openai import AsyncOpenAI

from backend.config import Config
from backend.config.clients import get_openai_client
from backend.functions.function_schemas import functions, get_time  

logger = logging.getLogger(__name__)

def extract_content_from_openai_chunk(chunk: Any) -> Optional[str]:
    try:
        return chunk.choices[0].delta.content
    except (IndexError, AttributeError) as e:
        logger.warning(f"Unexpected chunk format: {chunk}. Error: {e}")
        return None

def compile_delimiter_pattern(delimiters: List[str]) -> Optional[re.Pattern]:
    if not delimiters:
        return None
    sorted_delimiters = sorted(delimiters, key=len, reverse=True)
    escaped_delimiters = map(re.escape, sorted_delimiters)
    return re.compile("|".join(escaped_delimiters))

async def process_chunks(
    chunk_queue: asyncio.Queue,
    phrase_queue: asyncio.Queue,
    delimiter_pattern: Optional[re.Pattern],
    use_segmentation: bool,
    character_max: int
):
    working_string = ""
    chars_processed_in_segmentation = 0
    segmentation_active = use_segmentation

    while True:
        chunk = await chunk_queue.get()
        if chunk is None:
            if working_string.strip():
                phrase = working_string.strip()
                await phrase_queue.put(phrase)
            await phrase_queue.put(None)
            break

        content = extract_content_from_openai_chunk(chunk)
        if content:
            working_string += content
            if segmentation_active and delimiter_pattern:
                while True:
                    match = delimiter_pattern.search(working_string)
                    if match:
                        end_index = match.end()
                        phrase = working_string[:end_index].strip()
                        if phrase:
                            await phrase_queue.put(phrase)
                            chars_processed_in_segmentation += len(phrase)
                        working_string = working_string[end_index:]
                        if chars_processed_in_segmentation >= character_max:
                            segmentation_active = False
                            break
                    else:
                        break

class FunctionCallDetected(Exception):
    """Raised when a GPT function_call finish_reason is encountered."""
    def __init__(self, info_dict):
        super().__init__("Function call detected")
        self.info = info_dict

async def _stream_response_and_detect_function_call(response, chunk_queue: asyncio.Queue) -> AsyncIterator[str]:
    """
    Streams text from 'response'. If a function call is detected, 
    we capture it and raise a FunctionCallDetected exception.
    """
    full_text = ""
    function_name = None
    function_args_accumulator = ""
    function_call_finished = False

    async for chunk in response:
        # Enqueue chunk for TTS segmentation
        await chunk_queue.put(chunk)

        delta = chunk.choices[0].delta

        # Check for text content
        if hasattr(delta, "content") and delta.content:
            yield delta.content
            full_text += delta.content

        # Check for function call
        if hasattr(delta, "function_call") and delta.function_call is not None:
            if delta.function_call.name:
                function_name = delta.function_call.name
            if delta.function_call.arguments:
                function_args_accumulator += delta.function_call.arguments

        # If the finish reason is "function_call", raise an exception 
        # so we can handle it in the caller
        if chunk.choices[0].finish_reason == "function_call":
            function_call_finished = True
            raise FunctionCallDetected({
                "full_text": full_text,
                "function_name": function_name,
                "function_args": function_args_accumulator,
                "function_call_finished": function_call_finished
            })

    # If we exit the loop normally (finish_reason == "stop"), 
    # then just let the generator end.
    # We do *not* raise StopAsyncIteration.

async def _call_function_locally(function_name: str, arguments: dict) -> str:
    """
    Here is where you dispatch to your actual Python functions by name.
    """
    if function_name == "get_time":
        timezone = arguments.get("timezone", "America/New_York")
        format_value = arguments.get("format", "12-hour")
        date_shift = arguments.get("date_shift", 0)
        response_type = arguments.get("response_type", "both")

        # Decide how to interpret 'format'
        time_format = "12-hour"
        date_format = "MM/DD/YYYY"

        if format_value in ["12-hour", "24-hour"]:
            time_format = format_value
        elif format_value in ["MM/DD/YYYY", "YYYY-MM-DD", "DD/MM/YYYY"]:
            date_format = format_value

        return get_time(
            timezone=timezone,
            time_format=time_format,
            date_format=date_format,
            date_shift=date_shift,
            response_type=response_type,
        )

    # Fallback or unknown function
    return "No suitable function found or function not implemented."

async def stream_openai_completion(
    messages: Sequence[Dict[str, Union[str, Any]]],
    phrase_queue: asyncio.Queue,
    client: Optional[AsyncOpenAI] = None
) -> AsyncIterator[str]:
    """
    Stream OpenAI completion with function-calling.
    If a function call is detected, calls the function, 
    then continues the conversation with the function result.
    """
    client = client or get_openai_client()
    delimiters = Config.TTS_CONFIG.DELIMITERS
    use_segmentation = Config.TTS_CONFIG.USE_SEGMENTATION
    character_max = Config.TTS_CONFIG.CHARACTER_MAXIMUM
    delimiter_pattern = compile_delimiter_pattern(delimiters)

    # Create a queue to hold raw chunks
    chunk_queue = asyncio.Queue()

    # Start the chunk processing task for TTS
    chunk_processor_task = asyncio.create_task(
        process_chunks(chunk_queue, phrase_queue, delimiter_pattern, use_segmentation, character_max)
    )

    # ==========================
    # 1) First streaming call with function_call="auto"
    # ==========================
    try:
        response = await client.chat.completions.create(
            model=Config.LLM_CONFIG.OPENAI_RESPONSE_MODEL,
            messages=messages,
            stream=True,
            temperature=Config.LLM_CONFIG.OPENAI_TEMPERATURE,
            top_p=Config.LLM_CONFIG.OPENAI_TOP_P,
            functions=functions,            # <-- ADDED FOR FUNCTION CALL
            function_call="auto",          # <-- ADDED FOR FUNCTION CALL
        )
        logger.info("OpenAI streaming response started (function_call=auto).")

        # We'll manually catch StopAsyncIteration to know if there's a function call
        stream_generator = _stream_response_and_detect_function_call(response, chunk_queue)
        try:
            async for text_chunk in stream_generator:
                yield text_chunk

        except FunctionCallDetected as exc:
            # info dict about the function call
            info = exc.info
            function_call_finished = info.get("function_call_finished", False)
            function_name = info.get("function_name")
            function_args_str = info.get("function_args", "")

            # If there's a function call, parse arguments:
            if function_call_finished and function_name:
                try:
                    arguments = json.loads(function_args_str) if function_args_str else {}
                except (json.JSONDecodeError, TypeError):
                    arguments = {}

                function_result = await _call_function_locally(function_name, arguments)

                # Now build updated messages with the function result
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

                # Make second call with function_call="none"
                second_response = await client.chat.completions.create(
                    model=Config.LLM_CONFIG.OPENAI_RESPONSE_MODEL,
                    messages=updated_messages,
                    stream=True,
                    temperature=Config.LLM_CONFIG.OPENAI_TEMPERATURE,
                    top_p=Config.LLM_CONFIG.OPENAI_TOP_P,
                    functions=functions,    
                    function_call="none",
                )

                async for chunk in second_response:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, "content") and delta.content:
                        yield delta.content
                        # Also push to TTS
                        await chunk_queue.put(chunk)

    except Exception as e:
        logger.error(f"Error during OpenAI streaming: {e}")
        await chunk_queue.put(None)
        raise HTTPException(status_code=500, detail=f"OpenAI API error: {e}")
    finally:
        # Signal chunk processor to close
        await chunk_queue.put(None)
        await chunk_processor_task
