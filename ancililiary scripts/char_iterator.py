import os
import time
from dotenv import load_dotenv
from RealtimeTTS import TextToAudioStream, OpenAIEngine
import logging

# Load environment variables from .env file in the root directory
load_dotenv()

# Retrieve the API key from environment variables
openai_api_key = os.getenv("OPENAI_API_KEY")

# Initialize OpenAIEngine with the API key if required
engine = OpenAIEngine()  # Pass the API key if needed

# Initialize the stream with the OpenAI Engine
stream = TextToAudioStream(
    engine,
    log_characters=True,  # Log characters for debugging
    language="en",
    muted=False,
    level=logging.DEBUG
)

# Create a character-by-character iterator
char_iterator = iter("Contrary to popular belief, Lorem Ipsum is not simply random text. "
        "It has roots in classical Latin literature from 45 BC, making it over 2000 years old. "
        "Richard McClintock, a Latin professor at Hampden-Sydney College in Virginia, looked up "
        "one of the more obscure Latin words, consectetur, from a Lorem Ipsum passage, and going "
        "through the cites of the word in classical literature, discovered the undoubtable source. "
        "Lorem Ipsum comes from sections 1.10.32 and 1.10.33 of -de Finibus Bonorum et Malorum- "
        "by Cicero, written in 45 BC. This book is a treatise on ethics, popular during the Renaissance. "
        "The first line of Lorem Ipsum, comes from section 1.10.32.")

# Feed the iterator and start playback
stream.feed(char_iterator)

# Start asynchronous playback
stream.play_async(
    buffer_threshold_seconds=0.5,  # Lower buffer for faster response to each character
    minimum_sentence_length=1,     # Minimal sentence length to process each character
    minimum_first_fragment_length=1,  # Process each character as soon as it arrives
)

# Optional sleep to keep playback active for the iterator to finish
while stream.is_playing():
    time.sleep(0.1)  # Adjust as necessary
