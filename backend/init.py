import os
import pyaudio
from dotenv import load_dotenv
from openai import AsyncOpenAI
import anthropic  # Import the Anthropic SDK
import asyncio
from websocket_manager import ConnectionManager

# Load environment variables from a .env file
load_dotenv()

# Initialize PyAudio for audio playback
p = pyaudio.PyAudio()

# Audio configuration mapping for different formats
AUDIO_CONFIG_MAPPING = {
    "pcm": {
        "AUDIO_FORMAT": pyaudio.paInt16,  # 16-bit PCM format
        "MIME_TYPE": "audio/pcm",
        "RATE": 24000,  # Sampling rate in Hz
        "CHANNELS": 1   # Mono channel
    },
    "float": {
        "AUDIO_FORMAT": pyaudio.paFloat32,  # 32-bit Float PCM format
        "MIME_TYPE": "audio/float",
        "RATE": 48000,  # Higher sampling rate for better quality
        "CHANNELS": 1   # Mono channel
    },
    "int24": {
        "AUDIO_FORMAT": pyaudio.paInt24,  # 24-bit PCM format
        "MIME_TYPE": "audio/int24",
        "RATE": 44100,  # Standard sampling rate for high-quality audio
        "CHANNELS": 2   # Stereo channels
    },
    "ogg-opus": {
        "AUDIO_FORMAT": None,  # Requires decoding before playback
        "MIME_TYPE": "audio/ogg; codecs=opus",
        "RATE": 48000,  # Sampling rate in Hz
        "CHANNELS": 2   # Stereo channels
    },
    "mp3": {
        "AUDIO_FORMAT": None,  # Requires decoding before playback
        "MIME_TYPE": "audio/mpeg",
        "RATE": 48000,  # Sampling rate in Hz
        "CHANNELS": 2   # Stereo channels
    },
    "aac": {
        "AUDIO_FORMAT": None,  # Requires decoding before playback
        "MIME_TYPE": "audio/aac",
        "RATE": 48000,  # Sampling rate in Hz
        "CHANNELS": 2   # Stereo channels
    }
}

# Shared Constants used across the application
SHARED_CONSTANTS = {
    "MINIMUM_PHRASE_LENGTH": 25,  # Minimum length of a phrase for processing
    "TTS_CHUNK_SIZE": 256,        # Chunk size for Text-to-Speech audio streaming
    "DEFAULT_TTS_MODEL": "tts-1",   # Default Text-to-Speech model
    "AUDIO_FORMAT_KEY": "pcm",       # Default audio format key
    "TTS_SPEED": 1.0,               # Speed of the Text-to-Speech playback
    "DELIMITERS": [".", "?", "!"],   # Sentence delimiters for splitting text
    "FRONTEND_PLAYBACK": True       # Enable frontend playback via WebSocket
}

# OpenAI-specific constants
OPENAI_CONSTANTS = {
    **SHARED_CONSTANTS,
    "TEMPERATURE": 0.7,
    "TOP_P": 1.0,
    "MAX_TOKENS": 4000,
    "FREQUENCY_PENALTY": 0.0,
    "PRESENCE_PENALTY": 0.6,
    "STOP": None,
    "LOGIT_BIAS": None,
    "MODEL": "gpt-4o-mini",
    "BEST_OF": 1,
    "STREAM": True,
    "TOP_K_SAMPLING": 40,
    "ECHO": False,
    "DEFAULT_RESPONSE_MODEL": "gpt-4o-mini",  # Default OpenAI response model
    "DEFAULT_VOICE": "alloy",                 # Default voice for Text-to-Speech
    "SYSTEM_PROMPT": {
        "role": "system",
        "content": "You are a dry but witty AI assistant in a group conversation that includes Claude (another AI assistant) and human users. Messages are prefixed to identify the users. Do not prefix your own messages."
    }
}

# Anthropic-specific constants
ANTHROPIC_CONSTANTS = {
    **SHARED_CONSTANTS,
    "TEMPERATURE": 0.8,
    "TOP_P": 0.9,
    "MAX_TOKENS": 3000,
    "FREQUENCY_PENALTY": 0.5,
    "PRESENCE_PENALTY": 0.7,
    "STOP": ["\n", "###"],
    "LOGIT_BIAS": None,
    "MODEL": "claude-3-5-sonnet-20240620",
    "BEST_OF": 1,
    "STREAM": True,
    "TOP_K_SAMPLING": 50,
    "ECHO": False,
    "DEFAULT_RESPONSE_MODEL": "claude-3-5-sonnet-20240620",  # Default Anthropic response model
    "DEFAULT_VOICE": "onyx",                                 # Default voice for Anthropic Text-to-Speech
    "SYSTEM_PROMPT": {
        "role": "system",
        "content": "You are dry, witty and unapologetic. You are in a group conversation that includes GPT (another AI assistant) and human users. Messages are prefixed to identify the users. Do not prefix your own messages."
    }
}

# Function to update audio format settings
def update_audio_format(new_format_key: str):
    # Validate the new format key
    if new_format_key not in AUDIO_CONFIG_MAPPING:
        raise ValueError(f"Unsupported audio format: {new_format_key}")
    
    # Update shared constants with the new format settings
    SHARED_CONSTANTS["AUDIO_FORMAT_KEY"] = new_format_key
    config = AUDIO_CONFIG_MAPPING[new_format_key]
    SHARED_CONSTANTS["AUDIO_FORMAT"] = config["AUDIO_FORMAT"]
    SHARED_CONSTANTS["MIME_TYPE"] = config["MIME_TYPE"]
    SHARED_CONSTANTS["RATE"] = config["RATE"]
    SHARED_CONSTANTS["CHANNELS"] = config["CHANNELS"]

    # Print a note if the new format requires decoding
    if config["AUDIO_FORMAT"] is None:
        print(f"Note: {new_format_key.upper()} format requires decoding before playback.")
    
    # Debug print of updated shared constants (optional)
    print(f"Updated format: {new_format_key}")
    print(f"MIME Type: {SHARED_CONSTANTS['MIME_TYPE']}")
    print(f"Channels: {SHARED_CONSTANTS['CHANNELS']}")
    print(f"Sample Rate: {SHARED_CONSTANTS['RATE']} Hz")

# Initialize OpenAI API client with API key from environment variables
aclient = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize Anthropic API client with API key from environment variables
anthropic_client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Initialize ConnectionManager for WebSocket communication
connection_manager = ConnectionManager()

# Get the main event loop
try:
    loop = asyncio.get_event_loop()
except RuntimeError:
    # If there's no running event loop in the current thread, create a new one
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
