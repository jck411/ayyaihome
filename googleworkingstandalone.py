import os
import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv
import asyncio
from fastapi import HTTPException
import google.generativeai as genai
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
AZURE_SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")
AZURE_SERVICE_REGION = os.getenv("AZURE_SERVICE_REGION")

# Function to perform TTS using Azure Speech SDK
def text_to_speech(text):
    try:
        logger.debug("Initializing Azure Speech Config...")
        speech_config = speechsdk.SpeechConfig(subscription=AZURE_SPEECH_KEY, region=AZURE_SERVICE_REGION)
        audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)

        # Initialize synthesizer with config and audio output
        synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

        logger.info(f"Performing TTS for text: {text}")
        # Perform synthesis
        result = synthesizer.speak_text_async(text).get()
        
        # Check if synthesis was successful
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            logger.info(f"TTS synthesis completed successfully for text: {text}")
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            logger.error(f"TTS synthesis was canceled: {cancellation_details.reason}. Details: {cancellation_details.error_details}")

    except Exception as e:
        logger.error(f"Exception occurred in TTS: {e}")

# Function for streaming responses from Google's Gemini API and performing Azure TTS
async def stream_google_completion(
    messages: list[dict],
    phrase_queue: asyncio.Queue
):
    """
    Streams completion from Google's Gemini API and processes the text.

    Args:
        messages (list[dict]): List of message dictionaries with role and content keys.
        phrase_queue (asyncio.Queue): Queue to handle processed phrases.
    """
    try:
        logger.debug("Starting stream_google_completion...")
        # Configure the SDK with your API key
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="GEMINI_API_KEY is not set.")
        
        genai.configure(api_key=api_key)

        # Initialize the model
        model = genai.GenerativeModel("gemini-1.5-flash")

        # Construct the system prompt and user input
        system_prompt = "You are a helpful assistant who writes creative and engaging responses."
        user_inputs = "\n".join(msg["content"] for msg in messages)
        complete_prompt = f"{system_prompt}\n\n{user_inputs}"

        # Generate content asynchronously with the system prompt
        response = await model.generate_content_async(complete_prompt, stream=True)

        # Create an asyncio Queue for TTS phrases
        tts_queue = asyncio.Queue()

        # Variable to keep track if TTS has been started
        tts_started = False

        # Stream the response and accumulate content until a full sentence is formed
        working_string = ""
        async for chunk in response:
            content = chunk.text or ""
            if content:
                logger.debug(f"Received chunk: {content}")
                working_string += content

                # Yield content to the client immediately
                yield content

                # Check if the working string contains at least one complete sentence
                while any(punct in working_string for punct in [".", "!", "?"]):
                    # Find the first occurrence of the punctuation to determine the complete sentence
                    for punct in [".", "!", "?"]:
                        if punct in working_string:
                            split_index = working_string.index(punct) + 1
                            complete_sentence = working_string[:split_index].strip()

                            # Put the complete sentence into the TTS queue for processing
                            logger.info(f"Complete sentence ready for TTS: {complete_sentence}")
                            await tts_queue.put(complete_sentence)

                            # Start the TTS processing task after the first sentence is ready
                            if not tts_started:
                                logger.debug("Starting TTS processing task...")
                                asyncio.create_task(process_tts_queue(tts_queue))
                                tts_started = True

                            # Put the complete sentence in the phrase queue
                            await phrase_queue.put(complete_sentence)
                            logger.debug(f"Put complete sentence into phrase_queue: {complete_sentence}")

                            # Remove the processed sentence from the working string
                            working_string = working_string[split_index:].strip()
                            break

        # If there's any remaining content that doesn't end in punctuation, process it as well
        if working_string:
            logger.info(f"Remaining content ready for TTS: {working_string}")
            await tts_queue.put(working_string)

        # Signal the end of processing
        await tts_queue.put(None)
        await phrase_queue.put(None)
        logger.debug("Stream processing completed, put None into phrase_queue.")

    except Exception as e:
        await phrase_queue.put(None)
        logger.error(f"Exception occurred in stream_google_completion: {e}")
        raise HTTPException(status_code=500, detail=f"Error calling Google's Gemini API: {e}")

# Background task to process the TTS queue sequentially
async def process_tts_queue(tts_queue: asyncio.Queue):
    while True:
        text = await tts_queue.get()
        if text is None:
            logger.debug("TTS queue received termination signal. Exiting TTS processing.")
            break
        logger.info(f"Processing TTS for text from queue: {text}")
        await asyncio.get_running_loop().run_in_executor(None, text_to_speech, text)
        tts_queue.task_done()
