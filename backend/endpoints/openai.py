# /home/jack/ayyaihome/backend/endpoints/openai.py

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
import asyncio
import queue
from threading import Event
from init import OPENAI_CONSTANTS, aclient
from services.tts_service import process_streams
from services.audio_player import find_next_phrase_end
import uuid
from stop_events import stop_events  # Import stop_events from the new module

openai_router = APIRouter()

@openai_router.post("/api/openai")
async def openai_stream(request: Request):
    """
    Handles POST requests to the "/api/openai" endpoint.
    """
    # Generate a unique request ID
    request_id = str(uuid.uuid4())
    stop_event = Event()
    stop_events[request_id] = stop_event

    try:
        # Parse incoming data
        data = await request.json()
        messages = [{"role": msg["role"], "content": msg["content"]} for msg in data.get('messages', [])]
        messages.insert(0, OPENAI_CONSTANTS["SYSTEM_PROMPT"])  # Add system prompt

        tts_enabled = data.get('ttsEnabled', True)  # Get TTS enabled state from the request

        # Initialize phrase queue only if TTS is enabled
        phrase_queue = None
        if tts_enabled:
            phrase_queue = asyncio.Queue()
            audio_queue = queue.Queue()  # Synchronous queue for audio processing

            # Use OpenAI TTS service with OpenAI-specific constants
            asyncio.create_task(process_streams(phrase_queue, audio_queue, OPENAI_CONSTANTS, stop_event))

        # Return a streaming response and pass the phrase queue to handle TTS
        response = StreamingResponse(
            stream_completion(messages, phrase_queue, stop_event, request_id),
            media_type='text/plain'
        )
        # Include the request ID in the response headers
        response.headers['X-Request-ID'] = request_id
        return response

    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}

async def stream_completion(messages: list, phrase_queue: asyncio.Queue, stop_event: Event, request_id: str, model: str = OPENAI_CONSTANTS["DEFAULT_RESPONSE_MODEL"]):
    """
    Streams the response from the OpenAI API.
    """
    try:
        # Send the request to OpenAI API
        response = await aclient.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
            temperature=OPENAI_CONSTANTS["TEMPERATURE"],
            top_p=OPENAI_CONSTANTS["TOP_P"],
        )

        working_string = ""
        in_code_block = False

        async for chunk in response:
            if stop_event.is_set():
                if phrase_queue:
                    await phrase_queue.put(None)
                break

            # Check if the response chunk is valid
            content = ""
            if chunk.choices and hasattr(chunk.choices[0].delta, 'content'):
                content = chunk.choices[0].delta.content or ""

            if content:
                yield content  # Stream content back to the client
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
                    if working_string.strip() and phrase_queue:
                        await phrase_queue.put(working_string.strip())
                        working_string = ''
                    break

        # End of TTS
        if phrase_queue:
            await phrase_queue.put(None)

        # Remove stop_event after processing
        if request_id in stop_events:
            del stop_events[request_id]

    except Exception as e:
        if phrase_queue:
            await phrase_queue.put(None)
        # Remove stop_event in case of error
        if request_id in stop_events:
            del stop_events[request_id]
        yield f"Error: {e}"
