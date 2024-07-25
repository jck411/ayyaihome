import os
from dotenv import load_dotenv
import azure.cognitiveservices.speech as speechsdk
import asyncio
from typing import List, Tuple

load_dotenv()

async def text_to_speech(parsed_sentences: List[Tuple[str, str]], output_file: str):
    subscription_key = os.getenv('AZURE_SPEECH_KEY')
    region = os.getenv('AZURE_SPEECH_REGION')

    speech_config = speechsdk.SpeechConfig(subscription=subscription_key, region=region)
    speech_config.speech_synthesis_voice_name = "en-US-JennyNeural"
    audio_config = speechsdk.audio.AudioOutputConfig(filename=output_file)
    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

    ssml_string = generate_ssml(parsed_sentences)
    result = await asyncio.get_event_loop().run_in_executor(None, speech_synthesizer.speak_ssml_async(ssml_string).get)

    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        print(f"Speech synthesized and saved to [{output_file}]")
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = result.cancellation_details
        print(f"Speech synthesis canceled: {cancellation_details.reason}")
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            print(f"Error details: {cancellation_details.error_details}")

def generate_ssml(parsed_sentences):
    ssml = (
        '<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">'
        '<voice name="en-US-JennyNeural">'
    )

    for text, sentiment in parsed_sentences:
        ssml += f'<prosody rate="medium"><emphasis level="moderate">{text}</emphasis></prosody>'

    ssml += '</voice></speak>'
    return ssml
