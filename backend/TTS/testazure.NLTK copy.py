import asyncio
import queue
import os
import logging
from typing import Optional, List
from dotenv import load_dotenv
import azure.cognitiveservices.speech as speechsdk
from nltk.tokenize import sent_tokenize

# Load environment variables from .env file
load_dotenv(dotenv_path="/home/jack/ayyaihome/backend/.env")

# Azure TTS keys
AZURE_SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")
AZURE_REGION = os.getenv("AZURE_REGION")

if not all([AZURE_SPEECH_KEY, AZURE_REGION]):
    raise EnvironmentError("Missing required environment variables in .env file.")

# Initialize logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Default options
DEFAULT_VOICE_NAME = "en-US-Andrew:DragonHDLatestNeural"  # Example voice
DEFAULT_TTS_SPEED = "1.0"  # Speech speed
DEFAULT_CHUNK_SIZE = 2400  # Audio chunk size in bytes
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"  # OpenAI model to use
MINIMUM_PHRASE_LENGTH = 25  # Minimum length for a phrase


async def azure_text_to_speech_processor(
    phrase_queue: asyncio.Queue,
    audio_queue: queue.Queue,
    speech_config: Optional[speechsdk.SpeechConfig] = None
):
    """
    Processes phrases into speech using Azure TTS and stores audio in the audio queue.
    """
    if speech_config is None:
        speech_config = speechsdk.SpeechConfig(subscription=AZURE_SPEECH_KEY, region=AZURE_REGION)
        speech_config.speech_synthesis_voice_name = DEFAULT_VOICE_NAME
        speech_config.speech_synthesis_rate = DEFAULT_TTS_SPEED

    try:
        while True:
            phrase = await phrase_queue.get()
            if phrase is None:
                audio_queue.put(None)
                return

            try:
                # Synthesize speech
                audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)
                synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
                result_future = synthesizer.speak_text_async(phrase)
                result = await asyncio.to_thread(result_future.get)

                if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                    audio_queue.put(result.audio_data)
                elif result.reason == speechsdk.ResultReason.Canceled:
                    details = result.cancellation_details
                    logger.error(f"TTS canceled: {details.reason} - {details.error_details}")
                else:
                    logger.error("Unknown TTS error occurred.")
            except Exception as e:
                logger.error(f"Error in Azure TTS for phrase '{phrase}': {e}")

            # Add a small pause between phrases
            audio_queue.put(b'\x00' * DEFAULT_CHUNK_SIZE)

    except Exception as e:
        logger.error(f"Error in TTS processing: {e}")
        audio_queue.put(None)


async def stream_text_to_speech_with_queues():
    """
    Streams text from OpenAI, processes it into phrases, and uses Azure TTS to convert them to speech.
    """
    phrase_queue = asyncio.Queue()
    audio_queue = queue.Queue()

    async def stream_openai_text():
        from openai import AsyncOpenAI  # Inline import for clarity
        client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        messages = [{"role": "user", "content": "tell zoe a bed time story about her toy kitty family, mommy and daddy kitty, and baby kitty. Make sure you say it slow so it makes her sleepy"}]
        buffer = ""  # Holds unprocessed text

        try:
            logger.info("Starting OpenAI streaming...")
            response = await client.chat.completions.create(
                model=DEFAULT_OPENAI_MODEL,
                messages=messages,
                stream=True
            )

            async for chunk in response:
                content = chunk.choices[0].delta.content
                if content:
                    logger.info(f"Received chunk: {content}")
                    buffer += content

                    # Use NLTK to split text into sentences
                    sentences = sent_tokenize(buffer)
                    buffer = sentences.pop()  # Keep the last incomplete sentence in the buffer

                    for sentence in sentences:
                        if len(sentence) >= MINIMUM_PHRASE_LENGTH:
                            await phrase_queue.put(sentence.strip())

            # Process remaining buffer
            if buffer.strip():
                await phrase_queue.put(buffer.strip())

            # Signal end of text streaming
            await phrase_queue.put(None)
            logger.info("OpenAI streaming completed.")

        except Exception as e:
            logger.error(f"Error during OpenAI streaming: {e}")
            await phrase_queue.put(None)

    tts_task = asyncio.create_task(azure_text_to_speech_processor(phrase_queue, audio_queue))

    await stream_openai_text()
    await tts_task

    logger.info("Saving audio output...")
    with open("output_audio.wav", "wb") as f:
        while True:
            audio_chunk = audio_queue.get()
            if audio_chunk is None:
                break
            f.write(audio_chunk)


if __name__ == "__main__":
    asyncio.run(stream_text_to_speech_with_queues())
