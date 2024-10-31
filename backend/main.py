import asyncio
import logging
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import os
from dotenv import load_dotenv
from openai import OpenAI
import pyaudio

# Initialize FastAPI
app = FastAPI()

# Load environment variables and initialize OpenAI API client
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize PyAudio for audio playback
p = pyaudio.PyAudio()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_TTS_MODEL = "tts-1"   # Default Text-to-Speech model
DEFAULT_VOICE = "alloy"       # Default voice for Text-to-Speech
MODEL = "gpt-4o-mini"
STREAM = True

# Endpoint to trigger hardcoded OpenAI request with TTS playback
@app.get("/api/openai")
async def openai_stream():
    """
    Handles GET requests to the "/api/openai" endpoint.
    Sends a hardcoded message to OpenAI, streams the response, and plays it back as TTS.
    """
    logger.info("Received request at /api/openai")

    # Define a hardcoded message for testing
    messages = [
        {"role": "user", "content": "repeat this exactly: this is a test to see how long you can talk without stopping when there are no delimiters used in a long text. How's that?"}
    ]

    # Fetch the completion response from OpenAI and process as TTS
    async def stream_response():
        try:
            # Send the request to OpenAI for streaming response
            response = await client.chat.completions.create(
                model=MODEL,
                messages=messages,
                stream=STREAM
            )

            # Initialize PyAudio stream for playback
            audio_stream = p.open(format=pyaudio.paInt16, channels=1, rate=24000, output=True)

            async for chunk in response:
                content = getattr(chunk.choices[0].delta, 'content', "")
                if content:
                    logger.debug(f"Streaming content: {content}")
                    # Convert content to speech and yield for playback
                    async for audio_chunk in text_to_speech(content):
                        audio_stream.write(audio_chunk)
                        yield content  # Stream content back to the client

            audio_stream.close()
        except Exception as e:
            logger.error(f"Error in stream_response: {e}")
            yield f"Error: {e}"

    return StreamingResponse(stream_response(), media_type='text/plain')

async def text_to_speech(text):
    """
    Converts text to speech using OpenAI's TTS API and yields audio data chunks.
    """
    try:
        response = await client.audio.speech.create(
            model=DEFAULT_TTS_MODEL,
            voice=DEFAULT_VOICE,
            input=text,
            stream=True
        )
        
        async for chunk in response:
            # Each chunk contains audio data
            yield chunk
    except Exception as e:
        logger.error(f"Error in text_to_speech: {e}")

# Run the FastAPI app
if __name__ == '__main__':
    import uvicorn
    logger.info("Starting the Uvicorn server.")
    uvicorn.run(app, host='0.0.0.0', port=8000)
