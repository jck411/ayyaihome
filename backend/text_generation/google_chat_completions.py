import asyncio
from typing import List, Dict, Any, AsyncIterator
import google.generativeai as genai
from fastapi import HTTPException
import logging

from backend.config import Config
from backend.config.clients import get_google_client
from backend.phrase_accumulator import PhraseAccumulator
from backend.text_generation.stream_handler import handle_streaming, extract_content_from_gemini_chunk

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
        messages (list[dict]): List of message dictionaries with role and content keys.
        phrase_queue (asyncio.Queue): Queue to handle processed phrases.

    Yields:
        AsyncIterator[str]: The streamed content strings.
    """
    logger.info("Starting stream_google_completion...")  # Log function start

    try:
        # Initialize the Google client here
        google_client = get_google_client()

        # Extract client properties from the injected dictionary
        api_key = google_client["api_key"]
        model_version = google_client["model_version"]

        # Configure the SDK and initialize the model
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_version)
        logger.info(f"Google Gemini client initialized with model version: {model_version}")

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

# Example usage (optional for testing purposes)
async def main():
    # Define your messages and phrase queue
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Can you summarize the benefits of client injection?"}
    ]
    phrase_queue = asyncio.Queue()

    try:
        # Call the stream_google_completion function
        async for content in stream_google_completion(messages, phrase_queue):
            print(content)
    except Exception as e:
        print(f"Error in streaming: {e}")

# Run the async main function (optional for testing purposes)
if __name__ == "__main__":
    asyncio.run(main())