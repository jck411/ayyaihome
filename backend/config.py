# backend/config.py

import os
import yaml
import logging
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# Define paths
BASE_DIR = Path(__file__).parent
CONFIG_PATH = BASE_DIR / "config.yaml"

logger = logging.getLogger(__name__)

# Load configuration from YAML file
try:
    with open(CONFIG_PATH, 'r') as config_file:
        config_data = yaml.safe_load(config_file)
        logger.info(f"Configuration loaded from {CONFIG_PATH}.")
except FileNotFoundError:
    logger.error(f"Configuration file not found at {CONFIG_PATH}.")
    raise
except yaml.YAMLError as e:
    logger.error(f"Error parsing YAML configuration: {e}")
    raise

# Define a mapping for audio format to playback rate
AUDIO_FORMAT_PLAYBACK_RATE_MAP = {
    "Raw8Khz16BitMonoPcm": 8000,
    "Raw16Khz16BitMonoPcm": 16000,
    "Raw24Khz16BitMonoPcm": 24000,
    "Raw44100Hz16BitMonoPcm": 44100,
    "Raw48Khz16BitMonoPcm": 48000,
}

class Config:
    """
    Configuration class to hold all settings for TTS and LLM models.
    """

    # GENERAL_TTS
    GENERAL_TTS = config_data.get('GENERAL_TTS', {})
    TTS_PROVIDER = GENERAL_TTS.get('TTS_PROVIDER', "azure")  # Default to Azure
    USE_SSML_MODULE = GENERAL_TTS.get('USE_SSML_MODULE', False)
    USE_TEXT_SPLITTING = GENERAL_TTS.get('USE_TEXT_SPLITTING', False)
    TOKENIZER = GENERAL_TTS.get('TOKENIZER', None)
    DELIMITERS = GENERAL_TTS.get('DELIMITERS', {})  # Ensure it's a dict

    # STANZA_CONFIG (relevant if TOKENIZER="stanza")
    STANZA_CONFIG = GENERAL_TTS.get('STANZA_CONFIG', {})
    STANZA_LANGUAGE = STANZA_CONFIG.get('language', "en")
    STANZA_PROCESSORS = STANZA_CONFIG.get('processors', "tokenize")
    STANZA_USE_GPU = STANZA_CONFIG.get('use_gpu', False)

    # TTS_MODELS
    TTS_MODELS = config_data.get('TTS_MODELS', {})

    # TTS_MODELS - OpenAI
    OPENAI_TTS = TTS_MODELS.get('OPENAI_TTS', {})
    OPENAI_TTS_SPEED = OPENAI_TTS.get('TTS_SPEED', 1.0)
    OPENAI_TTS_VOICE = OPENAI_TTS.get('TTS_VOICE', "onyx")
    OPENAI_TTS_MODEL = OPENAI_TTS.get('TTS_MODEL', "tts-1")
    OPENAI_AUDIO_RESPONSE_FORMAT = OPENAI_TTS.get('AUDIO_RESPONSE_FORMAT', "pcm")
    OPENAI_PLAYBACK_RATE = OPENAI_TTS.get('PLAYBACK_RATE', 24000)

    # TTS_MODELS - Azure
    AZURE_TTS = TTS_MODELS.get('AZURE_TTS', {})
    AZURE_TTS_VOICE = AZURE_TTS.get('TTS_VOICE', "en-US-Brian:DragonHDLatestNeural")
    AZURE_AUDIO_FORMAT = AZURE_TTS.get('AUDIO_FORMAT', "Raw24Khz16BitMonoPcm")
    AZURE_SPEECH_SYNTHESIS_RATE = AZURE_TTS.get('SPEECH_SYNTHESIS_RATE', "0%")
    AZURE_STABILITY = AZURE_TTS.get('STABILITY', 1.0)
    AZURE_USE_AZURE_SSML = AZURE_TTS.get('USE_AZURE_SSML', False)

    # Prosody settings
    AZURE_PROSODY = AZURE_TTS.get('PROSODY', {})
    AZURE_PROSODY_RATE = AZURE_PROSODY.get('rate', "0%")
    AZURE_PROSODY_PITCH = AZURE_PROSODY.get('pitch', "0%")
    AZURE_PROSODY_VOLUME = AZURE_PROSODY.get('volume', "default")

    # LLM_MODEL_CONFIG
    LLM_MODEL_CONFIG = config_data.get('LLM_MODEL_CONFIG', {})
    OPENAI_LLM = LLM_MODEL_CONFIG.get('OPENAI', {})
    ANTHROPIC_LLM = LLM_MODEL_CONFIG.get('ANTHROPIC', {})

    # AUDIO_PLAYBACK_CONFIG
    AUDIO_PLAYBACK_CONFIG = config_data.get('AUDIO_PLAYBACK_CONFIG', {})
    AUDIO_FORMAT = AUDIO_PLAYBACK_CONFIG.get('FORMAT', 16)
    AUDIO_CHANNELS = AUDIO_PLAYBACK_CONFIG.get('CHANNELS', 1)
    AUDIO_RATE = AUDIO_PLAYBACK_CONFIG.get('RATE', None)

    # Azure Credentials from .env
    AZURE_SUBSCRIPTION_KEY = os.getenv("AZURE_SUBSCRIPTION_KEY")
    AZURE_REGION = os.getenv("AZURE_REGION")

    # OpenAI Credentials from .env or config.yaml
    OPENAI_API_KEY = config_data.get('OPENAI_API_KEY') or os.getenv("OPENAI_API_KEY")

    @staticmethod
    def get_playback_rate():
        if Config.TTS_PROVIDER.lower() == "openai":
            return Config.OPENAI_PLAYBACK_RATE
        elif Config.TTS_PROVIDER.lower() == "azure":
            return AUDIO_FORMAT_PLAYBACK_RATE_MAP.get(Config.AZURE_AUDIO_FORMAT, 24000)
        else:
            raise ValueError(f"Unsupported TTS_PROVIDER: {Config.TTS_PROVIDER}")

