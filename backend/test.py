import os
import asyncio
from dotenv import load_dotenv
import azure.cognitiveservices.speech as speechsdk
from openai import AsyncOpenAI

# Load environment variables from .env file
load_dotenv()

# Fetch API keys from environment variables
api_key = os.getenv("OPENAI_API_KEY")
azure_key = os.getenv("AZURE_SPEECH_KEY")
azure_region = os.getenv("AZURE_REGION")

if not all([api_key, azure_key, azure_region]):
    raise EnvironmentError("Missing required environment variables.")

# OpenAI Client
client = AsyncOpenAI(api_key=api_key)

# Azure TTS Configuration
speech_config = speechsdk.SpeechConfig(subscription=azure_key, region=azure_region)
speech_config.speech_synthesis_voice_name = "en-US-Andrew:DragonHDLatestNeural"  # Set default voice
MINIMUM_PHRASE_LENGTH = 100  # Minimum length of a phrase before processing
DELIMITERS = [".", "?", "!"]

# Function to split streaming content into phrases
def split_text_into_phrases(streaming_text: str, buffer: str) -> tuple[list[str], str]:
    """
    Splits streaming text into phrases based on delimiters and minimum length.
    Args:
        streaming_text (str): Incoming text from the stream.
        buffer (str): Buffer holding unprocessed text from previous iterations.
    Returns:
        tuple[list[str], str]: A list of complete phrases and the remaining buffer text.
    """
    buffer += streaming_text
    phrases = []
    while len(buffer) >= MINIMUM_PHRASE_LENGTH:
        for delimiter in DELIMITERS:
            index = buffer.find(delimiter, MINIMUM_PHRASE_LENGTH)
            if index != -1:
                phrases.append(buffer[: index + 1].strip())
                buffer = buffer[index + 1:].strip()
                break
        else:
            break
    return phrases, buffer

# Function to convert a single phrase to speech
async def text_to_speech(phrase: str) -> bytes:
    """
    Converts a single phrase to speech audio using Azure TTS.
    Args:
        phrase (str): The input phrase to synthesize.
    Returns:
        bytes: The synthesized audio data.
    """
    audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)
    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
    result_future = speech_synthesizer.speak_text_async(phrase)
    result = await asyncio.to_thread(result_future.get)

    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        return result.audio_data
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = result.cancellation_details
        raise Exception(f"TTS canceled: {cancellation_details.reason} - {cancellation_details.error_details}")
    else:
        raise Exception("Unknown TTS error occurred.")

# Main function to stream OpenAI responses and process them with TTS
async def process_streamed_text_to_speech():
    """
    Streams text from OpenAI API and processes it into speech using Azure TTS.
    """
    buffer = ""  # Holds unprocessed text
    completion = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Tell me a 100-word story about streaming."}
        ],
        temperature=0.5,
        max_tokens=256,
        stream=True
    )

    # Process chunks from OpenAI stream
    async for chunk in completion:
        # Extract content from the stream
        if "content" in chunk.choices[0].delta:
            streaming_text = chunk.choices[0].delta.content
            # Split text into phrases
            phrases, buffer = split_text_into_phrases(streaming_text, buffer)
            for phrase in phrases:
                print(f"Processing phrase: {phrase}")
                await text_to_speech(phrase)

    # Process any remaining text in the buffer
    if buffer.strip():
        print(f"Processing final buffer: {buffer}")
        await text_to_speech(buffer)

# Run the main function
if __name__ == "__main__":
    asyncio.run(process_streamed_text_to_speech())
