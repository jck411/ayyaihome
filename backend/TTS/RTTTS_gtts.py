import os
from RealtimeTTS import TextToAudioStream, GTTSEngine, GTTSVoice

# Initialize GTTS TTS engine with adjustable parameters
tts_engine = GTTSEngine(
    voice=GTTSVoice(
        language="en",             # Language code (e.g., 'en' for English)
        tld="com",                 # Top-level domain for the Google Translate host (e.g., 'com', 'co.uk')
        chunk_length=100,          # Chunk length for speed increase processing
        crossfade_length=10,       # Crossfade length between chunks
        speed_increase=1.0         # Playback speed increase factor (e.g., 1.0 for normal speed)
    ),
    print_installed_voices=False   # Set to True to print available voices
    # You can adjust 'voice' parameters to change language, tld, chunk settings, and speed
)

def play_text_stream(text_stream):
    """
    Plays a text stream using the TextToAudioStream with GTTS engine.
    
    Parameters:
        text_stream (generator): A generator yielding text chunks to be synthesized.
        
    This function feeds the text stream into the TTS engine and begins playback.
    """
    # Initialize TextToAudioStream with GTTS engine and additional playback parameters
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
