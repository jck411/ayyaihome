import os
import asyncio
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Configure Azure Speech SDK
speech_config = speechsdk.SpeechConfig(
    subscription=os.getenv('SPEECH_KEY'),
    region=os.getenv('SPEECH_REGION')
)
speech_config.speech_recognition_language = "en-US"
speech_config.set_property(
    property_id=speechsdk.PropertyId.SpeechServiceResponse_DiarizeIntermediateResults,
    value='true'
)

# Initialize audio config for default microphone
audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)

async def process_conversation_transcription(websocket: WebSocket, queue: asyncio.Queue):
    conversation_transcriber = speechsdk.transcription.ConversationTranscriber(
        speech_config=speech_config,
        audio_config=audio_config
    )

    def transcribed_cb(evt: speechsdk.SpeechRecognitionEventArgs):
        if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
            queue.put_nowait({
                "type": "transcribed",
                "text": evt.result.text,
                "speaker_id": evt.result.speaker_id
            })

    def transcribing_cb(evt: speechsdk.SpeechRecognitionEventArgs):
        queue.put_nowait({
            "type": "transcribing",
            "text": evt.result.text,
            "speaker_id": evt.result.speaker_id
        })

    def session_started_cb(evt: speechsdk.SessionEventArgs):
        queue.put_nowait({
            "type": "info",
            "message": "Session started"
        })

    def session_stopped_cb(evt: speechsdk.SessionEventArgs):
        queue.put_nowait({
            "type": "info",
            "message": "Session stopped"
        })

    def canceled_cb(evt: speechsdk.SessionEventArgs):
        queue.put_nowait({
            "type": "info",
            "message": f"Canceled: {evt.cancellation_details.reason}"
        })

    conversation_transcriber.transcribed.connect(transcribed_cb)
    conversation_transcriber.transcribing.connect(transcribing_cb)
    conversation_transcriber.session_started.connect(session_started_cb)
    conversation_transcriber.session_stopped.connect(session_stopped_cb)
    conversation_transcriber.canceled.connect(canceled_cb)

    await websocket.send_text("Starting conversation transcription...")
    conversation_transcriber.start_transcribing_async()

    try:
        while True:
            data = await queue.get()
            await websocket.send_json(data)
    except asyncio.CancelledError:
        conversation_transcriber.stop_transcribing_async()
        await websocket.send_text("Conversation transcription stopped.")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    queue = asyncio.Queue()
    
    transcription_task = asyncio.create_task(process_conversation_transcription(websocket, queue))
    
    try:
        while True:
            data = await websocket.receive_text()
            if data == "stop":
                break
    finally:
        transcription_task.cancel()
        try:
            await transcription_task
        except asyncio.CancelledError:
            pass

# Serve static files (frontend)
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)