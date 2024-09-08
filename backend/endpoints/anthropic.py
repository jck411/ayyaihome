from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
import asyncio
import queue
from init import stop_event, CONSTANTS, anthropic_client
from services.tts_service_openai import process_streams # Import process_streams for TTS handling
from services.audio_player import find_next_phrase_end  # Import find_next_phrase_end for phrase detection

# Define the router for Anthropic-related endpoints
anthropic_router = APIRouter()

@anthropic_router.post("/api/anthropic")
async def anthropic_chat(request: Request):
    """
    Handles POST requests to the "/api/anthropic" endpoint.
    Processes user input, sends it to the Anthropic API for response generation,
    streams the text back, and uses OpenAI TTS to convert the text to speech.
    """
    stop_event.set()  # Signal to stop ongoing tasks
    await asyncio.sleep(0.1)
    stop_event.clear()

    try:
        data = await request.json()
        messages = [{"role": msg["role"], "content": msg["content"]} for msg in data.get('messages', [])]

        if not messages:
            return {"error": "Prompt is required."}

        # Initialize queues for TTS processing
        phrase_queue, audio_queue = asyncio.Queue(), queue.Queue()

        # Start TTS processing in the background (OpenAI TTS)
        asyncio.create_task(process_streams(phrase_queue, audio_queue))

        # Return a streaming response from the Anthropic API
        return StreamingResponse(stream_completion(messages, phrase_queue), media_type='text/plain')

    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


async def stream_completion(messages: list, phrase_queue: asyncio.Queue, model: str = "claude-3-5-sonnet-20240620"):
    """
    Streams the response from the Anthropic API.
    Sends each chunk of the response to the phrase queue for OpenAI TTS processing.
    """
    try:
        async with anthropic_client.messages.stream(
            model=model,
            messages=messages,
            max_tokens=1024,
            temperature=0.7
        ) as stream:
            working_string = ""
            in_code_block = False

            async for chunk in stream.text_stream:
                if stop_event.is_set():  # Stop streaming if the event is triggered
                    await phrase_queue.put(None)
                    return

                content = chunk or ""

                if content:
                    yield content  # Stream content back to client
                    working_string += content  # Accumulate the content

                    while True:
                        code_block_start = working_string.find("```")

                        if in_code_block:
                            code_block_end = working_string.find("```", 3)
                            if code_block_end != -1:
                                working_string = working_string[code_block_end + 3:]
                                await phrase_queue.put("Code presented on screen")
                                in_code_block = False
                            else:
                                break
                        else:
                            if code_block_start != -1:
                                phrase, working_string = working_string[:code_block_start], working_string[code_block_start:]
                                if phrase.strip():
                                    await phrase_queue.put(phrase.strip())
                                in_code_block = True
                            else:
                                next_phrase_end = find_next_phrase_end(working_string)
                                if next_phrase_end == -1:
                                    break
                                phrase, working_string = working_string[:next_phrase_end + 1].strip(), working_string[next_phrase_end + 1:]
                                await phrase_queue.put(phrase)

            if working_string.strip() and not in_code_block:
                await phrase_queue.put(working_string.strip())

            await phrase_queue.put(None)  # Signal the end of the stream to the TTS processor

    except Exception as e:
        print(f"Error in stream_completion: {e}")
        await phrase_queue.put(None)
        yield f"Error: {e}"

