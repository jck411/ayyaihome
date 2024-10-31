# create_files.py

file_contents = {
    'openai_client.py': '''
# openai_client.py
import os
from dotenv import load_dotenv
import openai

# Load environment variables
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable is not set.")

# Initialize OpenAI client
openai.api_key = api_key
''',

    'audio_stream.py': '''
# audio_stream.py
import pyaudio

# Initialize PyAudio and open stream
p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=1, rate=24000, output=True)
''',

    'text_generator.py': '''
# text_generator.py
from openai_client import openai

def generate_text_from_input(user_input):
    """Generates text from input prompt and streams it."""
    stream_response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": user_input}],
        stream=True,
    )

    for chunk in stream_response:
        if 'content' in chunk.choices[0].delta:
            text_chunk = chunk.choices[0].delta.content
            yield text_chunk
''',

    'text_processor.py': '''
# text_processor.py
import re
import queue

def process_sentences(text_queue, sentence_queue, text_generation_complete, sentence_processing_complete):
    sentence_buffer = ""
    while not (text_generation_complete.is_set() and text_queue.empty()):
        try:
            new_text = text_queue.get(timeout=0.1)
            sentence_buffer += new_text
            sentences = re.findall(r'[^.!?]+[.!?]', sentence_buffer)
            for sentence in sentences:
                sentence_queue.put(sentence.strip())
            sentence_buffer = re.sub(r'.*[.!?]', '', sentence_buffer)
        except queue.Empty:
            continue

    if sentence_buffer:
        sentence_queue.put(sentence_buffer.strip())

    sentence_processing_complete.set()
''',

    'tts_service.py': '''
# tts_service.py
import queue
from openai_client import openai

def generate_audio(sentence_queue, audio_queue, sentence_processing_complete, audio_generation_complete):
    while not (sentence_processing_complete.is_set() and sentence_queue.empty()):
        try:
            sentence = sentence_queue.get(timeout=0.5)
            response = openai.Audio.create(
                engine="tts-1",
                text=sentence,
                voice="allison",
                response_format="pcm"
            )
            audio_queue.put(response)
            audio_queue.put(b'\\x00' * 4800)  # 0.1 seconds of silence
        except queue.Empty:
            continue

    audio_generation_complete.set()
''',

    'audio_player.py': '''
# audio_player.py
import queue
from audio_stream import stream

def play_audio(audio_queue, audio_generation_complete):
    while not (audio_generation_complete.is_set() and audio_queue.empty()):
        try:
            audio_chunk = audio_queue.get(timeout=0.5)
            stream.write(audio_chunk)
        except queue.Empty:
            continue

    # Close the PyAudio stream properly
    stream.stop_stream()
    stream.close()
''',

    'main.py': '''
# main.py
import threading
import queue
from text_generator import generate_text_from_input
from text_processor import process_sentences
from tts_service import generate_audio
from audio_player import play_audio
from audio_stream import p  # To terminate PyAudio at the end

# Queues and flags
text_queue = queue.Queue()
sentence_queue = queue.Queue()
audio_queue = queue.Queue()
text_generation_complete = threading.Event()
sentence_processing_complete = threading.Event()
audio_generation_complete = threading.Event()

def generate_text():
    user_input = input("Enter a prompt for TTS: ")
    for text_chunk in generate_text_from_input(user_input):
        print(text_chunk, end="", flush=True)
        text_queue.put(text_chunk)
    text_generation_complete.set()

# Start threads for each task
text_thread = threading.Thread(target=generate_text)
sentence_thread = threading.Thread(
    target=process_sentences,
    args=(text_queue, sentence_queue, text_generation_complete, sentence_processing_complete)
)
audio_gen_thread = threading.Thread(
    target=generate_audio,
    args=(sentence_queue, audio_queue, sentence_processing_complete, audio_generation_complete)
)
audio_play_thread = threading.Thread(
    target=play_audio,
    args=(audio_queue, audio_generation_complete)
)

text_thread.start()
sentence_thread.start()
audio_gen_thread.start()
audio_play_thread.start()

# Wait for all threads to complete
text_thread.join()
sentence_thread.join()
audio_gen_thread.join()
audio_play_thread.join()

# Terminate PyAudio
p.terminate()
''',
}

for filename, content in file_contents.items():
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content.strip())
    print(f'Created {filename}')
