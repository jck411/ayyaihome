import threading
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
from init import (
    stop_event,
    ANTHROPIC_CONSTANTS,
    anthropic_client,
    OPENAI_CONSTANTS,
    aclient,
    p  # Assuming p is the PyAudio instance
)
from services.tts_service import process_streams
from services.audio_player import audio_player, start_audio_player
import queue
import logging
import azure.cognitiveservices.speech as speechsdk
import os
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

chat_router = APIRouter()

# Load environment variables from the .env file
load_dotenv('/home/jack/ayyaihome/backend/.env')

# Configure Azure STT
def get_speech_config():
    # Fetch the keys from environment variables
    speech_key = os.getenv('AZURE_SPEECH_KEY')
    service_region = os.getenv('AZURE_REGION')

    if not speech_key or not service_region:
        raise ValueError("AZURE_SPEECH_KEY and AZURE_REGION must be set in the .env file.")

    # Configure Azure Speech SDK
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
    speech_config.speech_recognition_language = "en-US"
    
    return speech_config

def find_next_phrase_end(text: str) -> int:
    """
    Finds the position of the next sentence-ending delimiter in the text
    starting from a specified minimum length.
    """
    sentence_delim_pos = [
        text.find(d, ANTHROPIC_CONSTANTS["MINIMUM_PHRASE_LENGTH"]) for d in ANTHROPIC_CONSTANTS["DELIMITERS"]
    ]
    sentence_delim_pos = [pos for pos in sentence_delim_pos if pos != -1]
    return min(sentence_delim_pos, default=-1)

@chat_router.websocket("/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    logging.info("WebSocket connection accepted.")

    api_type = None  # To store which API to use ('anthropic' or 'openai')
    constants = None
    client = None

    # Initialize queues
    phrase_queue = asyncio.Queue()
    audio_sync_queue = queue.Queue()

    # Start the audio player in a separate thread with synchronous queue
    audio_player_thread = threading.Thread(target=audio_player, args=(audio_sync_queue,), daemon=True)
    audio_player_thread.start()
    logging.info("Audio player started.")

    # Start the STT recognizer in a background task
    stt_task = asyncio.create_task(start_microphone_recognition(websocket))

    # Variable to keep track of the process_streams task
    process_streams_task = None

    try:
        # Expect the first message to specify the API type
        initial_data = await websocket.receive_json()
        logging.info(f"Initial data received: {initial_data}")

        api_type = initial_data.get('api')
        if api_type == 'anthropic':
            constants = ANTHROPIC_CONSTANTS
            client = anthropic_client
        elif api_type == 'openai':
            constants = OPENAI_CONSTANTS
            client = aclient
        else:
            error_msg = "Invalid or missing 'api' field. Must be 'anthropic' or 'openai'."
            logging.warning(error_msg)
            await websocket.send_json({"error": error_msg})
            await websocket.close()
            return

        logging.info(f"Using API: {api_type}")

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

            # Cancel previous process_streams task if it's still running
            if process_streams_task and not process_streams_task.done():
                process_streams_task.cancel()
                try:
                    await process_streams_task
                except asyncio.CancelledError:
                    logging.info("Previous process_streams task cancelled.")
                # Clear the phrase queue
                phrase_queue = asyncio.Queue()
                # Optionally, clear the audio queue
                with audio_sync_queue.mutex:
                    audio_sync_queue.queue.clear()

            stop_event.set()
            await asyncio.sleep(0.1)
            stop_event.clear()
            logging.info("Stop event toggled.")

            # Start processing streams
            process_streams_task = asyncio.create_task(process_streams(phrase_queue, audio_sync_queue, constants))
            logging.info("Started process_streams task.")

            # Call the unified stream_completion
            await stream_completion(
                websocket,
                messages,
                phrase_queue,
                api_type,
                constants,
                client,
                audio_sync_queue
            )
    except WebSocketDisconnect:
        stop_event.set()
        logging.info("WebSocket disconnected.")
    except Exception as e:
        stop_event.set()
        error_msg = f"Unexpected error: {str(e)}"
        logging.exception(error_msg)
        await websocket.send_json({"error": error_msg})
    finally:
        # Signal the phrase queue and audio queue to stop
        await phrase_queue.put(None)
        audio_sync_queue.put(None)
        # Cancel the STT task
        stt_task.cancel()
        try:
            await stt_task
        except asyncio.CancelledError:
            pass
        # Wait for the audio player thread to finish
        audio_player_thread.join()
        logging.info("Audio player thread has been terminated.")


async def stream_completion(
    websocket: WebSocket,
    messages: list,
    phrase_queue: asyncio.Queue,
    api_type: str,
    constants: dict,
    client,
    audio_sync_queue: queue.Queue
):
    try:
        if api_type == 'anthropic':
            # Anthropic-specific streaming
            async with client.messages.stream(
                model=constants["DEFAULT_RESPONSE_MODEL"],
                messages=messages,
                max_tokens=1024,
                temperature=constants["TEMPERATURE"],
                system=constants["SYSTEM_PROMPT"]["content"]
            ) as stream:
                await handle_stream(websocket, stream.text_stream, phrase_queue, constants)
        elif api_type == 'openai':
            # OpenAI-specific streaming
            response = await client.chat.completions.create(
                model=constants["DEFAULT_RESPONSE_MODEL"],
                messages=messages,
                stream=True,
                temperature=constants["TEMPERATURE"],
                top_p=constants["TOP_P"],
            )
            await handle_stream(websocket, response, phrase_queue, constants, is_openai=True)
    except asyncio.TimeoutError:
        await phrase_queue.put(None)
        logging.warning("Stream completion timed out.")
    except Exception as e:
        await phrase_queue.put(None)
        error_msg = f"Error in stream completion: {e}"
        logging.exception(error_msg)
        await websocket.send_text(f"Error: {e}")

async def handle_stream(
    websocket: WebSocket,
    stream,
    phrase_queue: asyncio.Queue,
    constants: dict,
    is_openai: bool = False
):
    try:
        working_string = ""
        in_code_block = False
        logging.info("Started streaming completion.")

        async for chunk in stream:
            if is_openai:
                if chunk.choices and hasattr(chunk.choices[0].delta, 'content'):
                    content = chunk.choices[0].delta.content or ""
                else:
                    content = ""
            else:
                content = chunk or ""

            if stop_event.is_set():
                logging.info("Stop event detected. Ending stream.")
                await phrase_queue.put(None)
                break

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
    except Exception as e:
        await phrase_queue.put(None)
        error_msg = f"Error in handle_stream: {e}"
        logging.exception(error_msg)
        await websocket.send_text(f"Error: {e}")

# Start microphone recognition and stream STT results to WebSocket
async def start_microphone_recognition(websocket: WebSocket):
    speech_config = get_speech_config()
    audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)

    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

    # Event handler for recognized speech
    def recognized_handler(evt):
        if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
            # Get the recognized text
            recognized_text = evt.result.text

            # Log the recognized text to the terminal
            logging.info(f"Recognized text: {recognized_text}")

            # Send recognized text to the WebSocket
            asyncio.create_task(websocket.send_text(recognized_text))

    # Connect the event handler to the recognizer
    speech_recognizer.recognized.connect(recognized_handler)

    # Start continuous recognition
    speech_recognizer.start_continuous_recognition()

    try:
        while True:
            await asyncio.sleep(1)  # Keep the server running to listen for events
    except asyncio.CancelledError:
        logging.info("Stopping recognition...")
        speech_recognizer.stop_continuous_recognition()
