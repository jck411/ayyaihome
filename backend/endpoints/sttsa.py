import os
import time
from dotenv import load_dotenv
import azure.cognitiveservices.speech as speechsdk

# Load environment variables from .env file
load_dotenv()

# Predefined speaker mapping (you can modify this)
speaker_mapping = {
    "0": "Jack",   # Assume first speaker is Jack
    "1": "Sanja"   # Assume second speaker is Sanja
}
current_speaker = "Unknown"  # Default for unrecognized speakers

def recognize_continuous_from_microphone():
    # Load subscription key and region from environment variables
    speech_config = speechsdk.SpeechConfig(
        subscription=os.getenv('SPEECH_KEY'), 
        region=os.getenv('SPEECH_REGION')
    )

    # Set language to English (en-US)
    speech_config.speech_recognition_language = "en-US"

    # Request word-level timestamps
    speech_config.request_word_level_timestamps()

    # Initialize microphone input
    audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

    # Status flag for recognition
    done = False

    # Error and session handling functions
    def stop_cb(evt):
        print(f'CLOSING on {evt}')
        speech_recognizer.stop_continuous_recognition()
        nonlocal done
        done = True

    # Recognizing handler to capture intermediate results
    def recognizing_handler(evt: speechsdk.SpeechRecognitionEventArgs):
        if evt.result.reason == speechsdk.ResultReason.RecognizingSpeech and len(evt.result.text) > 0:
            print(f"RECOGNIZING: {evt.result.text}")
            print(f"Offset in Ticks: {evt.result.offset}")
            print(f"Duration in Ticks: {evt.result.duration}")
            print(f"Speaker: {current_speaker}")  # Output the current speaker

    # Recognized handler for final transcriptions and timing
    def recognized_handler(evt: speechsdk.SpeechRecognitionEventArgs):
        global current_speaker  # Update speaker globally
        if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
            # Update speaker logic (this can be expanded based on logic to identify speakers)
            current_speaker = speaker_mapping.get(evt.result.speaker_id, "Unknown")
            print(f"RECOGNIZED: {evt.result.text}")
            print(f"Offset in Ticks: {evt.result.offset}")
            print(f"Duration in Ticks: {evt.result.duration}")
            print(f"Speaker: {current_speaker}")

    # Event handler functions for recognizing and recognized results
    speech_recognizer.recognizing.connect(recognizing_handler)
    speech_recognizer.recognized.connect(recognized_handler)

    # Session management events
    speech_recognizer.session_started.connect(lambda evt: print(f'SESSION STARTED: {evt}'))
    speech_recognizer.session_stopped.connect(lambda evt: print(f'SESSION STOPPED: {evt}'))

    # Error handling on cancellation
    speech_recognizer.canceled.connect(lambda evt: print(f'CANCELED: {evt.reason}, ErrorDetails: {evt.error_details}'))

    # Stop recognition on session end or cancelation
    speech_recognizer.session_stopped.connect(stop_cb)
    speech_recognizer.canceled.connect(stop_cb)

    # Start continuous recognition
    print("Starting continuous recognition with speaker mapping...")
    speech_recognizer.start_continuous_recognition()

    # Loop to keep recognition alive
    try:
        while not done:
            time.sleep(0.5)
    except KeyboardInterrupt:
        # Gracefully stop if interrupted
        print("Stopping recognition...")
        speech_recognizer.stop_continuous_recognition()

    print("Recognition stopped.")

if __name__ == "__main__":
    recognize_continuous_from_microphone()