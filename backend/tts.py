import queue
import threading
from functools import reduce
from typing import Callable, Generator

import openai
import pyaudio
from dotenv import load_dotenv

load_dotenv()

DELIMITERS = [f"{d} " for d in (".", "?", "!")]
MINIMUM_PHRASE_LENGTH = 200
TTS_CHUNK_SIZE = 1024

DEFAULT_RESPONSE_MODEL = "gpt-4o-mini"
DEFAULT_TTS_MODEL = "tts-1"
DEFAULT_VOICE = "alloy"

OPENAI_CLIENT = openai.OpenAI()

stop_event = threading.Event()

def stream_delimited_completion(
    messages: list[dict],
    client: openai.OpenAI = OPENAI_CLIENT,
    model: str = DEFAULT_RESPONSE_MODEL,
    content_transformers: list[Callable[[str], str]] = [],
    phrase_transformers: list[Callable[[str], str]] = [],
    delimiters: list[str] = DELIMITERS,
) -> Generator[str, None, None]:

    def apply_transformers(s: str, transformers: list[Callable[[str], str]]) -> str:
        return reduce(lambda c, transformer: transformer(c), transformers, s)

    working_string = ""
    last_chunk = None
    for chunk in client.chat.completions.create(
        messages=messages, 
        model=model, 
        stream=True, 
        temperature=1.0, 
        top_p=1.0,
        stream_options={"include_usage": True}
    ):
        last_chunk = chunk
        if stop_event.is_set():
            yield None
            return

        if chunk.choices and len(chunk.choices) > 0:
            content = chunk.choices[0].delta.content or ""
            if content:
                working_string += apply_transformers(content, content_transformers)
                while len(working_string) >= MINIMUM_PHRASE_LENGTH:
                    delimiter_index = -1
                    for delimiter in delimiters:
                        index = working_string.find(delimiter, MINIMUM_PHRASE_LENGTH)
                        if index != -1 and (
                            delimiter_index == -1 or index < delimiter_index
                        ):
                            delimiter_index = index

                    if delimiter_index == -1:
                        break

                    phrase, working_string = (
                        working_string[: delimiter_index + len(delimiter)],
                        working_string[delimiter_index + len(delimiter) :],
                    )
                    yield apply_transformers(phrase, phrase_transformers)

    if working_string.strip():
        yield working_string.strip()

    if last_chunk:
        print(f"choices: {last_chunk.choices}\nusage: {last_chunk.usage}")
        print("****************")

    yield None

def phrase_generator(prompt, phrase_queue: queue.Queue):
    messages = prompt

    for phrase in stream_delimited_completion(
        messages=messages,
        content_transformers=[
            lambda c: c.replace("\n", " ")
        ],
        phrase_transformers=[
            lambda p: p.strip()
        ],
    ):
        if phrase is None:
            phrase_queue.put(None)
            return
        print(f"Generated phrase: {phrase}")  # Print the generated phrase for debugging
        phrase_queue.put(phrase)

def text_to_speech_processor(
    phrase_queue: queue.Queue,
    audio_queue: queue.Queue,
    client: openai.OpenAI = OPENAI_CLIENT,
    model: str = DEFAULT_TTS_MODEL,
    voice: str = DEFAULT_VOICE,
):
    while not stop_event.is_set():
        phrase = phrase_queue.get()
        if phrase is None:
            audio_queue.put(None)
            return

        try:
            with client.audio.speech.with_streaming_response.create(
                model=model, voice=voice, response_format="pcm", input=phrase
            ) as response:
                for chunk in response.iter_bytes(chunk_size=TTS_CHUNK_SIZE):
                    audio_queue.put(chunk)
                    if stop_event.is_set():
                        return
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
