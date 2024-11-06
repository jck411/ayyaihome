from fastapi import APIRouter, Request
from backend.TTS.RTTTS_openai import play_text_stream, play_text_stream_async
from backend.text_clients.openai_chat_sync import generate_text_stream_sync
from backend.text_clients.openai_chat_async import generate_text_stream_async
router = APIRouter()

@router.post("/api/openai")
async def openai_stream(request: Request):
    """
    Endpoint to handle OpenAI text generation and TTS playback.

    Request payload should include:
        - messages (list): List of message dictionaries with "sender" and "text".
        - use_async (bool): If True, uses async OpenAI client and TTS playback.
        
    Returns:
        JSON response indicating playback start.
    """
    # Parse JSON request data
    data = await request.json()
    messages = [{"role": msg["sender"], "content": msg["text"]} for msg in data.get("messages", [])]
    messages.insert(0, {"role": "system", "content": "You are a helpful assistant."})

    # Determine whether to use async client and async playback
    use_async = data.get("use_async", False)

    if use_async:
        # Use async OpenAI text stream and play it with async TTS playback
        text_stream = generate_text_stream_async(messages)
        await play_text_stream_async(text_stream)  # Async playback
    else:
        # Use sync OpenAI text stream and play it with sync TTS playback
        text_stream = generate_text_stream_sync(messages)
        play_text_stream(text_stream)  # Sync playback

    # Return response to client after playback starts
    return {"status": "Playback started on backend"}
