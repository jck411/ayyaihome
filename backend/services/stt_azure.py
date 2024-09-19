# backend/services/stt_azure.py

import os
from dotenv import load_dotenv
import azure.cognitiveservices.speech as speechsdk
import asyncio
import logging

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

class AzureSpeechRecognizer:
    def __init__(self, on_transcription_callback):
        self.speech_config = self.get_speech_config()
        self.push_stream = speechsdk.audio.PushAudioInputStream()
        self.audio_config = speechsdk.audio.AudioConfig(stream=self.push_stream)

        # Use ConversationTranscriber for diarization
        self.conversation_transcriber = speechsdk.transcription.ConversationTranscriber(
            speech_config=self.speech_config, audio_config=self.audio_config
        )
        self.current_speaker = "Unknown"
        self.on_transcription_callback = on_transcription_callback

        # Connect event handlers
        self.conversation_transcriber.transcribing.connect(self.transcribing_handler)
        self.conversation_transcriber.transcribed.connect(self.transcribed_handler)
        self.conversation_transcriber.canceled.connect(self.canceled_handler)
        self.conversation_transcriber.session_stopped.connect(self.session_stopped_handler)

    def get_speech_config(self):
        speech_key = os.getenv('SPEECH_KEY')
        service_region = os.getenv('SPEECH_REGION')

        if not speech_key or not service_region:
            raise ValueError("SPEECH_KEY and SPEECH_REGION must be set as environment variables.")

        speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
        speech_config.speech_recognition_language = "en-US"
        speech_config.request_word_level_timestamps()

        return speech_config

    def transcribing_handler(self, evt):
        if evt.result.reason == speechsdk.ResultReason.TranscribingSpeech and len(evt.result.text) > 0:
            transcription_data = {
                "type": "recognizing",
                "text": evt.result.text,
                "offset": evt.result.offset,
                "duration": evt.result.duration,
                "speaker": self.current_speaker
            }
            logger.debug(f"Transcribing: {transcription_data}")
            asyncio.create_task(self.on_transcription_callback(transcription_data))

    def transcribed_handler(self, evt):
        if evt.result.reason == speechsdk.ResultReason.TranscribedSpeech:
            # Assume speaker_id is available; adjust as per your actual event data
            speaker_id = evt.result.properties.get(speechsdk.PropertyId.SpeechServiceConnection_SpeakerId, "Unknown")
            speaker = self.get_speaker_name(speaker_id)
            transcription_data = {
                "type": "recognized",
                "text": evt.result.text,
                "offset": evt.result.offset,
                "duration": evt.result.duration,
                "speaker": speaker
            }
            logger.debug(f"Transcribed: {transcription_data}")
            asyncio.create_task(self.on_transcription_callback(transcription_data))

    def canceled_handler(self, evt):
        logger.error(f"CANCELED: Reason={evt.reason}, ErrorDetails={evt.error_details}")

    def session_stopped_handler(self, evt):
        logger.info("Session stopped.")
        asyncio.create_task(self.on_transcription_callback({"type": "session_stopped"}))
        self.conversation_transcriber.stop_transcribing()

    def get_speaker_name(self, speaker_id):
        # Implement your speaker mapping logic here
        speaker_mapping = {
            "0": "Jack",
            "1": "Sanja"
        }
        return speaker_mapping.get(speaker_id, "Unknown")

    async def start_recognition(self):
        logger.info("Starting continuous transcription...")
        await self.conversation_transcriber.start_transcribing_async()

    def stop_recognition(self):
        logger.info("Stopping transcription...")
        self.conversation_transcriber.stop_transcribing()

    def push_audio(self, audio_data: bytes):
        self.push_stream.write(audio_data)
