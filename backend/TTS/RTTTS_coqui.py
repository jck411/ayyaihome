import os
import logging
from RealtimeTTS import TextToAudioStream, CoquiEngine

# Initialize Coqui TTS engine with adjustable parameters
tts_engine = CoquiEngine(
    model_name="tts_models/multilingual/multi-dataset/xtts_v2",  # Name of the Coqui TTS model
    specific_model="v2.0.2",                                     # Specific model version
    local_models_path=None,                                       # Path to local models (None to use default)
    voices_path=None,                                             # Path to custom voices (if any)
    voice="",                                                     # Voice cloning reference file path
    language="en",                                                # Language code
    speed=1.0,                                                    # Speech speed factor
    thread_count=6,                                               # Number of threads to use
    stream_chunk_size=20,                                         # Chunk size for streaming
    overlap_wav_len=1024,                                         # Overlap length for streaming
    temperature=0.85,                                             # Sampling temperature
    length_penalty=1.0,                                           # Length penalty
    repetition_penalty=7.0,                                       # Repetition penalty
    top_k=50,                                                     # Top-k sampling
    top_p=0.85,                                                   # Top-p (nucleus) sampling
    enable_text_splitting=True,                                   # Enable text splitting
    full_sentences=False,                                         # Synthesize full sentences
    level=logging.WARNING,                                        # Logging level
    use_deepspeed=False,                                          # Use DeepSpeed for inference
    device=None,                                                  # Device to use ('cuda', 'cpu', etc.)
    prepare_text_for_synthesis_callback=None,                     # Custom text preparation function
    add_sentence_filter=False,                                    # Add additional sentence filtering
    pretrained=False,                                             # Use pretrained model
    comma_silence_duration=0.3,                                   # Silence duration after commas
    sentence_silence_duration=0.6,                                # Silence duration after sentences
    default_silence_duration=0.3,                                 # Default silence duration
    print_realtime_factor=False                                   # Print real-time factor statistics
    # You can adjust the parameters above to change TTS settings
)

def play_text_stream(text_stream):
    """
    Plays a text stream using the TextToAudioStream with Coqui TTS engine.
    
    Parameters:
        text_stream (generator): A generator yielding text chunks to be synthesized.
        
    This function feeds the text stream into the TTS engine and begins playback.
    """
    # Initialize TextToAudioStream with Coqui TTS engine and additional playback parameters
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
