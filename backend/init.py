# /home/jack/ayyaihome/backend/init.py

import os
import threading
import pyaudio
from dotenv import load_dotenv
from openai import AsyncOpenAI
import anthropic  # Import the Anthropic SDK

# Load environment variables from a .env file
load_dotenv()

# Initialize PyAudio for audio playback
p = pyaudio.PyAudio()

# Global stop event
stop_event = threading.Event()

# Mapping between OpenAI response formats and PyAudio formats
AUDIO_FORMAT_MAPPING = {
    "pcm": pyaudio.paInt16,        # 16-bit PCM
    "float": pyaudio.paFloat32,    # 32-bit Float PCM
    "int24": pyaudio.paInt24,      # 24-bit PCM
    "ogg-opus": None,              # Requires decoding
    "mp3": None,                   # Requires decoding
    "aac": None                    # Requires decoding
}

# Audio configuration mapping
AUDIO_CONFIG_MAPPING = {
    "pcm": {
        "AUDIO_FORMAT": pyaudio.paInt16,
        "RATE": 24000,
        "CHANNELS": 1
    },
    "float": {
        "AUDIO_FORMAT": pyaudio.paFloat32,
        "RATE": 48000,
        "CHANNELS": 1
    },
    "int24": {
        "AUDIO_FORMAT": pyaudio.paInt24,
        "RATE": 44100,
        "CHANNELS": 2
    },
    "ogg-opus": {
        "AUDIO_FORMAT": None,  # Requires decoding
        "RATE": 48000,
        "CHANNELS": 2
    },
    "mp3": {
        "AUDIO_FORMAT": None,  # Requires decoding
        "RATE": 48000,
        "CHANNELS": 2
    },
    "aac": {
        "AUDIO_FORMAT": None,  # Requires decoding
        "RATE": 48000,
        "CHANNELS": 2
    }
}

# Shared Constants
SHARED_CONSTANTS = {
    "MINIMUM_PHRASE_LENGTH": 25,
    "TTS_CHUNK_SIZE": 1024,
    "DEFAULT_TTS_MODEL": "tts-1",
    "RESPONSE_FORMAT": "aac",  # aac, mp3 works for frontend playback but only pcm for backend
    "AUDIO_FORMAT": AUDIO_FORMAT_MAPPING.get("pcm", pyaudio.paInt16),
    "CHANNELS": 1,
    "RATE": 24000,
    "TTS_SPEED": 1.0,
    "TEMPERATURE": 1.0,
    "TOP_P": 1.0,
    "DELIMITERS": [".", "?", "!"],
    "FRONTEND_PLAYBACK": True # Enable frontend playback via WebSocket False plays via backend player
}

# OpenAI Constants
OPENAI_CONSTANTS = {
    **SHARED_CONSTANTS,
    "DEFAULT_RESPONSE_MODEL": "gpt-4o-mini",
    "DEFAULT_VOICE": "alloy",
    "SYSTEM_PROMPT": {
        "role": "system",
        "content": "You are a dry but witty AI assistant in a group conversation that includes Claude (another AI assistant) and human users. Messages are prefixed to identify the users. Do not prefix your own messages."
    }
}

# Anthropic Constants
ANTHROPIC_CONSTANTS = {
    **SHARED_CONSTANTS,
    "DEFAULT_RESPONSE_MODEL": "claude-3-5-sonnet-20240620",
    "DEFAULT_VOICE": "onyx",
    "SYSTEM_PROMPT": {
        "role": "system",
        "content": "You are dry, witty and unapologetic. You are in a group conversation that includes GPT (another AI assistant) and human users. Messages are prefixed to identify the users. Do not prefix your own messages."
    }
}

def update_audio_format(new_format: str):
    if new_format not in AUDIO_CONFIG_MAPPING:
        raise ValueError(f"Unsupported audio format: {new_format}")
    config = AUDIO_CONFIG_MAPPING[new_format]
    SHARED_CONSTANTS["RESPONSE_FORMAT"] = new_format
    SHARED_CONSTANTS["AUDIO_FORMAT"] = config["AUDIO_FORMAT"]
    SHARED_CONSTANTS["RATE"] = config["RATE"]
    SHARED_CONSTANTS["CHANNELS"] = config["CHANNELS"]
    if new_format in ["ogg-opus", "mp3", "aac"]:
        print(f"Note: {new_format.upper()} format requires decoding before playback.")

# Initialize API clients
aclient = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
anthropic_client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Import ConnectionManager
from websocket_manager import ConnectionManager
connection_manager = ConnectionManager()
