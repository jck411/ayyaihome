import os
from dotenv import load_dotenv
from RealtimeTTS import TextToAudioStream, AzureEngine

# Load environment variables from the specified .env file
load_dotenv("/path/to/your/.env")  # Change this path to your .env file if needed

# Retrieve Azure TTS credentials from environment variables
azure_speech_key = os.getenv("AZURE_SPEECH_KEY")
azure_service_region = os.getenv("AZURE_SERVICE_REGION")

# Initialize Azure TTS engine with adjustable parameters
tts_engine = AzureEngine(
    speech_key=azure_speech_key,          # Your Azure subscription key (TTS API key)
    service_region=azure_service_region,  # Your Azure service region (Cloud Region ID)
    voice="en-US-AshleyNeural",           # Voice name; change to use a different voice
    rate=0.0,                             # Speech speed as a percentage (e.g., 0.0 for default speed)
    pitch=0.0                             # Speech pitch as a percentage (e.g., 0.0 for default pitch)
    # You can adjust 'voice', 'rate', and 'pitch' to change TTS settings
)

def play_text_stream(text_stream):
    """
    Plays a text stream using the TextToAudioStream with Azure TTS engine.
    
    Parameters:
        text_stream (generator): A generator yielding text chunks to be synthesized.
        
    This function feeds the text stream into the TTS engine and begins playback.
    """
    # Initialize TextToAudioStream with Azure TTS engine and additional playback parameters
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

    # Feed the text stream into TextToAudioStream and start playback
    tts_stream.feed(text_stream).play()
