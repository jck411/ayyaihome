from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
import asyncio
import queue  # Import the synchronous queue
from init import stop_event, ANTHROPIC_CONSTANTS, anthropic_client
from services.tts_service import process_streams
from services.audio_player import find_next_phrase_end

# Define the router for Anthropic-related endpoints
anthropic_router = APIRouter()

@anthropic_router.post("/api/anthropic")
async def anthropic_chat(request: Request):
    """
    Handles POST requests to the "/api/anthropic" endpoint.
    Processes user input, sends it to the Anthropic API for response generation, and streams the output back.
    """
    stop_event.set()  # Signal to stop ongoing processes
    await asyncio.sleep(0.1)  # Give a brief delay
    stop_event.clear()  # Clear the stop signal

    try:
        # Parse incoming data
        data = await request.json()
        messages = [{"role": msg["role"], "content": msg["content"]} for msg in data.get('messages', [])]

        if not messages:
            return {"error": "Prompt is required."}

        # Initialize queues for TTS processing
        phrase_queue = asyncio.Queue()
        audio_queue = queue.Queue()  # Changed to synchronous queue.Queue()

        # Start TTS processing in the background
        asyncio.create_task(process_streams(phrase_queue, audio_queue, ANTHROPIC_CONSTANTS))

        # Stream response back to the client
        return StreamingResponse(stream_completion(messages, phrase_queue), media_type='text/plain')

    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


async def stream_completion(messages: list, phrase_queue: asyncio.Queue):
    """
    Streams the response from the Anthropic API.
    Processes each chunk of the response, adds it to the phrase queue for text-to-speech conversion,
    and streams the content back to the client.
    """
    try:
        # Request the response from the Anthropic API
        async with anthropic_client.messages.stream(
            model=ANTHROPIC_CONSTANTS["DEFAULT_RESPONSE_MODEL"],
            messages=messages,
            max_tokens=1024,
            temperature=ANTHROPIC_CONSTANTS["TEMPERATURE"]
        ) as stream:
            working_string = ""  # Accumulates the full response
            in_code_block = False  # Track whether we're inside a code block

            # Stream the response chunks as they arrive
            async for chunk in stream.text_stream:
                if stop_event.is_set():
                    await phrase_queue.put(None)
                    break

                content = chunk or ""
                if content:
                    # Accumulate the response in `working_string`
                    working_string += content

                    # Yield the chunk to stream the content to the frontend
                    yield content

                    # Process code blocks and regular text
                    while True:
                        code_block_start = working_string.find("```")

                        if in_code_block:
                            # Check for the end of the code block
                            code_block_end = working_string.find("```", 3)
                            if code_block_end != -1:
                                # End the code block
                                working_string = working_string[code_block_end + 3:]
                                await phrase_queue.put("Code presented on screen")
                                in_code_block = False
                            else:
                                break
                        else:
                            # Check if the next part is a code block
                            if code_block_start != -1:
                                # Extract phrase before the code block
                                phrase, working_string = working_string[:code_block_start], working_string[code_block_start:]
                                if phrase.strip():
                                    await phrase_queue.put(phrase.strip())
                                in_code_block = True
                            else:
                                # Find the end of the next phrase
                                next_phrase_end = find_next_phrase_end(working_string)
                                if next_phrase_end == -1:
                                    break
                                # Send the phrase for TTS
                                phrase, working_string = working_string[:next_phrase_end + 1].strip(), working_string[next_phrase_end + 1:]
                                await phrase_queue.put(phrase)

        # Send the final accumulated text
        if working_string.strip() and not in_code_block:
            await phrase_queue.put(working_string.strip())

        # End the TTS processing
        await phrase_queue.put(None)

    except asyncio.TimeoutError:
        await phrase_queue.put(None)
    except Exception as e:
        await phrase_queue.put(None)
        yield f"Error: {e}"
