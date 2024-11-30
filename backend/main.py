
#/home/jack/ayyaihome/backend/main.py

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pyaudio
from dotenv import load_dotenv

from backend.config import Config
from backend.endpoints import router  # Import the router

# Step 1: Load environment variables from a .env file
load_dotenv()

# Step 2: Initialize PyAudio for audio playback
try:
    pyaudio_instance = pyaudio.PyAudio()
except Exception as e:
    raise Exception(f"Failed to initialize PyAudio: {e}")

# Step 3: Initialize the FastAPI app
app = FastAPI()

# Step 4: Add CORS middleware to allow requests from various origins
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")  # Use env variable directly
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in cors_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Step 5: Include the router for endpoints
app.include_router(router)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
