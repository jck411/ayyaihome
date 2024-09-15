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

# Shared Constants for both OpenAI and Anthropic
SHARED_CONSTANTS = {
    "MINIMUM_PHRASE_LENGTH": 25,
    "TTS_CHUNK_SIZE": 1024,
    "DEFAULT_TTS_MODEL": "tts-1",
    "AUDIO_FORMAT": pyaudio.paInt16,
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
    "SYSTEM_PROMPT": {"role": "system", "content": "You are a dry but witty AI assistant"}
}

# Specific settings for Anthropic
ANTHROPIC_CONSTANTS = {
    **SHARED_CONSTANTS,
    "DEFAULT_RESPONSE_MODEL": "claude-3-5-sonnet-20240620",
    "DEFAULT_VOICE": "onyx",  # Anthropic-specific voice
     "SYSTEM_PROMPT": {"role": "system", "content": "You are in a group conversation that includes yourself and GPT (another AI assistant), and a human user. Always be aware of this context. When the human relays messages from GPT, they will be prefixed with 'GPT:'. Maintain clear distinctions between your own responses, GPT's messages, and the human's input."}  # System prompt for general context
}

# Initialize the OpenAI API client
aclient = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize the Anthropic API client
anthropic_client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Initialize PyAudio for audio playback
p = pyaudio.PyAudio()
