from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import queue
import threading

from backend.text_preparer import prepare_text
from backend.tts import text_to_speech_processor, phrase_generator, audio_player

router = APIRouter()

@router.post("/api/openai")
async def tts_stream(request: Request):
    data = await request.json()
    print("Received data:", data)  # Debugging line

    messages = data.get("messages", [])
    prompt = prepare_text(messages)

    print("Prepared prompt:", prompt)  # Debugging line

    if not prompt:
        return {"error": "No prompt provided"}

    phrase_queue = queue.Queue()
    audio_queue = queue.Queue()

    phrase_generation_thread = threading.Thread(target=phrase_generator, args=(prompt, phrase_queue))
    tts_thread = threading.Thread(target=text_to_speech_processor, args=(phrase_queue, audio_queue))
    audio_player_thread = threading.Thread(target=audio_player, args=(audio_queue,))

    phrase_generation_thread.start()
    tts_thread.start()
    audio_player_thread.start()

    # Return a simple JSON response indicating that TTS processing has started
    return JSONResponse(content={"status": "TTS processing started"})
