import os
import time
from dotenv import load_dotenv
from RealtimeTTS import TextToAudioStream, AzureEngine

# Load environment variables
load_dotenv()

# Retrieve Azure API key and region
azure_speech_key = os.getenv("AZURE_SPEECH_KEY")
azure_speech_region = os.getenv("AZURE_SPEECH_REGION")

# Initialize AzureEngine with the required parameters
engine = AzureEngine(speech_key=azure_speech_key, service_region=azure_speech_region)
stream = TextToAudioStream(engine)

# Feed text and play asynchronously
stream.feed("Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry's standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book. It has survived not only five centuries, but also the leap into electronic typesetting, remaining essentially unchanged. It was popularised in the 1960s with the release of Letraset sheets containing Lorem Ipsum passages, and more recently with desktop publishing software like Aldus PageMaker including versions of Lorem Ipsum.")
stream.play()

