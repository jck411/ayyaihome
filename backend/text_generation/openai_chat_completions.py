# /path/to/your/project/text_generation/openai_chat_completions.py

import asyncio
from typing import List, Dict, Optional
from openai import AsyncOpenAI
from backend.config import Config, get_openai_client
from backend.TTS.phrase_preparation.phrase_segmentation import segment_and_dispatch_phrases 

async def stream_completion(
    messages: List[Dict[str, str]],
    phrase_queue: asyncio.Queue,
    openai_client: Optional[AsyncOpenAI] = None
):
    """
    Streams the completion from OpenAI and handles phrase segmentation.
    """
    openai_client = openai_client or get_openai_client()
    working_string = ""

    try:
        # Use model from Config.RESPONSE_MODEL, which loads from config.yaml
        response = await openai_client.chat.completions.create(
            model=Config.RESPONSE_MODEL,
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
                    yield content  # Stream to front end immediately

                    # Use the shared utility function
                    working_string = await segment_and_dispatch_phrases(
                        working_string,
                        content,
                        phrase_queue,
                        Config
                    )

        # Handle any remaining content
        if working_string.strip():
            await phrase_queue.put(working_string.strip())
        await phrase_queue.put(None)

    except Exception as e:
        await phrase_queue.put(None)
        yield f"Error: {e}"
