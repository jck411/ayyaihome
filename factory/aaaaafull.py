import os  # For interacting with the operating system
import requests  # For making HTTP requests
from io import BytesIO  # For handling byte streams
from pathlib import Path  # For filesystem path manipulations
import pyaudio  # For handling audio playback
from openai import OpenAI  # For OpenAI API and event handling
import time  # For time-related functions
import threading  # For handling threads
import queue  # For creating and managing queues
import re  # For regular expressions
from dotenv import load_dotenv  # Load environment variables from a .env file

# Load environment variables
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable is not set.")

# Initialize the OpenAI client with the API key
client = OpenAI(api_key=api_key)

# Initialize PyAudio
p = pyaudio.PyAudio()

# Open a stream with specific audio format parameters
stream = p.open(format=pyaudio.paInt16,
    channels=1,
    rate=24000,
    output=True)

# Create separate queues for text and audio chunks
text_queue = queue.Queue()
sentence_queue = queue.Queue()
audio_queue = queue.Queue()

# Flags for process control
text_generation_complete = threading.Event()
sentence_processing_complete = threading.Event()
audio_generation_complete = threading.Event()

def generate_text():
    # Get the prompt from the terminal
    user_prompt = input("Please enter your prompt: ")

    chat_completion = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": user_prompt}
        ],
        stream=True
    )

    full_response = ""
    for chunk in chat_completion:
        if chunk.choices[0].delta.content:
            new_text = chunk.choices[0].delta.content
            full_response += new_text
            print(new_text, end="", flush=True)  # Print text chunk immediately
            text_queue.put(new_text)

    text_generation_complete.set()

def process_sentences():
    sentence_buffer = ""
    while not (text_generation_complete.is_set() and text_queue.empty()):
        try:
            new_text = text_queue.get(timeout=0.1)
            sentence_buffer += new_text

            # Split sentences properly
            sentences = re.split(r'(?<=[.!?])\s+', sentence_buffer)
            if sentences:
                # If the last character is not a sentence terminator, keep the last part in buffer
                if sentence_buffer[-1] not in '.!?':
                    sentence_buffer = sentences.pop()
                else:
                    sentence_buffer = ''
                for sentence in sentences:
                    sentence_queue.put(sentence.strip())
            else:
                # No complete sentences yet, keep buffering
                continue
        except queue.Empty:
            continue

    # Process any remaining text
    if sentence_buffer:
        sentence_queue.put(sentence_buffer.strip())

    sentence_processing_complete.set()

def generate_audio():
    while not (sentence_processing_complete.is_set() and sentence_queue.empty()):
        try:
            sentence = sentence_queue.get(timeout=0.5)
            with client.audio.speech.with_streaming_response.create(
                model="tts-1",
                voice="alloy",
                input=sentence,
                response_format="pcm"
            ) as response:
                for audio_chunk in response.iter_bytes(1024):
                    audio_queue.put(audio_chunk)

            # Add a short pause between sentences
            audio_queue.put(b'\x00' * 4800)  # 0.1 seconds of silence at 24000 Hz
        except queue.Empty:
            continue

    audio_generation_complete.set()

def play_audio():
    while not (audio_generation_complete.is_set() and audio_queue.empty()):
        try:
            audio_chunk = audio_queue.get(timeout=0.5)
            stream.write(audio_chunk)
        except queue.Empty:
            continue

# Start text generation in a separate thread
text_thread = threading.Thread(target=generate_text)
text_thread.start()

# Start sentence processing in a separate thread
sentence_thread = threading.Thread(target=process_sentences)
sentence_thread.start()

# Start audio generation in a separate thread
audio_gen_thread = threading.Thread(target=generate_audio)
audio_gen_thread.start()

# Start audio playback in a separate thread
time.sleep(1)  # Delay for smooth start
audio_play_thread = threading.Thread(target=play_audio)
audio_play_thread.start()

# Wait for all threads to complete
text_thread.join()
sentence_thread.join()
audio_gen_thread.join()
audio_play_thread.join()

# Close the PyAudio stream properly
stream.stop_stream()
stream.close()
p.terminate()
