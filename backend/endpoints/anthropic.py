# /home/jack/ayyaihome/backend/endpoints/anthropic.py

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
import asyncio
import queue
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
    logger.info("Received request at /api/anthropic")

    try:
        # Stop any active TTS tasks before handling the new request
        await tts_manager.stop_active_tts()

        # Parse incoming data
        data = await request.json()
        logger.info(f"Parsed request data: {data}")
        messages = [{"role": msg["role"], "content": msg["content"]} for msg in data.get('messages', [])]

        if not messages:
            logger.warning("No messages found in the request")
            return {"error": "Prompt is required."}

        tts_enabled = data.get('ttsEnabled', True)  # Get TTS enabled state from the request
        logger.info(f"TTS Enabled: {tts_enabled}")

        # Initialize phrase queue only if TTS is enabled
        phrase_queue = None
        if tts_enabled:
            phrase_queue = asyncio.Queue()
            audio_queue = queue.Queue()  # Synchronous queue for audio processing

            # Start TTS processing in the background
            logger.info("Starting TTS processing")
            tts_task = asyncio.create_task(process_streams(phrase_queue, audio_queue, ANTHROPIC_CONSTANTS))
            tts_manager.register_task(tts_task)

        # Stream response back to the client
        response = StreamingResponse(
            stream_completion(messages, phrase_queue),
            media_type='text/plain'
        )
        logger.info("Sending response with streaming content")
        return response

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {"error": f"Unexpected error: {str(e)}"}


async def stream_completion(messages: list, phrase_queue: asyncio.Queue):
    """
    Streams the response from the Anthropic API.
    """
    try:
        # Request the response from the Anthropic API with the top-level system prompt
        logger.info("Starting to stream completion from Anthropic API")
        async with anthropic_client.messages.stream(
            model=ANTHROPIC_CONSTANTS["DEFAULT_RESPONSE_MODEL"],
            messages=messages,
            max_tokens=1024,
            temperature=ANTHROPIC_CONSTANTS["TEMPERATURE"],
            system=ANTHROPIC_CONSTANTS["SYSTEM_PROMPT"]["content"]  # Top-level system prompt parameter
        ) as stream:
            working_string = ""  # Accumulates the full response
            in_code_block = False  # Track whether we're inside a code block

            # Stream the response chunks as they arrive
            async for chunk in stream.text_stream:
                content = chunk or ""
                if content:
                    logger.debug(f"Received chunk: {content}")
                    yield content
                    working_string += content

                    # Process phrases
                    while True:
                        if in_code_block:
                            code_block_end = working_string.find("```", 3)
                            if code_block_end != -1:
                                working_string = working_string[code_block_end + 3:]
                                if phrase_queue:
                                    await phrase_queue.put("Code presented on screen")
                                in_code_block = False
                            else:
                                break
                        else:
                            code_block_start = working_string.find("```")
                            if code_block_start != -1:
                                phrase, working_string = working_string[:code_block_start], working_string[code_block_start:]
                                if phrase.strip() and phrase_queue:
                                    await phrase_queue.put(phrase.strip())
                                in_code_block = True
                            else:
                                next_phrase_end = find_next_phrase_end(working_string)
                                if next_phrase_end == -1:
                                    break
                                phrase, working_string = working_string[:next_phrase_end + 1].strip(), working_string[next_phrase_end + 1:]
                                if phrase_queue and phrase:
                                    await phrase_queue.put(phrase)

        # Process any remaining text after streaming ends
        while working_string:
            if in_code_block:
                code_block_end = working_string.find("```", 3)
                if code_block_end != -1:
                    working_string = working_string[code_block_end + 3:]
                    if phrase_queue:
                        await phrase_queue.put("Code presented on screen")
                    in_code_block = False
                else:
                    break
            else:
                code_block_start = working_string.find("```")
                if code_block_start != -1:
                    phrase, working_string = working_string[:code_block_start], working_string[code_block_start:]
                    if phrase.strip() and phrase_queue:
                        await phrase_queue.put(phrase.strip())
                    in_code_block = True
                else:
                    if working_string.strip() and phrase_queue:
                        await phrase_queue.put(working_string.strip())
                    working_string = ''

        # End the TTS processing
        if phrase_queue:
            logger.info("Ending TTS processing")
            await phrase_queue.put(None)

    except Exception as e:
        logger.error(f"Error during streaming: {str(e)}")
        if phrase_queue:
            await phrase_queue.put(None)
        yield f"Error: {e}"
