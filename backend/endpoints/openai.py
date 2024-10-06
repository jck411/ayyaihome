from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
import asyncio
import queue
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
        await tts_manager.stop_active_tts()

        # Parse incoming JSON data from the request
        data = await request.json()
        logger.info(f"Request data: {data}")

        # Extract messages from the request and prepend the system prompt
        messages = [{"role": msg["role"], "content": msg["content"]} for msg in data.get('messages', [])]
        messages.insert(0, OPENAI_CONSTANTS["SYSTEM_PROMPT"])
        logger.info(f"Messages after adding system prompt: {messages}")

        # Determine if TTS (Text-To-Speech) is enabled
        tts_enabled = data.get('ttsEnabled', True)
        logger.info(f"TTS Enabled: {tts_enabled}")

        # Initialize phrase queue only if TTS is enabled
        phrase_queue = None
        if tts_enabled:
            # Create asynchronous and synchronous queues for processing TTS
            phrase_queue = asyncio.Queue()
            audio_queue = queue.Queue()  # Synchronous queue for audio processing
            logger.info("Initialized phrase and audio queues")

            # Start the TTS processing task with required arguments
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


async def stream_completion(messages: list, phrase_queue: asyncio.Queue, model: str = OPENAI_CONSTANTS["DEFAULT_RESPONSE_MODEL"]):
    """
    Streams the response from the OpenAI API.
    """
    try:
        logger.info("Starting stream_completion from OpenAI API")
        # Send the request to the OpenAI API to generate a completion
        response = await aclient.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
            temperature=OPENAI_CONSTANTS["TEMPERATURE"],
            top_p=OPENAI_CONSTANTS["TOP_P"]
        )
        logger.info("Received response from OpenAI API")

        working_string = ""  # To store text content temporarily
        in_code_block = False  # Flag to track whether we are inside a code block

        async for chunk in response:
            # Extract content from the response chunk, if available
            content = getattr(chunk.choices[0].delta, 'content', "") if chunk.choices else ""

            if content:
                logger.debug(f"Streaming content: {content}")
                yield content  # Stream content back to the client
                working_string += content

                # Process phrases to identify and handle code blocks and phrases
                while True:
                    if in_code_block:
                        # Find the end of the code block
                        code_block_end = working_string.find("```", 3)
                        if code_block_end != -1:
                            # Remove the code block from the working string
                            working_string = working_string[code_block_end + 3:]
                            if phrase_queue:
                                await phrase_queue.put("Code presented on screen")
                                logger.info("Code block ended, queued code presented message")
                            in_code_block = False
                        else:
                            break
                    else:
                        # Find the start of the next code block
                        code_block_start = working_string.find("```")
                        if code_block_start != -1:
                            # Extract the phrase before the code block
                            phrase, working_string = working_string[:code_block_start], working_string[code_block_start:]
                            if phrase.strip() and phrase_queue:
                                await phrase_queue.put(phrase.strip())
                                logger.info(f"Queued phrase: {phrase.strip()}")
                            in_code_block = True
                        else:
                            # Find the next phrase ending point
                            next_phrase_end = find_next_phrase_end(working_string)
                            if next_phrase_end == -1:
                                break
                            # Extract the phrase and update the working string
                            phrase, working_string = working_string[:next_phrase_end + 1].strip(), working_string[next_phrase_end + 1:]
                            if phrase_queue and phrase:
                                await phrase_queue.put(phrase)
                                logger.info(f"Queued phrase: {phrase}")

        # Process any remaining text after streaming ends
        while True:
            if in_code_block:
                # Find the end of the code block
                code_block_end = working_string.find("```", 3)
                if code_block_end != -1:
                    # Remove the code block from the working string
                    working_string = working_string[code_block_end + 3:]
                    if phrase_queue:
                        await phrase_queue.put("Code presented on screen")
                        logger.info("Code block ended, queued code presented message")
                    in_code_block = False
                else:
                    break
            else:
                # Find the start of the next code block
                code_block_start = working_string.find("```")
                if code_block_start != -1:
                    # Extract the phrase before the code block
                    phrase, working_string = working_string[:code_block_start], working_string[code_block_start:]
                    if phrase.strip() and phrase_queue:
                        await phrase_queue.put(phrase.strip())
                        logger.info(f"Queued phrase: {phrase.strip()}")
                    in_code_block = True
                else:
                    # Queue any remaining text
                    if working_string.strip() and phrase_queue:
                        await phrase_queue.put(working_string.strip())
                        logger.info(f"Queued remaining working string: {working_string.strip()}")
                        working_string = ''
                    break

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