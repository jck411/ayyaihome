# /home/jack/ayyaihome/backend/services/azure_keyword_recognition.py

#!/usr/bin/env python
# coding: utf-8

import time
import azure.cognitiveservices.speech as speechsdk
import asyncio
import logging

from init import connection_manager, loop  # Import the ConnectionManager and event loop
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv("/home/jack/ayyaihome/backend/.env")

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Set up the subscription info for the Speech Service:
speech_key = os.getenv('AZURE_SPEECH_KEY')
service_region = os.getenv('AZURE_REGION')

def speech_recognize_keyword():
    """Performs keyword-triggered speech recognition from the microphone"""

    logging.info("Initializing Azure Speech Service...")

    # Create the speech configuration
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)

    # Create the keyword recognition model
    model = speechsdk.KeywordRecognitionModel("/home/jack/ayyaihome/backend/services/a8fb67d6-474d-49e0-b04b-0692a58a544f.table")

    # Define the keyword to be recognized
    keyword = "Hey Computer"  # Replace with your actual keyword

    # Create a speech recognizer using the microphone
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config)

    done = False

    def stop_cb(evt):
        """Callback that signals to stop recognition upon receiving an event `evt`"""
        logging.info(f"CLOSING on {evt}")
        nonlocal done
        done = True

    def recognizing_cb(evt):
        """Callback for recognizing event"""
        if evt.result.reason == speechsdk.ResultReason.RecognizingKeyword:
            logging.info(f"RECOGNIZING KEYWORD: {evt}")
        elif evt.result.reason == speechsdk.ResultReason.RecognizingSpeech:
            logging.info(f"RECOGNIZING SPEECH: {evt}")

    def recognized_cb(evt):
        """Callback for recognized event"""
        if evt.result.reason == speechsdk.ResultReason.RecognizedKeyword:
            logging.info(f"RECOGNIZED KEYWORD: {evt.result.text}")
            # Schedule the send_keyword_detected coroutine
            asyncio.run_coroutine_threadsafe(send_keyword_detected(), loop)
        elif evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
            logging.info(f"RECOGNIZED SPEECH: {evt.result.text}")
        elif evt.result.reason == speechsdk.ResultReason.NoMatch:
            logging.warning(f"NO MATCH: {evt}")
        nonlocal done
        done = True

    async def send_keyword_detected():
        """Asynchronously sends a keyword detected message via ConnectionManager."""
        try:
            await connection_manager.send_keyword("keyword_detected")
            logging.info("Keyword message sent successfully.")
        except Exception as e:
            logging.error(f"Failed to send keyword message: {e}")

    # Connect callbacks to events fired by the recognizer
    speech_recognizer.recognizing.connect(recognizing_cb)
    speech_recognizer.recognized.connect(recognized_cb)
    speech_recognizer.session_started.connect(lambda evt: logging.info(f"SESSION STARTED: {evt}"))
    speech_recognizer.session_stopped.connect(lambda evt: logging.info(f"SESSION STOPPED: {evt}"))
    speech_recognizer.canceled.connect(lambda evt: logging.warning(f"CANCELED: {evt}"))

    # Stop recognition on session stopped or canceled events
    speech_recognizer.session_stopped.connect(stop_cb)
    speech_recognizer.canceled.connect(stop_cb)

    # Start keyword recognition
    logging.info(f'Say something starting with "{keyword}" followed by whatever you want...')
    speech_recognizer.start_keyword_recognition(model)

    while not done:
        time.sleep(0.5)

    # Stop keyword recognition
    speech_recognizer.stop_keyword_recognition()
    logging.info("Keyword recognition stopped.")

if __name__ == "__main__":
    speech_recognize_keyword()
