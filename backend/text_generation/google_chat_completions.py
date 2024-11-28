import asyncio
from typing import List, Dict, Any, AsyncIterator
from fastapi import HTTPException
import google.generativeai as genai

from backend.config import Config
from backend.config.clients import get_google_client

from backend.phrase_accumulator import PhraseAccumulator
from backend.text_generation.stream_handler import handle_streaming, extract_content_from_gemini_chunk
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    logger.info("Starting stream_google_completion...")  # Log function start

    try:
        # Get the API key from the centralized Config
        api_key = Config.LLM_CONFIG.GEMINI_API_KEY
        if not api_key:
            logger.error("GEMINI_API_KEY is not set.")
            raise HTTPException(status_code=500, detail="GEMINI_API_KEY is not set.")

        # Configure the SDK with your API key
        genai.configure(api_key=api_key)
        logger.info("Google Gemini API configured with the provided API key.")

        # Initialize the model using the version from Config
        model_version = Config.LLM_CONFIG.GEMINI_MODEL_VERSION
        model = genai.GenerativeModel(model_version)
        logger.info(f"Using Google Gemini model version: {model_version}")

        # Construct the system prompt and user input
        system_prompt = Config.LLM_CONFIG.GEMINI_SYSTEM_PROMPT
        user_inputs = "\n".join(msg["content"] for msg in messages)
        complete_prompt = f"{system_prompt}\n\n{user_inputs}"

        logger.debug(f"Complete prompt for generation: {complete_prompt}")

        # Generate content asynchronously with the system prompt
        response = await model.generate_content_async(complete_prompt, stream=True)
        logger.info("Content generation initiated with Google Gemini API.")

        # Initialize PhraseAccumulator
        accumulator = PhraseAccumulator(Config, phrase_queue)
        logger.info("PhraseAccumulator initialized.")

        # Use handle_streaming to process the stream
        async for content in handle_streaming(
            response,
            accumulator,
            content_extractor=extract_content_from_gemini_chunk,
            api_name="Google Gemini"
        ):
            logger.info(f"Streamed content: {content}")  # Log streamed content
            yield content

    except Exception as e:
        await phrase_queue.put(None)
        logger.error(f"Exception occurred in stream_google_completion: {e}")
        raise HTTPException(status_code=500, detail=f"Error calling Google's Gemini API: {e}")
    finally:
        logger.info("Finished stream_google_completion.")  # Log function end
