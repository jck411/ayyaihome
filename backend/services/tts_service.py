import asyncio
import queue
from init import stop_event, aclient
from services.audio_player import start_audio_player

async def text_to_speech_processor(phrase_queue: asyncio.Queue, audio_queue: queue.Queue, tts_constants):
    """
    Processes phrases into speech using OpenAI's TTS model.
    Streams audio chunks to the audio queue for playback.
    The tts_constants argument determines the voice, model, etc., to use.
    """
    try:
        while not stop_event.is_set():  # Check stop event in TTS processor
            phrase = await phrase_queue.get()
            if phrase is None:  # If None, this signals the end of TTS processing
                audio_queue.put(None)
                return

            # Send the phrase to OpenAI's TTS API with appropriate constants
            async with aclient.audio.speech.with_streaming_response.create(
                model=tts_constants["DEFAULT_TTS_MODEL"],
                voice=tts_constants["DEFAULT_VOICE"],
                input=phrase,
                speed=tts_constants["TTS_SPEED"],
                response_format="pcm"
            ) as response:
                async for audio_chunk in response.iter_bytes(tts_constants["TTS_CHUNK_SIZE"]):
                    if stop_event.is_set():  # Stop event triggered, exit
                        return
                    audio_queue.put(audio_chunk)  # Stream audio to the audio queue

            audio_queue.put(b'\x00' * 2400)  # Pause between sentences

    except Exception as e:
        print(f"Error in TTS processing: {e}")
        audio_queue.put(None)  # Signal the end of audio on error

async def process_streams(phrase_queue: asyncio.Queue, audio_queue: queue.Queue, tts_constants):
    """
    Manages the processing of text-to-speech and audio playback using OpenAI TTS.
    Pass the appropriate TTS constants for OpenAI or Anthropic.
    """
    tts_task = asyncio.create_task(text_to_speech_processor(phrase_queue, audio_queue, tts_constants))
    start_audio_player(audio_queue)
    await tts_task