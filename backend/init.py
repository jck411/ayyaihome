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
# Compressed formats (ogg-opus, mp3, aac) are set to None as they require decoding
AUDIO_FORMAT_MAPPING = {
    "pcm": pyaudio.paInt16,        # 16-bit PCM
    "float": pyaudio.paFloat32,    # 32-bit Float PCM
    "int24": pyaudio.paInt24,      # 24-bit PCM (ensure PyAudio supports this on your system)
    "ogg-opus": None,               # Requires decoding
    "mp3": None,                    # Requires decoding
    "aac": None                     # Requires decoding
    # Add more mappings as needed based on OpenAI's supported formats
}

# Optional: Centralized configuration mapping for all audio parameters
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
    # Add more mappings as needed
}

# Shared Constants for both OpenAI and Anthropic
SHARED_CONSTANTS = {
    "MINIMUM_PHRASE_LENGTH": 25,
    "TTS_CHUNK_SIZE": 1024,
    "DEFAULT_TTS_MODEL": "tts-1",
    "RESPONSE_FORMAT": "pcm",  # Default API response format
    "AUDIO_FORMAT": AUDIO_FORMAT_MAPPING.get("pcm", pyaudio.paInt16),  # PyAudio format based on response
    "CHANNELS": 1,
    "RATE": 24000,
    "TTS_SPEED": 1.0,
    "TEMPERATURE": 1.0,
    "TOP_P": 1.0,
    "DELIMITERS": [".", "?", "!"]
}

# Specific settings for OpenAI
OPENAI_CONSTANTS = {
    **SHARED_CONSTANTS,
    "DEFAULT_RESPONSE_MODEL": "gpt-4o-mini",
    "DEFAULT_VOICE": "alloy",  # OpenAI-specific voice
    "SYSTEM_PROMPT": {
        "role": "system",
        "content": "You are a dry but witty AI assistant in a group conversation that includes Claude (another AI assistant) and human users. Messages are prefixed to identify the users. Do not prefix your own messages."
    }
}

# Specific settings for Anthropic
ANTHROPIC_CONSTANTS = {
    **SHARED_CONSTANTS,
    "DEFAULT_RESPONSE_MODEL": "claude-3-5-sonnet-20240620",
    "DEFAULT_VOICE": "onyx",  # Anthropic-specific voice
    "SYSTEM_PROMPT": {
        "role": "system",
        "content": "You are dry, witty and unapologetic. You are in a group conversation that includes GPT (another AI assistant) and human users. Messages are prefixed to identify the users. Do not prefix your own messages."
    }
}

def update_audio_format(new_format: str):
    """
    Updates the AUDIO_FORMAT and related parameters in SHARED_CONSTANTS based on the provided RESPONSE_FORMAT.
    """
    if new_format not in AUDIO_CONFIG_MAPPING:
        raise ValueError(f"Unsupported audio format: {new_format}")
    
    config = AUDIO_CONFIG_MAPPING[new_format]
    
    SHARED_CONSTANTS["RESPONSE_FORMAT"] = new_format
    SHARED_CONSTANTS["AUDIO_FORMAT"] = config["AUDIO_FORMAT"]
    SHARED_CONSTANTS["RATE"] = config["RATE"]
    SHARED_CONSTANTS["CHANNELS"] = config["CHANNELS"]

    if new_format in ["ogg-opus", "mp3", "aac"]:
        print(f"Note: {new_format.upper()} format requires decoding before playback.")

# Initialize the OpenAI API client
aclient = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize the Anthropic API client
anthropic_client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
