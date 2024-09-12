from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
import asyncio
import queue
from init import stop_event, ANTHROPIC_CONSTANTS, anthropic_client
from services.tts_service import process_streams
from backend.context_manager import get_context, update_context, clear_context

anthropic_router = APIRouter()

@anthropic_router.post("/api/anthropic")
async def anthropic_chat(request: Request):
    stop_event.set()
    await asyncio.sleep(0.1)
    stop_event.clear()

    try:
        data = await request.json()
        current_messages = [{"role": msg["role"], "content": msg["content"]} for msg in data.get('messages', [])]

        if not current_messages or current_messages[0]["role"] != "user":
            return {"error": "The first message must come from the 'user' role."}

        user_id = data["user_id"]
        agent_id = "anthropic"

        context = get_context(user_id, agent_id)
        
        # Combine context with current messages
        messages = context + current_messages

        print(f"[DEBUG] Combined messages: {messages}")

        phrase_queue, audio_queue = asyncio.Queue(), queue.Queue()
        asyncio.create_task(process_streams(phrase_queue, audio_queue, ANTHROPIC_CONSTANTS))

        return StreamingResponse(stream_completion(messages, phrase_queue, user_id, agent_id), media_type='text/plain')

    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}

async def stream_completion(messages: list, phrase_queue: asyncio.Queue, user_id: str, agent_id: str):
    try:
        async with anthropic_client.messages.stream(
            model=ANTHROPIC_CONSTANTS["DEFAULT_RESPONSE_MODEL"],
            messages=messages,
            max_tokens=1024,
            temperature=ANTHROPIC_CONSTANTS["TEMPERATURE"]
        ) as stream:
            working_string = ""
            full_message = ""

            async for chunk in stream.text_stream:
                if stop_event.is_set():
                    await phrase_queue.put(None)
                    return

                content = chunk or ""
                if content:
                    full_message += content
                    yield content
                    working_string += content

            if working_string.strip():
                await phrase_queue.put(working_string.strip())

            # Update context with the assistant's response
            update_context(user_id, agent_id, {"role": "assistant", "content": full_message})

            await phrase_queue.put(None)

    except Exception as e:
        print(f"Error in stream_completion: {e}")
        await phrase_queue.put(None)
        yield f"Error: {e}"

@anthropic_router.post("/api/clear_context")
async def clear_anthropic_context(request: Request):
    try:
        data = await request.json()
        user_id = data["user_id"]
        agent_id = "anthropic"
        clear_context(user_id, agent_id)
        return {"message": "Context cleared successfully"}
    except Exception as e:
        return {"error": f"Error clearing context: {str(e)}"}