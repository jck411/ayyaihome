# main.py

import os
import logging

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import Config
from services.ai_services import OpenAIService
from services.tts_services import TTSService
from audio_players import PyAudioPlayer
from stream_manager import StreamManager
from lifecycle import AppLifecycle
from api import API
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app() -> FastAPI:
    config = Config()
    app = FastAPI()

    # Initialize services based on configuration
    # AI Service
    ai_service_class = config.get_ai_service_class()
    if config.AI_SERVICE.lower() == 'openai':
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            logger.error("OPENAI_API_KEY is not set in environment variables.")
            raise EnvironmentError("OPENAI_API_KEY is required.")
        ai_service = ai_service_class(api_key=openai_api_key, config=config)
    else:
        raise ValueError(f"Unsupported AI_SERVICE: {config.AI_SERVICE}")

    # TTS Service
    tts_service_class = config.get_tts_service_class()
    if config.TTS_SERVICE.lower() == 'openai':
        tts_service = tts_service_class(client=ai_service, config=config)
    else:
        raise ValueError(f"Unsupported TTS_SERVICE: {config.TTS_SERVICE}")

    # Audio Player
    audio_player_class = config.get_audio_player_class()
    if config.AUDIO_PLAYER.lower() == 'pyaudio':
        audio_player = audio_player_class(config=config)
    else:
        raise ValueError(f"Unsupported AUDIO_PLAYER: {config.AUDIO_PLAYER}")

    # Initialize Stream Manager
    stream_manager = StreamManager()

    # Initialize Application Lifecycle Manager
    lifecycle = AppLifecycle(stream_manager=stream_manager, audio_player=audio_player)

    # Initialize API Routes
    api = API(app, ai_service, tts_service, audio_player, stream_manager, config)

    # Add Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],  # Update this as needed
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Setup lifespan
    app.router.lifespan = lifecycle.lifespan

    return app

# Initialize the app
app = create_app()

# Run the application
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
