import os
from pathlib import Path

# Define the base directory where the project will be created
BASE_DIR = Path.cwd() / "backend_modules"

# Define all files and their corresponding content
files = {
    # Audio Player Module
    "audio_player/__init__.py": "",
    "audio_player/base.py": '''from abc import ABC, abstractmethod
from typing import AsyncIterator

class AudioPlayer(ABC):
    @abstractmethod
    async def play_audio(self, audio_stream: AsyncIterator[bytes]):
        pass
''',
    "audio_player/pyaudio_player.py": '''from .base import AudioPlayer
import pyaudio

class PyAudioPlayer(AudioPlayer):
    def __init__(self, format, channels, rate):
        self.pyaudio_instance = pyaudio.PyAudio()
        self.format = format
        self.channels = channels
        self.rate = rate

    async def play_audio(self, audio_stream: AsyncIterator[bytes]):
        stream = self.pyaudio_instance.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            output=True
        )
        try:
            async for chunk in audio_stream:
                stream.write(chunk)
        finally:
            stream.stop_stream()
            stream.close()
''',

    # TTS Service Module
    "tts_service/__init__.py": "",
    "tts_service/base.py": '''from abc import ABC, abstractmethod
from typing import AsyncIterator

class TTSService(ABC):
    @abstractmethod
    async def synthesize_speech(self, text: str) -> AsyncIterator[bytes]:
        pass
''',
    "tts_service/openai_tts.py": '''from .base import TTSService
from openai import AsyncOpenAI
from typing import Dict, AsyncIterator

class OpenAITTSService(TTSService):
    def __init__(self, api_key: str, params: Dict):
        self.client = AsyncOpenAI(api_key=api_key)
        self.params = params

    async def synthesize_speech(self, text: str) -> AsyncIterator[bytes]:
        async with self.client.audio.speech.with_streaming_response.create(
            input=text,
            **self.params
        ) as response:
            async for audio_chunk in response.iter_bytes(chunk_size=self.params.get("chunk_size", 1024)):
                yield audio_chunk
''',

    # TTS Mechanism Module
    "tts_mechanism/__init__.py": "",
    "tts_mechanism/base.py": '''from abc import ABC, abstractmethod
from typing import AsyncIterator

class TTSMechanism(ABC):
    @abstractmethod
    async def process_text(self, text_stream: AsyncIterator[str]):
        pass
''',
    "tts_mechanism/queue_based.py": '''from .base import TTSMechanism
from tts_service.base import TTSService
from audio_player.base import AudioPlayer
import asyncio
from typing import AsyncIterator

class QueueBasedTTSMechanism(TTSMechanism):
    def __init__(self, tts_service: TTSService, audio_player: AudioPlayer):
        self.tts_service = tts_service
        self.audio_player = audio_player

    async def process_text(self, text_stream: AsyncIterator[str]):
        async for text in text_stream:
            audio_stream = self.tts_service.synthesize_speech(text)
            await self.audio_player.play_audio(audio_stream)
''',

    # Text Generation Module
    "text_generation/__init__.py": "",
    "text_generation/base.py": '''from abc import ABC, abstractmethod
from typing import List, Dict

class TextGenerator(ABC):
    @abstractmethod
    async def generate_text(self, messages: List[Dict[str, str]]) -> str:
        pass
''',
    "text_generation/openai_generator.py": '''from .base import TextGenerator
import os
from openai import AsyncOpenAI
from typing import List, Dict

class OpenAITextGenerator(TextGenerator):
    def __init__(self, api_key: str, model: str, params: Dict):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        self.params = params

    async def generate_text(self, messages: List[Dict[str, str]]) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            **self.params
        )
        return response.choices[0].message.content
''',

    # STT Service Module
    "stt_service/__init__.py": "",
    "stt_service/base.py": '''from abc import ABC, abstractmethod
from typing import AsyncIterator

class STTService(ABC):
    @abstractmethod
    async def transcribe_audio(self, audio_stream: AsyncIterator[bytes]) -> str:
        pass
''',

    # Wakeword Service Module
    "wakeword_service/__init__.py": "",
    "wakeword_service/base.py": '''from abc import ABC, abstractmethod

class WakewordService(ABC):
    @abstractmethod
    def detect_wakeword(self, audio_chunk: bytes) -> bool:
        pass
''',

    # Utils Module
    "utils/__init__.py": "",

    # Configuration Module
    "config.py": '''from pydantic import BaseSettings, Field
from typing import List, Dict, Optional

class Config(BaseSettings):
    TTS_CHUNK_SIZE: int = 1024
    DELIMITERS: List[str] = [". ", "? ", "! "]
    # Add all other configuration fields

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
''',

    # Logging Module
    "logging_config.py": '''import logging
import sys

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s - %(name)s: %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger
''',

    # Main Application File
    "main.py": '''from fastapi import FastAPI, Request
from text_generation.openai_generator import OpenAITextGenerator
from tts_service.openai_tts import OpenAITTSService
from tts_mechanism.queue_based import QueueBasedTTSMechanism
from audio_player.pyaudio_player import PyAudioPlayer
from config import Config
import os

app = FastAPI()
config = Config()

# Initialize services
text_generator = OpenAITextGenerator(
    api_key=os.getenv("OPENAI_API_KEY"),
    model=config.RESPONSE_MODEL,
    params=config.OPENAI_CHAT_COMPLETION_PARAMS
)

tts_service = OpenAITTSService(
    api_key=os.getenv("OPENAI_API_KEY"),
    params=config.OPENAI_TTS_PARAMS
)

audio_player = PyAudioPlayer(
    format=config.PYAUDIO_FORMAT,
    channels=config.PYAUDIO_CHANNELS,
    rate=config.PYAUDIO_RATE
)

tts_mechanism = QueueBasedTTSMechanism(tts_service, audio_player)

@app.post("/api/openai")
async def openai_chat_completion_stream(request: Request):
    data = await request.json()
    messages = data.get('messages', [])
    # Validation and processing
    generated_text = await text_generator.generate_text(messages)

    async def text_stream():
        yield generated_text

    await tts_mechanism.process_text(text_stream())
    return {"status": "success"}
''',

    # Requirements File
    "requirements.txt": '''fastapi
pydantic
openai
pyaudio
uvicorn
''',

    # Configuration YAML
    "config.yaml": '''# General TTS configuration (independent of specific TTS models)
GENERAL_TTS:
  TTS_CHUNK_SIZE: 1024            # Size of audio chunks for TTS playback
  DELIMITERS: [". ", "? ", "! "]  # Delimiters for segmenting phrases

# TTS Models configuration with an OpenAI subcategory
TTS_MODELS:
  OPENAI_TTS:
    TTS_SPEED: 1.0                  # Speed for TTS playback
    TTS_VOICE: "alloy"              # Voice option for TTS
    TTS_MODEL: "tts-1"              # Model ID for OpenAI TTS
    AUDIO_RESPONSE_FORMAT: "pcm"    # Audio response format for OpenAI TTS (e.g., "pcm", "mp3")

# LLM Model configuration with a subcategory for OpenAI-specific settings
LLM_MODEL_CONFIG:
  OPENAI:
    RESPONSE_MODEL: "gpt-4o-mini"   # Model ID for OpenAI language model
    TEMPERATURE: 1.0                # Randomness of response
    TOP_P: 1.0                      # Nucleus sampling threshold
    N: 1                            # Number of responses to generate per request
    SYSTEM_PROMPT_CONTENT: "You are a helpful but witty and dry assistant"  # System prompt

    # Advanced settings for OpenAI completion
    STREAM_OPTIONS:
      include_usage: true           # Include usage information in the response stream
    STOP: null                       # Stop sequence for responses
    MAX_TOKENS: null                 # Max token limit for responses
    PRESENCE_PENALTY: 0.0           # Diversity control for responses
    FREQUENCY_PENALTY: 0.0          # Repetition penalty for responses
    LOGIT_BIAS: null                 # Token likelihood adjustment
    USER: null                       # User identifier
    TOOLS: null                      # Tools available to the model
    TOOL_CHOICE: null                # Preferred tool for model
    MODALITIES:
      - text                         # Response modality

# Audio playback settings for PyAudio
AUDIO_PLAYBACK_CONFIG:
  FORMAT: 8                         # Integer format for PyAudio (8 corresponds to pyaudio.paInt16)
  CHANNELS: 1                       # Number of audio channels
  RATE: 24000                       # Audio playback sample rate

# OpenAI API key and CORS origins (for security and server config)
OPENAI_API_KEY: "your-openai-api-key"  # Replace with your OpenAI API key
CORS_ORIGINS: 
  - "http://localhost:3000"
  - "https://your-app-domain.com"
''',
}

def create_project_structure(base_dir: Path, files: dict):
    for relative_path, content in files.items():
        file_path = base_dir / relative_path
        file_dir = file_path.parent
        if not file_dir.exists():
            file_dir.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {file_dir}")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
            print(f"Created file: {file_path}")

if __name__ == "__main__":
    create_project_structure(BASE_DIR, files)
    print("\nProject structure created successfully!")
    print(f"Navigate to {BASE_DIR} to view your project.")
