# /home/jack/ayyaihome/backend/main.py

import os
import yaml
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pyaudio
from dotenv import load_dotenv

from backend.endpoints import router  # Import the router from endpoints module
from backend.config import get_openai_client  # Import configuration utilities

# Load environment variables from a .env file
load_dotenv()

# Load configuration from YAML file
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.yaml")

try:
    with open(CONFIG_PATH, 'r') as config_file:
        config_data = yaml.safe_load(config_file)
except FileNotFoundError:
    raise FileNotFoundError(f"Configuration file not found at {CONFIG_PATH}")
except yaml.YAMLError as e:
    raise ValueError(f"Error parsing YAML configuration: {e}")

# Initialize PyAudio for audio playback
pyaudio_instance = pyaudio.PyAudio()

# Initialize the FastAPI app
app = FastAPI()

# Add CORS middleware to allow requests from various origins
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in cors_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the router for endpoints
app.include_router(router)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
