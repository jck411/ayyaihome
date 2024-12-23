# /home/jack/ayyaihome/backend/text_generation/function_call_handler.py

import asyncio
from typing import Any, AsyncIterator, Dict
from fastapi import HTTPException
from .logging_config import logger


class FunctionCallDetected(Exception):
    """
    Raised when a GPT function_call finish_reason is encountered.
    """
    def __init__(self, info_dict):
        super().__init__("Function call detected")
        self.info = info_dict


async def _stream_response_and_detect_function_call(
    response: Any, 
    chunk_queue: asyncio.Queue
) -> AsyncIterator[str]:
    """
    Streams OpenAI response data while detecting and responding to function calls.
    Yields text chunks and raises FunctionCallDetected if the completion calls a function.
    """
    logger.info("Started _stream_response_and_detect_function_call coroutine.")

    full_text = ""
    function_name = None
    function_args_accumulator = ""
    function_call_finished = False

    try:
        async for chunk in response:
            logger.debug(f"Streaming chunk received: {chunk}")
            # Enqueue chunk for TTS segmentation
            await chunk_queue.put(chunk)

            delta = chunk.choices[0].delta

            # Check for text content
            if hasattr(delta, "content") and delta.content:
                logger.debug(f"Yielding text chunk: {delta.content}")
                yield delta.content
                full_text += delta.content

            # Check for function call
            if hasattr(delta, "function_call") and delta.function_call is not None:
                if delta.function_call.name:
                    function_name = delta.function_call.name
                    logger.info(f"Function call detected: {function_name}")
                if delta.function_call.arguments:
                    function_args_accumulator += delta.function_call.arguments
                    logger.debug(f"Accumulated function arguments: {function_args_accumulator}")

            # Check if finish_reason indicates a function call
            if chunk.choices[0].finish_reason == "function_call":
                function_call_finished = True
                logger.info("Finish reason is function_call. Raising FunctionCallDetected.")
                raise FunctionCallDetected({
                    "full_text": full_text,
                    "function_name": function_name,
                    "function_args": function_args_accumulator,
                    "function_call_finished": function_call_finished
                })

    except Exception as e:
        logger.error(f"Error in _stream_response_and_detect_function_call: {e}", exc_info=True)
        raise
    finally:
        logger.info("Exiting _stream_response_and_detect_function_call coroutine.")
