import asyncio
from typing import List, Dict, Any, AsyncIterator
from fastapi import HTTPException
import google.generativeai as genai
from backend.config import Config
from backend.phrase_accumulator import PhraseAccumulator
from backend.text_generation.stream_handler import handle_streaming, extract_content_from_gemini_chunk
import os
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

async def stream_google_completion(
    messages: List[Dict[str, str]],
    phrase_queue: asyncio.Queue
) -> AsyncIterator[str]:
    """
    Streams completion from Google's Gemini API and processes the text.

    Args:
        messages (list[dict]): List of message dictionaries with `role` and `content` keys.
        phrase_queue (asyncio.Queue): Queue to handle processed phrases.

    Yields:
        AsyncIterator[str]: The streamed content strings.
    """
    try:
        logger.debug("Starting stream_google_completion...")
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

        logger.debug(f"Complete prompt for generation: {complete_prompt}")

        # Generate content asynchronously with the system prompt
        response = await model.generate_content_async(complete_prompt, stream=True)

        # Initialize PhraseAccumulator
        accumulator = PhraseAccumulator(Config, phrase_queue)

        # Use handle_streaming to process the stream
        async for content in handle_streaming(
            response,
            accumulator,
            content_extractor=extract_content_from_gemini_chunk,
            api_name="Google Gemini"
        ):
            logger.debug(f"Streaming content: {content}")  # Log each streamed content part
            print(f"Output content: {content}")  # Print each streamed content part for visibility
            yield content

    except Exception as e:
        await phrase_queue.put(None)
        logger.error(f"Exception occurred in stream_google_completion: {e}")
        raise HTTPException(status_code=500, detail=f"Error calling Google's Gemini API: {e}")
