# /home/jack/ayyaihome/backend/services/azure_keyword_recognition.py

#!/usr/bin/env python
# coding: utf-8

import time
import azure.cognitiveservices.speech as speechsdk
import asyncio
import logging
import os
import threading

from init import connection_manager, loop  # Ensure 'init.py' is correctly set up
from dotenv import load_dotenv

# Load environment variables
load_dotenv("/home/jack/ayyaihome/backend/.env")

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Set up the subscription info for the Speech Service:
speech_key = os.getenv('AZURE_SPEECH_KEY')
service_region = os.getenv('AZURE_REGION')

def speech_recognize_keyword(keyword, model_path):
    """Performs keyword-triggered speech recognition for a specific keyword."""
    
    logging.info(f"Initializing recognizer for keyword: '{keyword}' with model: {model_path}")

    # Create the speech configuration
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)

    # Create the keyword recognition model
    keyword_model = speechsdk.KeywordRecognitionModel(model_path)

    # Create a speech recognizer using the microphone
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config)

    done = False

    def stop_cb(evt):
        """Callback that signals to stop recognition upon receiving an event `evt`."""
        nonlocal done
        logging.info(f"CLOSING on {evt}")
        done = True

    def recognized_cb(evt):
        """Callback for recognized event."""
        if evt.result.reason == speechsdk.ResultReason.RecognizedKeyword:
            logging.info(f"RECOGNIZED KEYWORD '{keyword}': {evt.result.text}")
            # Schedule the send_keyword_detected coroutine
            asyncio.run_coroutine_threadsafe(send_keyword_detected(keyword), loop)
        elif evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
            logging.info(f"RECOGNIZED SPEECH: {evt.result.text}")
        elif evt.result.reason == speechsdk.ResultReason.NoMatch:
            logging.warning(f"NO MATCH: {evt}")
        # Do not set done to True here to allow continuous recognition

    async def send_keyword_detected(keyword_detected):
        """Asynchronously sends a keyword detected message via ConnectionManager."""
        try:
            # Construct a dictionary with relevant information
            message = {
                "keyword": keyword_detected,
                "timestamp": int(time.time())  # Optional: Add a timestamp
            }
            await connection_manager.send_keyword(message)
            logging.info(f"Keyword '{keyword_detected}' message sent successfully.")
        except Exception as e:
            logging.error(f"Failed to send keyword '{keyword_detected}' message: {e}")

    # Connect callbacks to events fired by the recognizer
    speech_recognizer.recognized.connect(recognized_cb)
    speech_recognizer.session_started.connect(lambda evt: logging.info(f"SESSION STARTED for '{keyword}': {evt}"))
    speech_recognizer.session_stopped.connect(lambda evt: logging.info(f"SESSION STOPPED for '{keyword}': {evt}"))
    speech_recognizer.canceled.connect(lambda evt: logging.warning(f"CANCELED for '{keyword}': {evt}"))

    # Stop recognition on session stopped or canceled events
    speech_recognizer.session_stopped.connect(stop_cb)
    speech_recognizer.canceled.connect(stop_cb)

    # Start keyword recognition
    logging.info(f"Starting keyword recognition for '{keyword}'...")
    try:
        speech_recognizer.start_keyword_recognition(keyword_model)
    except Exception as e:
        logging.error(f"Failed to start keyword recognition for '{keyword}': {e}")
        return

    while not done:
        time.sleep(0.5)

    # Stop keyword recognition
    speech_recognizer.stop_keyword_recognition()
    logging.info(f"Keyword recognition stopped for '{keyword}'.")
