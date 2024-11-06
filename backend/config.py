import os
import logging
from dotenv import load_dotenv
from openai import AsyncOpenAI, OpenAI

# Load environment variables
load_dotenv()

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Retrieve API key from environment variables
openai_api_key = os.getenv("OPENAI_API_KEY")

# Initialize both OpenAI clients for synchronous and asynchronous usage
client = OpenAI(api_key=openai_api_key)        # Synchronous client
aclient = AsyncOpenAI(api_key=openai_api_key)  # Asynchronous client

# Define default model name to be used in requests
default_model = "gpt-4o-mini"  # Adjust this to your preferred model

# Export client, aclient, and default_model for use in other modules
__all__ = ["client", "aclient", "default_model"]
