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

# Mapping between OpenAI response formats and PyAudio formats
AUDIO_FORMAT_MAPPING = {
    "pcm": pyaudio.paInt16,        # 16-bit PCM format for high-quality audio
    "float": pyaudio.paFloat32,    # 32-bit Float PCM for more dynamic range
    "int24": pyaudio.paInt24,      # 24-bit PCM for high-quality playback
    "ogg-opus": None,              # Requires decoding for playback
    "mp3": None,                   # Requires decoding for playback
    "aac": None                    # Requires decoding for playback
}

# Audio configuration mapping for different formats
AUDIO_CONFIG_MAPPING = {
    "pcm": {
        "AUDIO_FORMAT": pyaudio.paInt16,  # 16-bit PCM format
        "RATE": 24000,  # Sampling rate in Hz
        "CHANNELS": 1   # Mono channel
    },
    "float": {
        "AUDIO_FORMAT": pyaudio.paFloat32,  # 32-bit Float PCM format
        "RATE": 48000,  # Higher sampling rate for better quality
        "CHANNELS": 1   # Mono channel
    },
    "int24": {
        "AUDIO_FORMAT": pyaudio.paInt24,  # 24-bit PCM format
        "RATE": 44100,  # Standard sampling rate for high-quality audio
        "CHANNELS": 2   # Stereo channels
    },
    "ogg-opus": {
        "AUDIO_FORMAT": None,  # Requires decoding before playback
        "RATE": 48000,  # Sampling rate in Hz
        "CHANNELS": 2   # Stereo channels
    },
    "mp3": {
        "AUDIO_FORMAT": None,  # Requires decoding before playback
        "RATE": 48000,  # Sampling rate in Hz
        "CHANNELS": 2   # Stereo channels
    },
    "aac": {
        "AUDIO_FORMAT": None,  # Requires decoding before playback
        "RATE": 48000,  # Sampling rate in Hz
        "CHANNELS": 2   # Stereo channels
    }
}

# Shared Constants used across the application
SHARED_CONSTANTS = {
    "MINIMUM_PHRASE_LENGTH": 25,  # Minimum length of a phrase for processing
    "TTS_CHUNK_SIZE": 1024,  # Chunk size for Text-to-Speech audio streaming
    "DEFAULT_TTS_MODEL": "tts-1",  # Default Text-to-Speech model
    "RESPONSE_FORMAT": "aac",  # Default audio response format
    "AUDIO_FORMAT": AUDIO_FORMAT_MAPPING.get("pcm", pyaudio.paInt16),  # Default audio format
    "CHANNELS": 1,  # Default number of audio channels (mono)
    "RATE": 24000,  # Default sampling rate in Hz
    "TTS_SPEED": 1.0,  # Speed of the Text-to-Speech playback
    "TEMPERATURE": 1.0,  # Temperature parameter for response randomness
    "TOP_P": 1.0,  # Top-p sampling parameter
    "DELIMITERS": [".", "?", "!"],  # Sentence delimiters for splitting text
    "FRONTEND_PLAYBACK": True  # Enable frontend playback via WebSocket
}

# OpenAI-specific constants
OPENAI_CONSTANTS = {
    **SHARED_CONSTANTS,
    "DEFAULT_RESPONSE_MODEL": "gpt-4o-mini",  # Default OpenAI response model
    "DEFAULT_VOICE": "alloy",  # Default voice for Text-to-Speech
    "SYSTEM_PROMPT": {
        "role": "system",
        "content": "You are a dry but witty AI assistant in a group conversation that includes Claude (another AI assistant) and human users. Messages are prefixed to identify the users. Do not prefix your own messages."
    }
}

# Anthropic-specific constants
ANTHROPIC_CONSTANTS = {
    **SHARED_CONSTANTS,
    "DEFAULT_RESPONSE_MODEL": "claude-3-5-sonnet-20240620",  # Default Anthropic response model
    "DEFAULT_VOICE": "onyx",  # Default voice for Anthropic Text-to-Speech
    "SYSTEM_PROMPT": {
        "role": "system",
        "content": "You are dry, witty and unapologetic. You are in a group conversation that includes GPT (another AI assistant) and human users. Messages are prefixed to identify the users. Do not prefix your own messages."
    }
}

# Function to update audio format settings
def update_audio_format(new_format: str):
    # Validate the new format against supported formats
    if new_format not in AUDIO_CONFIG_MAPPING:
        raise ValueError(f"Unsupported audio format: {new_format}")
    # Retrieve configuration for the new format
    config = AUDIO_CONFIG_MAPPING[new_format]
    # Update shared constants with the new format settings
    SHARED_CONSTANTS["RESPONSE_FORMAT"] = new_format
    SHARED_CONSTANTS["AUDIO_FORMAT"] = config["AUDIO_FORMAT"]
    SHARED_CONSTANTS["RATE"] = config["RATE"]
    SHARED_CONSTANTS["CHANNELS"] = config["CHANNELS"]
    # Print a note if the new format requires decoding
    if new_format in ["ogg-opus", "mp3", "aac"]:
        print(f"Note: {new_format.upper()} format requires decoding before playback.")

# Initialize OpenAI API client with API key from environment variables
aclient = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize Anthropic API client with API key from environment variables
anthropic_client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Import and initialize ConnectionManager for WebSocket communication
from websocket_manager import ConnectionManager
connection_manager = ConnectionManager()