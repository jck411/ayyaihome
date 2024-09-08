import os
import threading
import pyaudio
from dotenv import load_dotenv
from openai import AsyncOpenAI
import anthropic  # Import the Anthropic SDK

# Load environment variables from a .env file
load_dotenv()

# Global stop event
stop_event = threading.Event()

# Constants used throughout the application
CONSTANTS = {
    "MINIMUM_PHRASE_LENGTH": 25,
    "TTS_CHUNK_SIZE": 1024,
    "DEFAULT_RESPONSE_MODEL": "gpt-4o-mini",
    "DEFAULT_TTS_MODEL": "tts-1",
    "DEFAULT_VOICE": "alloy",
    "AUDIO_FORMAT": pyaudio.paInt16,
    "CHANNELS": 1,
    "RATE": 24000,
    "TTS_SPEED": 1.0,
    "TEMPERATURE": 1.0,
    "TOP_P": 1.0,
    "DELIMITERS": [".", "?", "!"],
    "SYSTEM_PROMPT": {"role": "system", "content": "You are a dry but witty AI assistant"}
}

# Initialize the OpenAI API client
aclient = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize the Anthropic API client
anthropic_client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Initialize PyAudio for audio playback
p = pyaudio.PyAudio()
