import asyncio
import os
import google.generativeai as genai
from fastapi import HTTPException

async def stream_google_completion(
    messages: list[dict],
    phrase_queue: asyncio.Queue
):
    """
    Streams completion from Google's Gemini API and processes the text.

    Args:
        messages (list[dict]): List of message dictionaries with `role` and `content` keys.
        phrase_queue (asyncio.Queue): Queue to handle processed phrases.
    """
    try:
        # Configure the SDK with your API key
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="GEMINI_API_KEY is not set.")
        
        genai.configure(api_key=api_key)

        # Initialize the model
        model = genai.GenerativeModel("gemini-1.5-flash")

        # Construct the system prompt and user input
        system_prompt = "You are a helpful assistant who writes creative and engaging responses."
        user_inputs = "\n".join(msg["content"] for msg in messages)
        complete_prompt = f"{system_prompt}\n\n{user_inputs}"

        # Generate content asynchronously with the system prompt
        response = await model.generate_content_async(complete_prompt, stream=True)

        # Stream the response
        working_string = ""
        async for chunk in response:
            content = chunk.text or ""
            if content:
                # Yield content for immediate streaming
                yield content

                # Accumulate content
                working_string += content

                # Dispatch content to the queue (optional processing logic here)
                await phrase_queue.put(content)

        # Signal the end of processing
        await phrase_queue.put(None)

    except Exception as e:
        await phrase_queue.put(None)
        raise HTTPException(status_code=500, detail=f"Error calling Google's Gemini API: {e}")
