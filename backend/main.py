# backend/main.py

import os
import yaml
import logging
import logging.config
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pathlib import Path

from backend.endpoints import router  # Import the router from endpoints module

# Load environment variables from a .env file
load_dotenv()

# Define paths
BASE_DIR = Path(__file__).parent
CONFIG_PATH = BASE_DIR / "config.yaml"
LOGGING_CONFIG_PATH = BASE_DIR / "logging.yaml"

# Load configuration from YAML file
try:
    with open(CONFIG_PATH, 'r') as config_file:
        config_data = yaml.safe_load(config_file)
    # You can process config_data here if needed
except FileNotFoundError:
    raise FileNotFoundError(f"Configuration file not found at {CONFIG_PATH}")
except yaml.YAMLError as e:
    raise ValueError(f"Error parsing YAML configuration: {e}")

# Load logging configuration from logging.yaml
try:
    with open(LOGGING_CONFIG_PATH, 'r') as log_file:
        logging_config = yaml.safe_load(log_file.read())
    logging.config.dictConfig(logging_config)
except FileNotFoundError:
    raise FileNotFoundError(f"Logging configuration file not found at {LOGGING_CONFIG_PATH}")
except yaml.YAMLError as e:
    raise ValueError(f"Error parsing YAML logging configuration: {e}")

# Initialize the root logger
logger = logging.getLogger(__name__)
logger.info("Logging is configured.")

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

# Include the API router
app.include_router(router)

@app.get("/")
def read_root():
    logger.info("Root endpoint accessed.")
    return {"message": "Welcome to the TTS API!"}

if __name__ == '__main__':
    import uvicorn
    logger.info("Starting the FastAPI application.")
    uvicorn.run(app, host='0.0.0.0', port=8000)
