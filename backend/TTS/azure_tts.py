# backend/TTS/azure_tts.py

import asyncio
import queue
import logging
import azure.cognitiveservices.speech as speechsdk
from backend.config import Config, get_azure_speech_config
from backend.text_generation.phrase_preparation.SSML_addition import create_ssml
from backend.text_generation.phrase_preparation.text_splitting import process_text
from backend.text_generation.phrase_preparation.text_tokenization import tokenize_and_queue

logger = logging.getLogger(__name__)

class PushAudioOutputStreamCallback(speechsdk.audio.PushAudioOutputStreamCallback):
    """
    A callback mechanism to handle real-time audio streaming.
    Audio data is pushed to the provided audio queue.
    """

    def __init__(self, audio_queue: queue.Queue):
        super().__init__()
        self.audio_queue = audio_queue

    def write(self, data: memoryview) -> int:
        """
        Called by Azure Speech SDK when audio data is available.
        Pushes the audio data to the queue.
        """
        self.audio_queue.put(data.tobytes())
        return len(data)

    def close(self):
        """
        Called when the audio stream is closed.
        """
        self.audio_queue.put(None)
        logger.info("Audio stream closed.")

async def azure_text_to_speech_processor(phrase_queue: asyncio.Queue, audio_queue: queue.Queue):
    """
    Processes phrases from 'phrase_queue' and converts them to speech using Azure TTS.

    Args:
        phrase_queue (asyncio.Queue): Queue containing phrases to process.
        audio_queue (queue.Queue): Queue to send audio data.
    """
    try:
        # Load Azure speech configuration and playback rate
        speech_config, playback_rate = get_azure_speech_config()

        # Load general configuration
        general_tts_config = Config.GENERAL_TTS
        azure_config = Config.TTS_MODELS.get("AZURE_TTS", {})

        use_ssml_module = general_tts_config.get("USE_SSML_MODULE", False)
        use_azure_ssml = azure_config.get("USE_AZURE_SSML", False)
        use_tokenizer = general_tts_config.get("USE_TOKENIZER", False)
        use_text_splitting = general_tts_config.get("USE_TEXT_SPLITTING", False)
        tokenizer = general_tts_config.get("TOKENIZER", None)

        while True:
            raw_text = await phrase_queue.get()
            if raw_text is None:
                audio_queue.put(None)  # Signal end of processing
                logger.info("TTS processing complete.")
                return

            # Initialize a local queue for phrase processing
            local_phrase_queue = asyncio.Queue()

            # Step 1: Perform text splitting if enabled
            if use_text_splitting:
                await process_text(raw_text, local_phrase_queue, general_tts_config)
            else:
                await local_phrase_queue.put(raw_text)
                await local_phrase_queue.put(None)  # Signal end of queue

            # Step 2: Perform tokenization if enabled
            if use_tokenizer and tokenizer and tokenizer.lower() != "none":
                tokenized_queue = asyncio.Queue()
                while True:
                    phrase = await local_phrase_queue.get()
                    if phrase is None:
                        await tokenized_queue.put(None)
                        break
                    await tokenize_and_queue(phrase, tokenized_queue, tokenizer)
                local_phrase_queue = tokenized_queue
            else:
                # If tokenization is not used, continue with local_phrase_queue
                tokenized_queue = local_phrase_queue

            # Step 3: Convert each phrase to speech
            while True:
                phrase = await tokenized_queue.get()
                if phrase is None:
                    break  # Move to the next raw_text from phrase_queue

                try:
                    # Prepare SSML or plain text
                    if use_ssml_module:
                        voice_name = azure_config.get("TTS_VOICE", "en-US-Brian:DragonHDLatestNeural")
                        prosody = azure_config.get("PROSODY", {})
                        rate = prosody.get("rate", "0%")
                        pitch = prosody.get("pitch", "0%")
                        volume = prosody.get("volume", "default")
                        stability = azure_config.get("STABILITY", 1.0)

                        ssml_phrase = create_ssml(
                            phrase=phrase,
                            voice_name=voice_name,
                            rate=rate,
                            pitch=pitch,
                            volume=volume,
                            stability=stability,
                        )
                        use_ssml = True
                    elif use_azure_ssml:
                        ssml_phrase = f"<speak>{phrase}</speak>"
                        use_ssml = True
                    else:
                        ssml_phrase = phrase
                        use_ssml = False

                    # Set up push audio output stream with the callback
                    push_stream_callback = PushAudioOutputStreamCallback(audio_queue)
                    push_stream = speechsdk.audio.PushAudioOutputStream(push_stream_callback)
                    audio_config = speechsdk.audio.AudioOutputConfig(stream=push_stream)
                    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

                    # Synthesize speech
                    logger.info(f"Processing phrase: {phrase}")
                    
                    if use_ssml:
                        result = synthesizer.speak_ssml_async(ssml_phrase).get()
                    else:
                        result = synthesizer.speak_text_async(ssml_phrase).get()

                    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                        logger.info("TTS synthesis completed successfully.")
                    elif result.reason == speechsdk.ResultReason.Canceled:
                        details = result.cancellation_details
                        logger.error(f"TTS canceled: {details.reason} - {details.error_details}")
                    else:
                        logger.error("Unknown TTS error occurred.")
                except Exception as e:
                    logger.error(f"Error processing phrase '{phrase}': {e}")
    except Exception as e:
        logger.error(f"Error in TTS processing: {e}")
        audio_queue.put(None)
