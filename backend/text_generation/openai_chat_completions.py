# backend/text_generation/openai_chat_completions.py

import asyncio
import time
import logging
from typing import List, Dict, Optional

from backend.config import Config, get_openai_client
from openai import AsyncOpenAI
from fastapi import HTTPException

logger = logging.getLogger(__name__)

async def stream_completion(
    messages: List[Dict[str, str]],
    phrase_queue: asyncio.Queue,
    request_timestamp: float,
    openai_client: Optional[AsyncOpenAI] = None
):
    """
    Streams the completion from OpenAI and handles phrase segmentation.

    Args:
        messages (List[Dict[str, str]]): List of message dicts with 'role' and 'content'.
        phrase_queue (asyncio.Queue): Queue to hold phrases for processing.
        request_timestamp (float): Timestamp when the request was received.
        openai_client (Optional[AsyncOpenAI]): OpenAI client instance.
    """
    openai_client = openai_client or get_openai_client()
    working_string = ""
    first_text_timestamp = None

    try:
        response = await openai_client.chat.completions.create(
            model=Config.OPENAI_LLM.get('RESPONSE_MODEL', 'gpt-4'),
            messages=messages,
            stream=True,
            temperature=Config.OPENAI_LLM.get('TEMPERATURE', 1.0),
            top_p=Config.OPENAI_LLM.get('TOP_P', 1.0),
            stop=Config.OPENAI_LLM.get('STOP', None),
            presence_penalty=Config.OPENAI_LLM.get('PRESENCE_PENALTY', 0.0),
            frequency_penalty=Config.OPENAI_LLM.get('FREQUENCY_PENALTY', 0.0),
            logit_bias=Config.OPENAI_LLM.get('LOGIT_BIAS', None),
            user=Config.OPENAI_LLM.get('USER', None),
            tools=Config.OPENAI_LLM.get('TOOLS', None),
            tool_choice=Config.OPENAI_LLM.get('TOOL_CHOICE', None),
            modalities=Config.OPENAI_LLM.get('MODALITIES', ['text']),
        )

        async for chunk in response:
            if chunk.choices and hasattr(chunk.choices[0].delta, 'content'):
                content = chunk.choices[0].delta.content or ""

                if content:
                    if first_text_timestamp is None:
                        first_text_timestamp = time.time()
                        elapsed_time = first_text_timestamp - request_timestamp
                        logger.info(f"Time to first text generation: {elapsed_time:.2f} seconds")

                    yield content
                    working_string += content

                    # Segment phrases based on delimiters
                    # (Assuming a minimum phrase length from Config)
                    while len(working_string) >= 50:  # Example minimum length
                        delimiter_found = False
                        for delimiter in Config.DELIMITERS.keys():
                            index = working_string.find(delimiter, 50)
                            if index != -1:
                                phrase = working_string[:index + len(delimiter)].strip()
                                working_string = working_string[index + len(delimiter):]
                                await phrase_queue.put(phrase)
                                delimiter_found = True
                                break
                        if not delimiter_found:
                            break  # No delimiter found; wait for more content

        # After streaming, queue any remaining text
        if working_string.strip():
            await phrase_queue.put(working_string.strip())
        await phrase_queue.put(None)

    except Exception as e:
        logger.error(f"Error in stream_completion: {e}")
        await phrase_queue.put(None)
        yield f"Error: {e}"
