import os
from dotenv import load_dotenv
from openai import OpenAI
from RealtimeTTS import TextToAudioStream, OpenAIEngine

# Load environment variables
load_dotenv("/home/jack/aaaRealtime/.env")

# Retrieve API key
openai_api_key = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client and TTS engine with adjustable parameters
client = OpenAI(api_key=openai_api_key)
tts_engine = OpenAIEngine(
    model="tts-1",                # Model for TTS (e.g., "tts-1", "tts-1-hd")
    voice="alloy"                 # Voice selection, e.g., "alloy", "nova", "echo"
)

def generate_text_and_play_tts(messages):
    """
    Generate text using OpenAI and stream it to TTS for real-time playback.
    
    Parameters:
        messages (list): List of message dictionaries with role and content.
        
    Returns:
        None
    """
    # Create a streaming response from OpenAI
    stream = client.chat.completions.create(
        model="gpt-4o-mini",       # Select the model for text generation
        messages=messages,         # Input messages
        stream=True                # Enables streaming of the response
    )

    # Initialize TTS stream with OpenAI TTS engine
    tts_stream = TextToAudioStream(
        engine=tts_engine,
        log_characters=True        # Logs characters processed for synthesis
    )

    # Feed the OpenAI streaming response directly to TextToAudioStream and start playback
    tts_stream.feed(stream).play()

    # Optional asynchronous playback:
    # tts_stream.play_async()

# Usage example within this module or importable elsewhere
if __name__ == "__main__":
    # Define the messages to be processed
    messages = [
        {"role": "user", "content": "Tell me a story about a curious cat."}
    ]

    # Call the function to generate text and play TTS
    generate_text_and_play_tts(messages)
