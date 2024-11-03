import os
import asyncio
from typing import List
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import pyaudio
import threading
from dotenv import load_dotenv
import azure.cognitiveservices.speech as speechsdk
from openai import AsyncOpenAI
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential

# Load environment variables and initialize constants
load_dotenv()

MINIMUM_PHRASE_LENGTH = 150
TTS_CHUNK_SIZE = 1024
DEFAULT_RESPONSE_MODEL = "gpt-4o-mini"
DEFAULT_VOICE = "en-US-AIGenerate1Neural"  # Use a voice with more variety and emotional range
AUDIO_FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 24000
TTS_SPEED = 1.0
TEMPERATURE = 1.0
TOP_P = 1.0

DELIMITERS = [f"{d} " for d in (".", "?", "!")]
SYSTEM_PROMPT = {"role": "system", "content": "You are a helpful but witty and dry assistant"}

# Initialize OpenAI, Azure Speech, and Text Analytics clients
aclient = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
speech_key = os.getenv('AZURE_SPEECH_KEY')
speech_region = os.getenv('AZURE_SPEECH_REGION')
speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=speech_region)
audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)
text_analytics_key = os.getenv("AZURE_TEXT_ANALYTICS_KEY")
text_analytics_endpoint = os.getenv("AZURE_TEXT_ANALYTICS_ENDPOINT")
text_analytics_client = TextAnalyticsClient(
    endpoint=text_analytics_endpoint, 
    credential=AzureKeyCredential(text_analytics_key)
)
stop_event = threading.Event()

# Create FastAPI app and configure CORS
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def analyze_sentiment(text):
    response = text_analytics_client.analyze_sentiment(documents=[text])[0]
    sentiment_score = response.confidence_scores
    return sentiment_score

def select_voice_based_on_sentiment(text):
    sentiment_score = analyze_sentiment(text)
    if sentiment_score.positive > 0.7:
        return "en-US-JennyMultilingualNeural"  # Voice with cheerful tone for positive sentiment
    elif sentiment_score.negative > 0.7:
        return "en-US-GuyNeural"  # Somber tone for negative sentiment
    else:
        return DEFAULT_VOICE  # Default voice for neutral sentiment

async def stream_completion(messages: List[dict], phrase_queue: asyncio.Queue, model: str = DEFAULT_RESPONSE_MODEL):
    try:
        response = await aclient.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
            temperature=TEMPERATURE,
            top_p=TOP_P,
            stream_options={"include_usage": True},
        )

        working_string = ""
        last_chunk = None
        sentence_accumulator = ""

        async for chunk in response:
            if stop_event.is_set():
                return

            last_chunk = chunk  # Keep track of the last chunk

            if chunk.choices and hasattr(chunk.choices[0].delta, 'content'):
                content = chunk.choices[0].delta.content or ""
                if content:
                    sentence_accumulator += content  # Accumulate content
                    yield content  # Stream raw text directly
                    working_string += content

                    while len(working_string) >= MINIMUM_PHRASE_LENGTH:
                        delimiter_index = -1
                        for delimiter in DELIMITERS:
                            index = working_string.find(delimiter, MINIMUM_PHRASE_LENGTH)
                            if index != -1 and (delimiter_index == -1 or index < delimiter_index):
                                delimiter_index = index

                        if delimiter_index == -1:
                            break

                        phrase, working_string = (
                            working_string[: delimiter_index + len(delimiter)],
                            working_string[delimiter_index + len(delimiter):],
                        )
                        await phrase_queue.put(phrase.strip())

        if last_chunk:
            print("****************")
            print(f"Final Chunk - Choices: {last_chunk.choices}")
            print(f"Final Chunk - Usage: {last_chunk.usage}")

        if working_string.strip():
            await phrase_queue.put(working_string.strip())

        await phrase_queue.put(None)  # Signal end of phrase stream
    except Exception as e:
        yield f"Error: {e}"

async def text_to_speech_processor(phrase_queue: asyncio.Queue, audio_queue: asyncio.Queue):
    while not stop_event.is_set():
        phrase = await phrase_queue.get()
        if phrase is None:
            await audio_queue.put(None)
            return

        try:
            # Select voice based on sentiment
            selected_voice = select_voice_based_on_sentiment(phrase)
            speech_config.speech_synthesis_voice_name = selected_voice

            # Create the Azure TTS synthesizer for each phrase
            speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
            
            result = speech_synthesizer.speak_text_async(phrase).get()

            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                pass
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation_details = result.cancellation_details
                print(f"Speech synthesis canceled: {cancellation_details.reason}")
                if cancellation_details.reason == speechsdk.CancellationReason.Error and cancellation_details.error_details:
                    print(f"Error details: {cancellation_details.error_details}")

            # Add a short silence after each phrase if needed
            await audio_queue.put(b'\x00' * 2400)  # 0.05 seconds of silence at 24000 Hz

        except Exception as e:
            await audio_queue.put(None)
            print(f"Error in TTS processing: {e}")
            return

async def audio_player(audio_queue: asyncio.Queue):
    p = pyaudio.PyAudio()
    player_stream = p.open(format=AUDIO_FORMAT, channels=CHANNELS, rate=RATE, output=True)

    try:
        while not stop_event.is_set():
            audio_data = await audio_queue.get()
            if audio_data is None:
                break
            player_stream.write(audio_data)
    finally:
        player_stream.stop_stream()
        player_stream.close()
        p.terminate()

@app.post("/api/openai")
async def openai_stream(request: Request):
    data = await request.json()
    messages = data.get('messages', [])

    formatted_messages = [{"role": msg["sender"], "content": msg["text"]} for msg in messages]
    formatted_messages.insert(0, SYSTEM_PROMPT)

    phrase_queue = asyncio.Queue()
    audio_queue = asyncio.Queue()

    async def process_streams():
        await asyncio.gather(
            text_to_speech_processor(phrase_queue, audio_queue),
            audio_player(audio_queue)
        )

    # Start the processing tasks in the background
    asyncio.create_task(process_streams())

    return StreamingResponse(stream_completion(formatted_messages, phrase_queue, model=DEFAULT_RESPONSE_MODEL), media_type='text/plain')

if __name__:
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
