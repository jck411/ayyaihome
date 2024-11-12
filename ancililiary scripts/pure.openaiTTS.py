import logging
import os
import time
from dotenv import load_dotenv
from RealtimeTTS import TextToAudioStream, OpenAIEngine

# Load environment variables from .env file in the root directory
load_dotenv()

# Retrieve the API key from environment variables
openai_api_key = os.getenv("OPENAI_API_KEY")

# Initialize OpenAIEngine with the API key if required
engine = OpenAIEngine()  # Pass the API key if needed

# Initialize the stream with adjusted settings for smooth playback
stream = TextToAudioStream(
    engine, 
    log_characters=True,        # Enables character-level logging for debugging
    tokenizer="nltk",           # Sentence tokenizer
    language="en",              # Set to English for accurate text processing
    muted=False,                # Ensure local playback is active
    level=logging.DEBUG,        # Set logging to debug for comprehensive logs
)

# Feed text to the stream
text = ("Contrary to popular belief, Lorem Ipsum is not simply random text. "
        "It has roots in classical Latin literature from 45 BC, making it over 2000 years old. "
        "Richard McClintock, a Latin professor at Hampden-Sydney College in Virginia, looked up "
        "one of the more obscure Latin words, consectetur, from a Lorem Ipsum passage, and going "
        "through the cites of the word in classical literature, discovered the undoubtable source. "
        "Lorem Ipsum comes from sections 1.10.32 and 1.10.33 of -de Finibus Bonorum et Malorum- "
        "by Cicero, written in 45 BC. This book is a treatise on ethics, popular during the Renaissance. "
        "The first line of Lorem Ipsum, comes from section 1.10.32.")
stream.feed(text)

# Optional delay to allow buffer to fill initially
time.sleep(0.5)  # Increase if needed to reduce initial stuttering

# Play with async for more seamless buffering in continuous speech synthesis
stream.play_async(
    buffer_threshold_seconds=1.5,   # Increased threshold to help smooth playback
    minimum_sentence_length=20,     # Length before a sentence is processed for playback
    minimum_first_fragment_length=15,  # Minimum characters in the first sentence fragment
)


#try this on PC , computing power may be issue