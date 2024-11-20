# /home/jack/ayyaihome/backend/main.py

import logging
from backend.logging_config import setup_logging

# Step 1: Initialize logging before any other imports
setup_logging()

import os
import yaml
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pyaudio
from dotenv import load_dotenv

from backend.endpoints import router  # Import the router after logging is set up
from backend.config import get_openai_client  # Import configuration utilities

# Step 2: Load environment variables from a .env file
load_dotenv()

# Step 3: Load configuration from YAML file
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.yaml")

try:
    with open(CONFIG_PATH, 'r') as config_file:
        config_data = yaml.safe_load(config_file)
except FileNotFoundError:
    logger = logging.getLogger(__name__)
    logger.error(f"Configuration file not found at {CONFIG_PATH}")
    raise FileNotFoundError(f"Configuration file not found at {CONFIG_PATH}")
except yaml.YAMLError as e:
    logger = logging.getLogger(__name__)
    logger.error(f"Error parsing YAML configuration: {e}")
    raise ValueError(f"Error parsing YAML configuration: {e}")

# Step 4: Initialize PyAudio for audio playback
pyaudio_instance = pyaudio.PyAudio()

# Step 5: Initialize the FastAPI app
app = FastAPI()

# Step 6: Add CORS middleware to allow requests from various origins
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in cors_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Step 7: Include the router for endpoints
app.include_router(router)

# Step 8: Add a test log message to verify logging
logger = logging.getLogger(__name__)
logger.info("FastAPI application initialized successfully.")

if __name__ == '__main__':
    import uvicorn
    logger.info("Starting the Uvicorn server.")
    uvicorn.run(app, host='0.0.0.0', port=8000)