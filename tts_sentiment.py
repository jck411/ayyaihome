# tts_sentiment.py
import os
from google.cloud import texttospeech
from azure.cognitiveservices.speech import SpeechConfig, SpeechSynthesizer, AudioConfig
import openai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up OpenAI
openai.api_key = os.getenv('OPENAI_API_KEY')

# Set up Google TTS
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
google_client = texttospeech.TextToSpeechClient()

# Set up Azure TTS
azure_speech_key = os.getenv("AZURE_SPEECH_KEY")
azure_service_region = os.getenv("AZURE_SPEECH_REGION")
azure_speech_config = SpeechConfig(subscription=azure_speech_key, region=azure_service_region)

def sentiment_analysis(transcription):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": "As an AI with expertise in language and emotion analysis, your task is to analyze the sentiment of the following text. Please consider the overall tone of the discussion, the emotion conveyed by the language used, and the context in which words and phrases are used. Indicate whether the sentiment is generally positive, negative, or neutral, and provide brief explanations for your analysis where possible."
            },
            {
                "role": "user",
                "content": transcription
            }
        ]
    )
    return response.choices[0].message.content

def google_tts(text, output_file):
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(language_code="en-US", ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL)
    audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
    response = google_client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)
    with open(output_file, "wb") as out:
        out.write(response.audio_content)

def azure_tts(text, output_file):
    audio_output = AudioConfig(filename=output_file)
    synthesizer = SpeechSynthesizer(speech_config=azure_speech_config, audio_config=audio_output)
    synthesizer.speak_text(text)

def process_text(text, use_sentiment_analysis=True, tts_provider="google"):
    sentences = text.split('.')
    for i, sentence in enumerate(sentences):
        if use_sentiment_analysis:
            sentiment = sentiment_analysis(sentence)
            print(f"Sentence: {sentence}\nSentiment: {sentiment}")
            # Choose appropriate TTS voice based on sentiment (to be implemented)
        output_file = f"output_sentence_{i}.mp3"
        if tts_provider == "google":
            google_tts(sentence, output_file)
        elif tts_provider == "azure":
            azure_tts(sentence, output_file)

if __name__ == "__main__":
    sample_text = "Hello, this is a test. This is another sentence."
    process_text(sample_text)
