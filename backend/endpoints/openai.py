#/home/jack/ayyaihome/backend/endpoints/openai.py

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
import queue
from init import stop_event, OPENAI_CONSTANTS, aclient
from services.tts_service import process_streams
from services.audio_player import find_next_phrase_end

openai_router = APIRouter()

@openai_router.websocket("/ws/openai")
async def websocket_openai(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            messages = [{"role": msg["role"], "content": msg["content"]} for msg in data.get('messages', [])]
            messages.insert(0, OPENAI_CONSTANTS["SYSTEM_PROMPT"])

            stop_event.set()
            await asyncio.sleep(0.1)
            stop_event.clear()

            phrase_queue = asyncio.Queue()
            audio_queue = queue.Queue()

            asyncio.create_task(process_streams(phrase_queue, audio_queue, OPENAI_CONSTANTS))

            await stream_completion(websocket, messages, phrase_queue)
    except WebSocketDisconnect:
        stop_event.set()
    except Exception as e:
        await websocket.send_json({"error": f"Unexpected error: {str(e)}"})

async def stream_completion(websocket: WebSocket, messages: list, phrase_queue: asyncio.Queue, model: str = OPENAI_CONSTANTS["DEFAULT_RESPONSE_MODEL"]):
    try:
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
                await phrase_queue.put(None)
                break

            content = ""
            if chunk.choices and hasattr(chunk.choices[0].delta, 'content'):
                content = chunk.choices[0].delta.content or ""

            if content:
                await websocket.send_text(content)
                working_string += content

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
        await phrase_queue.put(None)
    except asyncio.TimeoutError:
        await phrase_queue.put(None)
    except Exception as e:
        await phrase_queue.put(None)
        await websocket.send_text(f"Error: {e}")
