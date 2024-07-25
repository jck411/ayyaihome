from openai import AsyncOpenAI
import openai
import os
import queue
import threading
import pyaudio

aclient = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Define global stop event
stop_event = threading.Event()

TTS_CHUNK_SIZE = 1024  # Initial size of the chunks of audio data to be processed

async def generate_openai_response(formatted_messages):
    full_content = ""
    last_chunk = None
    phrase_queue = queue.Queue()
    audio_queue = queue.Queue()

    # Processor Thread to handle TTS
    tts_thread = threading.Thread(target=text_to_speech_processor, args=(phrase_queue, audio_queue))
    # Audio Player Thread to handle audio playback
    audio_player_thread = threading.Thread(target=audio_player, args=(audio_queue,))

    # Start the threads
    tts_thread.start()
    audio_player_thread.start()

    try:
        response = await aclient.chat.completions.create(
            model="gpt-4o-mini",
            messages=formatted_messages,
            stream=True,
            stream_options={"include_usage": True},
        )
        batch_text = ""  # Initialize batch text variable
        async for chunk in response:
            last_chunk = chunk  # Store the current chunk as the last chunk - for token count

            if chunk.choices:
                delta = chunk.choices[0].delta
                if delta.content:
                    batch_text += delta.content  # Append content to batch text

                    # If batch text length exceeds a threshold, process it
                    if len(batch_text) > 100:  # Smaller threshold to start TTS earlier
                        phrase_queue.put(batch_text.strip())
                        batch_text = ""

                    full_content += delta.content
                    yield delta.content

        # Process any remaining batch text
        if batch_text:
            phrase_queue.put(batch_text.strip())

        # Print the last chunk after all chunks have been processed - token count
        if last_chunk:
            print(f"Last chunk data: {last_chunk}")

    except Exception as e:
        yield f"Error: {e}"
    
    phrase_queue.put(None)  # Signal end of phrases to TTS processor
    tts_thread.join()
    audio_player_thread.join()

def text_to_speech_processor(phrase_queue: queue.Queue, audio_queue: queue.Queue):
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    while not stop_event.is_set():
        text = phrase_queue.get()
        if text is None:
            audio_queue.put(None)
            return

        try:
            response = client.audio.speech.create(
                model="tts-1",
                voice="alloy",
                response_format="pcm",
                input=text,
            )

            # Assuming the response is a stream, we need to read the content
            audio_data = b''
            for chunk in response.iter_bytes():
                audio_data += chunk

            # Split audio data into chunks of TTS_CHUNK_SIZE and put them into the queue
            for i in range(0, len(audio_data), TTS_CHUNK_SIZE):
                audio_chunk = audio_data[i:i + TTS_CHUNK_SIZE]
                audio_queue.put(audio_chunk)

        except Exception as e:
            print(f"Error in text_to_speech_processor: {e}")
            audio_queue.put(None)
            return

def audio_player(audio_queue: queue.Queue):
    p = pyaudio.PyAudio()
    player_stream = p.open(format=pyaudio.paInt16, channels=1, rate=24000, output=True)

    try:
        while not stop_event.is_set():
            audio_data = audio_queue.get()
            if audio_data is None:
                break
            player_stream.write(audio_data)

    except Exception as e:
        print(f"Error in audio_player: {e}")

    finally:
        player_stream.stop_stream()
        player_stream.close()
        p.terminate()

# Wait for Enter key to stop
def wait_for_enter():
    input("Press Enter to stop...\n\n")
    stop_event.set()
    print("STOP instruction received. Working to quit...")

# Daemon thread to handle stopping
threading.Thread(target=wait_for_enter, daemon=True).start()
