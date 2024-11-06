from backend.config import aclient, logger


async def generate_text_stream_async(messages):
    """
    Async generator function for asynchronous text stream from OpenAI.

    Parameters:
        messages (list): List of message dictionaries with role and content.

    Yields:
        str: Text chunks from OpenAI response for TTS.
    """
    response = await aclient.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        stream=True,
    )
    async for chunk in response:
        text_chunk = chunk.choices[0].delta.get("content")
        if text_chunk:
            yield text_chunk
