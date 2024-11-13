import anthropic
import asyncio
from typing import List

client = anthropic.Anthropic()

async def stream_completion(messages: List[dict], system: str, phrase_queue: asyncio.Queue, request_timestamp: float):
    """
    Handles message streaming for the Anthropic service.
    """
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=2048,
        system=system,
        messages=messages
    )
    # Code to stream response to phrase_queue
    # Implementation will depend on the Anthropic SDK's capabilities for streaming
