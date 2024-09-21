#/home/jack/ayyaihome/backend/endpoints/anthropic.py

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
import queue
from init import stop_event, ANTHROPIC_CONSTANTS, anthropic_client
from services.tts_service import process_streams
from services.audio_player import find_next_phrase_end
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

anthropic_router = APIRouter()

@anthropic_router.websocket("/ws/anthropic")
async def websocket_anthropic(websocket: WebSocket):
    await websocket.accept()
    logging.info("WebSocket connection accepted.")
    try:
        while True:
            data = await websocket.receive_json()
            logging.info(f"Received data: {data}")

            messages = [{"role": msg["role"], "content": msg["content"]} for msg in data.get('messages', [])]
            logging.info(f"Extracted messages: {messages}")

            if not messages:
                error_msg = "Prompt is required."
                logging.warning(error_msg)
                await websocket.send_json({"error": error_msg})
                continue

            stop_event.set()
            await asyncio.sleep(0.1)
            stop_event.clear()
            logging.info("Stop event toggled.")

            phrase_queue = asyncio.Queue()
            audio_queue = queue.Queue()

            asyncio.create_task(process_streams(phrase_queue, audio_queue, ANTHROPIC_CONSTANTS))
            logging.info("Started process_streams task.")

            await stream_completion(websocket, messages, phrase_queue)
    except WebSocketDisconnect:
        stop_event.set()
        logging.info("WebSocket disconnected.")
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logging.exception(error_msg)
        await websocket.send_json({"error": error_msg})

async def stream_completion(websocket: WebSocket, messages: list, phrase_queue: asyncio.Queue):
    try:
        async with anthropic_client.messages.stream(
            model=ANTHROPIC_CONSTANTS["DEFAULT_RESPONSE_MODEL"],
            messages=messages,
            max_tokens=1024,
            temperature=ANTHROPIC_CONSTANTS["TEMPERATURE"],
            system=ANTHROPIC_CONSTANTS["SYSTEM_PROMPT"]["content"]
        ) as stream:
            working_string = ""
            in_code_block = False
            logging.info("Started streaming completion.")

            async for chunk in stream.text_stream:
                if stop_event.is_set():
                    logging.info("Stop event detected. Ending stream.")
                    await phrase_queue.put(None)
                    break

                content = chunk or ""
                logging.info(f"Received chunk: {content}")

                if content:
                    working_string += content
                    await websocket.send_text(content)
                    logging.info(f"Sent content to WebSocket: {content}")

                    while True:
                        code_block_start = working_string.find("```")

                        if in_code_block:
                            code_block_end = working_string.find("```", 3)
                            if code_block_end != -1:
                                logging.info("Code block end found.")
                                working_string = working_string[code_block_end + 3:]
                                await phrase_queue.put("Code presented on screen")
                                in_code_block = False
                            else:
                                break
                        else:
                            if code_block_start != -1:
                                logging.info("Code block start found.")
                                phrase, working_string = working_string[:code_block_start], working_string[code_block_start:]
                                if phrase.strip():
                                    await phrase_queue.put(phrase.strip())
                                    logging.info(f"Queued phrase: {phrase.strip()}")
                                in_code_block = True
                            else:
                                next_phrase_end = find_next_phrase_end(working_string)
                                if next_phrase_end == -1:
                                    break
                                phrase, working_string = working_string[:next_phrase_end + 1].strip(), working_string[next_phrase_end + 1:]
                                await phrase_queue.put(phrase)
                                logging.info(f"Queued phrase: {phrase}")
            if working_string.strip() and not in_code_block:
                await phrase_queue.put(working_string.strip())
                logging.info(f"Queued final phrase: {working_string.strip()}")
            await phrase_queue.put(None)
            logging.info("Stream completion ended.")
    except asyncio.TimeoutError:
        await phrase_queue.put(None)
        logging.warning("Stream completion timed out.")
    except Exception as e:
        await phrase_queue.put(None)
        error_msg = f"Error in stream completion: {e}"
        logging.exception(error_msg)
        await websocket.send_text(f"Error: {e}")
