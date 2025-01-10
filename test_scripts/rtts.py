import os
from dotenv import load_dotenv
from RealtimeTTS import TextToAudioStream, AzureEngine

# Load environment variables from the .env file
load_dotenv()

# Retrieve the Azure Speech subscription key and region from the .env file
subscription_key = os.getenv("AZURE_SPEECH_KEY")
service_region = os.getenv("AZURE_SPEECH_REGION")

if not subscription_key or not service_region:
    raise ValueError("AZURE_SPEECH_KEY and AZURE_SPEECH_REGION must be set in your .env file")

# Initialize the AzureEngine with the subscription key and region
engine = AzureEngine(
    speech_key=subscription_key,
    service_region=service_region,
    voice="en-US-AshleyNeural"  # You can change this to any supported voice
)

# Set up the TextToAudioStream with the AzureEngine
stream = TextToAudioStream(engine)

# Provide text for synthesis
stream.feed("Hello world! How are you today?")
stream.play_async()