def get_openai_client():
    """
    Returns an instance of AsyncOpenAI for interacting with OpenAI APIs.
    """
    from openai import AsyncOpenAI  # Import here to avoid circular imports
    api_key = Config.OPENAI_API_KEY
    if not api_key:
        logger.error("OpenAI API key is not set.")
        raise ValueError("OpenAI API key is not set.")
    logger.info("OpenAI client initialized.")
    return AsyncOpenAI(api_key=api_key)

def get_azure_speech_config():
    """
    Returns Azure SpeechConfig and playback rate.
    """
    from azure.cognitiveservices.speech import SpeechConfig, SpeechSynthesisOutputFormat

    subscription_key = Config.AZURE_SUBSCRIPTION_KEY
    region = Config.AZURE_REGION
    if not subscription_key or not region:
        logger.error("Azure Speech credentials are not set.")
        raise ValueError("Azure Speech credentials are not set.")

    # Validate and map AUDIO_FORMAT to PLAYBACK_RATE
    audio_format = Config.AZURE_AUDIO_FORMAT
    playback_rate = AUDIO_FORMAT_PLAYBACK_RATE_MAP.get(audio_format)
    if playback_rate is None:
        logger.error(f"Invalid AUDIO_FORMAT: {audio_format}. Please update the YAML.")
        raise ValueError(f"Unsupported AUDIO_FORMAT: {audio_format}")

    speech_config = SpeechConfig(subscription=subscription_key, region=region)
    speech_config.speech_synthesis_voice_name = Config.AZURE_TTS_VOICE
    speech_config.speech_synthesis_rate = Config.AZURE_SPEECH_SYNTHESIS_RATE

    # Set output format
    try:
        speech_config.set_speech_synthesis_output_format(
            getattr(SpeechSynthesisOutputFormat, audio_format)
        )
    except AttributeError:
        logger.error(f"Invalid OUTPUT_FORMAT: {audio_format}")
        raise ValueError(f"Invalid OUTPUT_FORMAT: {audio_format}")

    logger.info(f"Azure Speech Configured with format: {audio_format}, playback rate: {playback_rate} Hz.")
    return speech_config, playback_rate
