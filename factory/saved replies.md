Certainly! Below, I've reorganized your code into four separate modules corresponding to your specified components:

API call for chat completion (text_generator.py)
Text processing/preparation (sentence_processor.py)
TTS service (tts_service.py)
Audio player (audio_player.py)
Each module contains classes that can be interchanged with different implementations, following the factory pattern.

text_generator.py

python
Copy code
# text_generator.py

from abc import ABC, abstractmethod

class TextGenerator(ABC):
    @abstractmethod
    def generate_text(self):
        pass

class OpenAITextGenerator(TextGenerator):
    def __init__(self, client, text_queue, text_generation_complete):
        self.client = client
        self.text_queue = text_queue
        self.text_generation_complete = text_generation_complete

    def generate_text(self):
        # Get the prompt from the terminal
        user_prompt = input("Please enter your prompt: ")

        chat_completion = self.client.chat.completions.create(
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
                self.text_queue.put(new_text)

        self.text_generation_complete.set()
sentence_processor.py

python
Copy code
# sentence_processor.py

from abc import ABC, abstractmethod
import re  # For regular expressions
import queue  # For creating and managing queues

class SentenceProcessor(ABC):
    @abstractmethod
    def process_sentences(self):
        pass

class DefaultSentenceProcessor(SentenceProcessor):
    def __init__(self, text_queue, sentence_queue, text_generation_complete, sentence_processing_complete):
        self.text_queue = text_queue
        self.sentence_queue = sentence_queue
        self.text_generation_complete = text_generation_complete
        self.sentence_processing_complete = sentence_processing_complete

    def process_sentences(self):
        sentence_buffer = ""
        while not (self.text_generation_complete.is_set() and self.text_queue.empty()):
            try:
                new_text = self.text_queue.get(timeout=0.1)
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
                        self.sentence_queue.put(sentence.strip())
                else:
                    # No complete sentences yet, keep buffering
                    continue
            except queue.Empty:
                continue

        # Process any remaining text
        if sentence_buffer:
            self.sentence_queue.put(sentence_buffer.strip())

        self.sentence_processing_complete.set()
tts_service.py

python
Copy code
# tts_service.py

from abc import ABC, abstractmethod
import queue  # For creating and managing queues

class TTSService(ABC):
    @abstractmethod
    def generate_audio(self):
        pass

class OpenAITTSService(TTSService):
    def __init__(self, client, sentence_queue, audio_queue, sentence_processing_complete, audio_generation_complete):
        self.client = client
        self.sentence_queue = sentence_queue
        self.audio_queue = audio_queue
        self.sentence_processing_complete = sentence_processing_complete
        self.audio_generation_complete = audio_generation_complete

    def generate_audio(self):
        while not (self.sentence_processing_complete.is_set() and self.sentence_queue.empty()):
            try:
                sentence = self.sentence_queue.get(timeout=0.5)
                with self.client.audio.speech.with_streaming_response.create(
                    model="tts-1",
                    voice="alloy",
                    input=sentence,
                    response_format="pcm"
                ) as response:
                    for audio_chunk in response.iter_bytes(1024):
                        self.audio_queue.put(audio_chunk)

                # Add a short pause between sentences
                self.audio_queue.put(b'\x00' * 4800)  # 0.1 seconds of silence at 24000 Hz
            except queue.Empty:
                continue

        self.audio_generation_complete.set()
audio_player.py

python
Copy code
# audio_player.py

from abc import ABC, abstractmethod
import queue  # For creating and managing queues

class AudioPlayer(ABC):
    @abstractmethod
    def play_audio(self):
        pass

class PyAudioPlayer(AudioPlayer):
    def __init__(self, audio_queue, audio_generation_complete, stream):
        self.audio_queue = audio_queue
        self.audio_generation_complete = audio_generation_complete
        self.stream = stream

    def play_audio(self):
        while not (self.audio_generation_complete.is_set() and self.audio_queue.empty()):
            try:
                audio_chunk = self.audio_queue.get(timeout=0.5)
                self.stream.write(audio_chunk)
            except queue.Empty:
                continue
main.py

python
Copy code
# main.py

import os  # For interacting with the operating system
import threading  # For handling threads
import queue  # For creating and managing queues
import pyaudio  # For handling audio playback
from openai import OpenAI  # For OpenAI API and event handling
from dotenv import load_dotenv  # Load environment variables from a .env file
import time  # For time-related functions

# Import the modules
from text_generator import OpenAITextGenerator
from sentence_processor import DefaultSentenceProcessor
from tts_service import OpenAITTSService
from audio_player import PyAudioPlayer

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

# Instantiate the classes
text_generator = OpenAITextGenerator(client, text_queue, text_generation_complete)
sentence_processor = DefaultSentenceProcessor(text_queue, sentence_queue, text_generation_complete, sentence_processing_complete)
tts_service = OpenAITTSService(client, sentence_queue, audio_queue, sentence_processing_complete, audio_generation_complete)
audio_player = PyAudioPlayer(audio_queue, audio_generation_complete, stream)

# Start text generation in a separate thread
text_thread = threading.Thread(target=text_generator.generate_text)
text_thread.start()

# Start sentence processing in a separate thread
sentence_thread = threading.Thread(target=sentence_processor.process_sentences)
sentence_thread.start()

# Start audio generation in a separate thread
audio_gen_thread = threading.Thread(target=tts_service.generate_audio)
audio_gen_thread.start()

# Start audio playback in a separate thread
time.sleep(1)  # Delay for smooth start
audio_play_thread = threading.Thread(target=audio_player.play_audio)
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
By structuring your code into these modules and classes, each component becomes interchangeable. You can now replace any module with a different implementation by creating a new class that inherits from the respective abstract base class (TextGenerator, SentenceProcessor, TTSService, AudioPlayer) and implements its abstract methods.

This modular design adheres to the factory pattern and allows you to plug in different services or methods without changing the core logic of your application.