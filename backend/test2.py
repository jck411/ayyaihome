import os
import azure.cognitiveservices.speech as speechsdk
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Azure credentials and endpoints
speech_key = os.getenv('AZURE_SPEECH_KEY')
speech_region = os.getenv('AZURE_SPEECH_REGION')
text_analytics_key = os.getenv("AZURE_TEXT_ANALYTICS_KEY")
text_analytics_endpoint = os.getenv("AZURE_TEXT_ANALYTICS_ENDPOINT")

# Initialize clients
speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=speech_region)
text_analytics_client = TextAnalyticsClient(endpoint=text_analytics_endpoint, credential=AzureKeyCredential(text_analytics_key))

# The story text (a longer story with different emotional segments)
story_text = [
    "Once upon a time, in a land far away, there was a prosperous kingdom where people lived in peace and harmony. The sun always shone brightly, and the fields were abundant with crops.",
    "But one day, a dark shadow fell over the land. A mysterious illness spread throughout the kingdom, causing fear and panic among the people.",
    "The once joyful streets were now empty, and the sound of laughter was replaced by the eerie silence of despair.",
    "In the midst of this chaos, a young princess named Elara refused to give up hope. She believed that there was still a way to save her people.",
    "With courage in her heart, Elara set out on a journey to find the legendary healer who was said to possess the cure for any illness.",
    "Her journey was fraught with danger. She faced wild beasts, treacherous mountains, and a fierce storm that nearly claimed her life.",
    "But Elara's determination was unshakable. She pressed on, driven by her love for her people and the hope of restoring her kingdom.",
    "Finally, after many trials, she found the healer, an old man living in a remote village. He listened to her plea and agreed to help, but there was a cost.",
    "The healer told Elara that to save her people, she must sacrifice something dear to her. Without hesitation, Elara agreed, knowing the lives of her people were worth any price.",
    "As the healer prepared the cure, Elara felt a deep sadness, but also a sense of resolve. She knew she had made the right choice.",
    "When Elara returned to her kingdom with the cure, the people rejoiced. The illness was eradicated, and life slowly returned to normal.",
    "But the kingdom had changed. The people had learned the value of unity and compassion through their trials. And Elara, though she had lost something precious, gained the love and respect of her people forever."
]

# Function to analyze sentiment
def analyze_sentiment(text):
    response = text_analytics_client.analyze_sentiment(documents=[text])[0]
    return response.sentiment

# Function to select TTS voice style based on sentiment
def select_voice_style(sentiment):
    if sentiment == "positive":
        return "cheerful"
    elif sentiment == "negative":
        return "sad"
    else:
        return "neutral"

# Process each sentence in the story
for sentence in story_text:
    sentiment = analyze_sentiment(sentence)
    style = select_voice_style(sentiment)
    
    # Create SSML with the selected style
    ssml = f"""
    <speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xmlns:mstts='http://www.w3.org/2001/mstts' xml:lang='en-US'>
        <voice name='en-US-NancyNeural'>
            <mstts:express-as style='{style}'>
                {sentence}
            </mstts:express-as>
        </voice>
    </speak>
    """

    # Synthesize the speech
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)
    result = synthesizer.speak_ssml_async(ssml).get()

    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        print(f"Successfully synthesized: {sentence}")
    else:
        print(f"Speech synthesis failed: {result.reason}")
