import asyncio
from anthropic import AsyncAnthropic
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from backend.config import Config  # Import the Config class directly

client = AsyncAnthropic()

async def stream_anthropic_completion(messages: list):
    """
    Streams responses from the Anthropic API.

    Args:
        messages (list): The list of message dicts with 'role' and 'content' keys.
        
    Returns:
        StreamingResponse: A response that streams data to the client.
    """
    try:
        async def event_generator():
            async with client.messages.stream(
                max_tokens=Config.ANTHROPIC_MAX_TOKENS,
                messages=messages,
                model=Config.ANTHROPIC_RESPONSE_MODEL,
                system=Config.ANTHROPIC_SYSTEM_PROMPT,  
                temperature=Config.ANTHROPIC_TEMPERATURE,
                top_p=Config.ANTHROPIC_TOP_P,
                stop_sequences=Config.ANTHROPIC_STOP_SEQUENCES,
            ) as stream:
                async for text_chunk in stream.text_stream:
                    yield text_chunk

        return StreamingResponse(event_generator(), media_type="text/plain")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calling Anthropic API: {str(e)}")