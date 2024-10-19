# /home/jack/ayyaihome/backend/endpoints/anthropic.py

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
import asyncio
import logging
from init import ANTHROPIC_CONSTANTS, anthropic_client
from services.tts_service import process_streams
from services.audio_player import find_next_phrase_end
from services.tts_manager import tts_manager  # Import TTSManager

logger = logging.getLogger(__name__)

anthropic_router = APIRouter()

@anthropic_router.post("/api/anthropic")
async def anthropic_chat(request: Request):
    """
    Handles POST requests to the "/api/anthropic" endpoint.
    Ensures any active TTS process is stopped before handling a new request.
    """
    try:
        logger.info("Received request at /api/anthropic")
        # Stop any active TTS tasks before handling the new request
        await tts_manager.stop_active_tts()

        # Parse incoming JSON data from the request
        data = await request.json()
        logger.info(f"Request data: {data}")

        # Extract messages from the request
        messages = [{"role": msg["role"], "content": msg["content"]} for msg in data.get('messages', [])]
        logger.info(f"Messages extracted: {messages}")

        if not messages:
            logger.warning("No messages found in the request")
            return {"error": "Prompt is required."}

        # Determine if TTS (Text-To-Speech) is enabled
        tts_enabled = data.get('ttsEnabled', ANTHROPIC_CONSTANTS["FRONTEND_PLAYBACK"])
        logger.info(f"TTS Enabled: {tts_enabled}")

        # Initialize phrase queue and audio queue only if TTS is enabled
        phrase_queue = None
        audio_queue = None
        if tts_enabled:
            # Create asynchronous queues for processing TTS
            phrase_queue = asyncio.Queue()
            audio_queue = asyncio.Queue()
            logger.info("Initialized phrase and audio queues")

            # Start the TTS processing task with required arguments
            tts_task = asyncio.create_task(process_streams(phrase_queue, audio_queue, ANTHROPIC_CONSTANTS))
            tts_manager.register_task(tts_task)
            logger.info("Started TTS processing task")

        # Return a streaming response and pass the phrase queue to handle TTS
        response = StreamingResponse(
            stream_completion(messages, phrase_queue),
            media_type='text/plain'
        )
        logger.info("Streaming response initialized")
        return response

    except Exception as e:
        logger.error(f"Error in anthropic_chat: {e}")
        return {"error": f"Unexpected error: {str(e)}"}


async def stream_completion(messages: list, phrase_queue: asyncio.Queue):
    """
    Streams the response from the Anthropic API and processes phrases for TTS.
    """
    try:
        logger.info("Starting to stream completion from Anthropic API")
        # Send the request to the Anthropic API to generate a completion
        async with anthropic_client.messages.stream(
            model=ANTHROPIC_CONSTANTS["MODEL"],
            messages=messages,
            max_tokens=ANTHROPIC_CONSTANTS["MAX_TOKENS"],
            temperature=ANTHROPIC_CONSTANTS["TEMPERATURE"],
            system=ANTHROPIC_CONSTANTS["SYSTEM_PROMPT"]["content"]  # Top-level system prompt parameter
        ) as stream:
            working_string = ""
            in_code_block = False
            last_phrase = ""

            # Stream the response chunks as they arrive
            async for chunk in stream.text_stream:
                content = chunk or ""
                if content:
                    logger.debug(f"Received chunk: {content}")
                    yield content  # Stream content back to the client
                    working_string += content

                    # Process the working string to handle code blocks and phrases
                    working_string, in_code_block, last_phrase = await process_working_string(
                        working_string, in_code_block, phrase_queue, last_phrase
                    )

        # Process any remaining text after streaming ends
        if working_string.strip():
            working_string, in_code_block, last_phrase = await process_working_string(
                working_string, in_code_block, phrase_queue, last_phrase, final=True
            )

        # End the TTS processing
        if phrase_queue:
            await phrase_queue.put(None)
            logger.info("Queued None to indicate end of TTS")

    except Exception as e:
        logger.error(f"Error during streaming: {str(e)}")
        if phrase_queue:
            await phrase_queue.put(None)
        yield f"Error: {e}"


async def process_working_string(
    working_string: str,
    in_code_block: bool,
    phrase_queue: asyncio.Queue,
    last_phrase: str,
    final: bool = False
):
    """
    Processes the working string to extract phrases and handle code blocks.

    :param working_string: The accumulated text
    :param in_code_block: Flag indicating if currently in a code block
    :param phrase_queue: Queue to send phrases for TTS processing
    :param last_phrase: The last phrase that was queued
    :param final: Flag indicating if this is the final call (after streaming ends)
    :return: Tuple of updated (working_string, in_code_block, last_phrase)
    """
    while True:
        if in_code_block:
            code_block_end = working_string.find("```", 3)
            if code_block_end != -1:
                # Exiting code block
                working_string = working_string[code_block_end + 3:]
                if phrase_queue:
                    await phrase_queue.put("Code presented on screen.")
                    logger.info("Code block ended, queued code presentation message.")
                in_code_block = False
            else:
                # Still inside code block
                break
        else:
            code_block_start = working_string.find("```")
            if code_block_start != -1:
                # Entering code block
                phrase, working_string = working_string[:code_block_start], working_string[code_block_start:]
                phrase = phrase.strip()
                if phrase and phrase_queue and phrase != last_phrase:
                    await phrase_queue.put(phrase)
                    logger.info(f"Queued phrase: {phrase}")
                    last_phrase = phrase
                in_code_block = True
            else:
                # Look for sentence endings
                next_phrase_end = find_next_phrase_end(working_string)
                if next_phrase_end == -1:
                    if final and working_string.strip() and phrase_queue and working_string.strip() != last_phrase:
                        phrase = working_string.strip()
                        await phrase_queue.put(phrase)
                        logger.info(f"Queued final phrase: {phrase}")
                        last_phrase = phrase
                        working_string = ""
                    break
                else:
                    # Extract phrase up to the next sentence end
                    phrase, working_string = working_string[:next_phrase_end + 1], working_string[next_phrase_end + 1:]
                    phrase = phrase.strip()
                    if phrase and phrase_queue and phrase != last_phrase:
                        await phrase_queue.put(phrase)
                        logger.info(f"Queued phrase: {phrase}")
                        last_phrase = phrase
    return working_string, in_code_block, last_phrase
