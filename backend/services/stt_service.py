# /home/jack/ayyaihome/backend/services/stt_service.py

import azure.cognitiveservices.speech as speechsdk
import asyncio
import logging
import os
from dotenv import load_dotenv
from fastapi import WebSocket

# Load environment variables from the .env file
load_dotenv('/home/jack/ayyaihome/backend/.env')

# Configure Azure STT
def get_speech_config():
    # Fetch the keys from environment variables
    speech_key = os.getenv('AZURE_SPEECH_KEY')
    service_region = os.getenv('AZURE_REGION')

    if not speech_key or not service_region:
        raise ValueError("AZURE_SPEECH_KEY and AZURE_REGION must be set in the .env file.")

    # Configure Azure Speech SDK
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
    speech_config.speech_recognition_language = "en-US"

    return speech_config

# Start microphone recognition and stream STT results to WebSocket
async def start_microphone_recognition(websocket: WebSocket, loop: asyncio.AbstractEventLoop):
    speech_config = get_speech_config()
    audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)

    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

    # Event handler for recognized speech
    def recognized_handler(evt):
        if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
            # Get the recognized text
            recognized_text = evt.result.text

            # Log the recognized text to the terminal
            logging.info(f"Recognized text: {recognized_text}")

            # Send recognized text to the WebSocket
            asyncio.run_coroutine_threadsafe(
                websocket.send_json({'type': 'stt_result', 'text': recognized_text}),
                loop
            )

    # Connect the event handler to the recognizer
    speech_recognizer.recognized.connect(recognized_handler)

    # Start continuous recognition
    speech_recognizer.start_continuous_recognition()

    try:
        while True:
            await asyncio.sleep(1)  # Keep the server running to listen for events
    except asyncio.CancelledError:
        logging.info("Stopping recognition...")
        speech_recognizer.stop_continuous_recognition()
