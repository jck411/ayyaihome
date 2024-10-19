from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
import asyncio
import logging
from init import OPENAI_CONSTANTS, aclient
from services.tts_service import process_streams
from services.audio_player import find_next_phrase_end
from services.tts_manager import tts_manager  # Import TTSManager

logger = logging.getLogger(__name__)

openai_router = APIRouter()

@openai_router.post("/api/openai")
async def openai_stream(request: Request):
    """
    Handles POST requests to the "/api/openai" endpoint.
    Ensures any active TTS process is stopped before handling a new request.
    """
    try:
        logger.info("Received request at /api/openai")
        
        # Stop any active TTS tasks before handling the new request
        await tts_manager.stop_active_tts()  # Ensure this doesn't block starting new task

        # Parse incoming JSON data from the request
        data = await request.json()
        logger.info(f"Request data: {data}")

        # Extract messages from the request and prepend the system prompt from OPENAI_CONSTANTS
        messages = [{"role": msg["role"], "content": msg["content"]} for msg in data.get('messages', [])]
        messages.insert(0, OPENAI_CONSTANTS["SYSTEM_PROMPT"])
        logger.info(f"Messages after adding system prompt: {messages}")

        # Determine if TTS (Text-To-Speech) is enabled (default from OPENAI_CONSTANTS)
        tts_enabled = data.get('ttsEnabled', OPENAI_CONSTANTS["FRONTEND_PLAYBACK"])
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
            # Start the new task immediately after stopping the old task
            tts_task = asyncio.create_task(process_streams(phrase_queue, audio_queue, OPENAI_CONSTANTS))
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
        logger.error(f"Error in openai_stream: {e}")
        return {"error": f"Unexpected error: {str(e)}"}


async def stream_completion(messages: list, phrase_queue: asyncio.Queue, model: str = OPENAI_CONSTANTS["MODEL"]):
    """
    Streams the response from the OpenAI API and processes phrases for TTS.

    :param messages: List of conversation messages
    :param phrase_queue: Queue to send phrases for TTS processing
    :param model: OpenAI model to use for completion
    """
    try:
        logger.info("Starting stream_completion from OpenAI API")
        # Send the request to the OpenAI API to generate a completion
        response = await aclient.chat.completions.create(
            model=model,
            messages=messages,
            stream=OPENAI_CONSTANTS["STREAM"],
            temperature=OPENAI_CONSTANTS["TEMPERATURE"],
            top_p=OPENAI_CONSTANTS["TOP_P"],
            max_tokens=OPENAI_CONSTANTS["MAX_TOKENS"],
            frequency_penalty=OPENAI_CONSTANTS["FREQUENCY_PENALTY"],
            presence_penalty=OPENAI_CONSTANTS["PRESENCE_PENALTY"],
            stop=OPENAI_CONSTANTS["STOP"],
            logit_bias=OPENAI_CONSTANTS["LOGIT_BIAS"]
        )
        logger.info("Received response from OpenAI API")

        working_string = ""
        in_code_block = False
        last_phrase = ""

        async for chunk in response:
            # Extract content from the response chunk, if available
            content = getattr(chunk.choices[0].delta, 'content', "") if chunk.choices else ""

            if content:
                logger.debug(f"Streaming content: {content}")
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

        # End of TTS - indicate that no more phrases will be sent
        if phrase_queue:
            await phrase_queue.put(None)
            logger.info("Queued None to indicate end of TTS")

    except Exception as e:
        # Handle exceptions and ensure the phrase queue ends properly
        if phrase_queue:
            await phrase_queue.put(None)
        yield f"Error: {e}"
        logger.error(f"Yielding error: {e}")


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
