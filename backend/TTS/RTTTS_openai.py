import os
from dotenv import load_dotenv
from openai import OpenAI
from RealtimeTTS import TextToAudioStream, OpenAIEngine

# Load environment variables from the specified .env file
load_dotenv("/home/jack/aaaRealtime/.env")

# Retrieve API key from environment variables
openai_api_key = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client and OpenAI TTS engine with adjustable parameters
client = OpenAI(api_key=openai_api_key)
tts_engine = OpenAIEngine(
    model="tts-1",               # Model for TTS (options depend on OpenAI's offerings, e.g., "tts-1", "tts-1-hd")
    voice="alloy"                # Voice selection, e.g., "alloy", "nova", "echo"
)

def play_text_stream(text_stream):
    """
    Plays a text stream using the TextToAudioStream with OpenAI TTS engine.
    
    Parameters:
        text_stream (generator): A generator yielding text chunks from OpenAI's response.
        
    This function feeds the text stream into the TTS engine and begins playback.
    """
    # Initialize TextToAudioStream with OpenAI TTS engine and additional playback parameters
    tts_stream = TextToAudioStream(
        engine=tts_engine,
        log_characters=True,      # Logs characters processed for synthesis
        # Additional optional settings can be added here if required
        ## on_text_stream_start=None,  # Optional callback when text stream starts
        ## on_text_stream_stop=None,   # Optional callback when text stream stops
        ## on_audio_stream_start=None, # Optional callback when audio stream starts
        ## on_audio_stream_stop=None,  # Optional callback when audio stream stops
        ## output_device_index=None,   # Audio output device index (None for default)
        ## tokenizer="nltk",           # Tokenizer for sentence splitting (options: "nltk", "stanza")
        ## language="en",              # Language for sentence splitting
        ## muted=False,                # Mutes audio output (if True)
        ## level=logging.INFO          # Sets logging level for internal processes
    )

    # Feed the OpenAI text stream into TextToAudioStream and start playback
    tts_stream.feed(text_stream).play()

# Optional async variant of play_text_stream if async playback is needed  ###  ###  make a seperate tts module for this later ##  ###  ###
async def play_text_stream_async(text_stream):
    """
    Asynchronously plays a text stream using the TextToAudioStream with OpenAI TTS engine.

    Parameters:
        text_stream (async generator): An async generator yielding text chunks.
        
    This function supports asynchronous playback, enabling non-blocking execution.
    """
    tts_stream = TextToAudioStream(
        engine=tts_engine,
        log_characters=True,       # Logs characters processed for synthesis
        # Optional settings and callbacks can be defined similarly to the sync version
    )

    # Async feed for streaming audio asynchronously
    await tts_stream.feed(text_stream).play_async()
