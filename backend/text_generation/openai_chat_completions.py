import asyncio
import time
from typing import List, Dict, Optional
import logging
from openai import AsyncOpenAI
from backend.config import Config, get_openai_client  # Absolute import

# Initialize logging
logger = logging.getLogger(__name__)


async def stream_completion(
    messages: List[Dict[str, str]],
    phrase_queue: asyncio.Queue,
    request_timestamp: float,
    model: str = Config.RESPONSE_MODEL,
    openai_client: Optional[AsyncOpenAI] = None
):
    
    
    """
    Streams the completion from OpenAI and handles phrase segmentation.
    """
    openai_client = openai_client or get_openai_client()
    working_string = ""
    first_text_timestamp = None  # Initialize the first text timestamp
    
    try:
        response = await openai_client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
            temperature=Config.TEMPERATURE,
            top_p=Config.TOP_P,
            stream_options={"include_usage": True},
        )

        async for chunk in response:
            if chunk.choices and hasattr(chunk.choices[0].delta, 'content'):
                content = chunk.choices[0].delta.content or ""

                if content:
                    if first_text_timestamp is None:
                        # Capture the timestamp when the first text is generated
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
        logger.error(f"Error in stream_completion: {e}")
        await phrase_queue.put(None)
        yield f"Error: {e}"
