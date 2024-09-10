from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
import asyncio
import queue
from init import stop_event, ANTHROPIC_CONSTANTS, anthropic_client
from services.tts_service import process_streams  # Use shared TTS service
from services.audio_player import find_next_phrase_end

anthropic_router = APIRouter()

@anthropic_router.post("/api/anthropic")
async def anthropic_chat(request: Request):
    stop_event.set()
    await asyncio.sleep(0.1)
    stop_event.clear()

    try:
        data = await request.json()
        messages = [{"role": msg["role"], "content": msg["content"]} for msg in data.get('messages', [])]

        if not messages:
            return {"error": "Prompt is required."}

        phrase_queue, audio_queue = asyncio.Queue(), queue.Queue()

        # Use the OpenAI TTS service, but pass ANTHROPIC_CONSTANTS for voice settings
        asyncio.create_task(process_streams(phrase_queue, audio_queue, ANTHROPIC_CONSTANTS))

        return StreamingResponse(stream_completion(messages, phrase_queue), media_type='text/plain')

    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}

async def stream_completion(messages: list, phrase_queue: asyncio.Queue):
    try:
        async with anthropic_client.messages.stream(
            model=ANTHROPIC_CONSTANTS["DEFAULT_RESPONSE_MODEL"],
            messages=messages,
            max_tokens=1024,
            temperature=ANTHROPIC_CONSTANTS["TEMPERATURE"]
        ) as stream:
            working_string = ""
            in_code_block = False

            async for chunk in stream.text_stream:
                if stop_event.is_set():
                    await phrase_queue.put(None)
                    return

                content = chunk or ""
                if content:
                    yield content
                    working_string += content

                    while True:
                        next_phrase_end = find_next_phrase_end(working_string)
                        if next_phrase_end == -1:
                            break
                        phrase, working_string = working_string[:next_phrase_end + 1].strip(), working_string[next_phrase_end + 1:]
                        await phrase_queue.put(phrase)

            if working_string.strip():
                await phrase_queue.put(working_string.strip())

            await phrase_queue.put(None)

    except Exception as e:
        await phrase_queue.put(None)
        yield f"Error: {e}"
