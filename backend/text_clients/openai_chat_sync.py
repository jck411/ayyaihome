from backend.config import client, default_model
from backend.TTS.RTTTS_openai import play_text_stream  # Corrected function name

def generate_text_stream_sync(messages):
    """
    Synchronous generator function for text stream from OpenAI.

    Parameters:
        messages (list): List of message dictionaries with role and content.

    Yields:
        str: Text chunks from OpenAI response for TTS.
    """
    response = client.chat.completions.create(
        model=default_model,
        messages=messages,
        stream=True
    )
    for chunk in response:
        # Access the content directly
        text_chunk = chunk.choices[0].delta.content
        if text_chunk:
            yield text_chunk

def generate_and_play_tts(messages):
    """
    Generate text using OpenAI in synchronous mode and play TTS.

    Parameters:
        messages (list): List of message dictionaries with role and content.

    Returns:
        None
    """
    # Create a synchronous response stream from OpenAI
    text_stream = generate_text_stream_sync(messages)
    play_text_stream(text_stream)
