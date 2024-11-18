# backend/config.py

import os
import yaml
import logging
from dotenv import load_dotenv
from openai import AsyncOpenAI
import azure.cognitiveservices.speech as speechsdk
from pathlib import Path

# Load environment variables from a .env file
load_dotenv()

# Load configuration from YAML file
CONFIG_PATH = Path(__file__).parent / "config.yaml"

try:
    with open(CONFIG_PATH, 'r') as config_file:
        config_data = yaml.safe_load(config_file)
except FileNotFoundError:
    raise FileNotFoundError(f"Configuration file not found at {CONFIG_PATH}")
except yaml.YAMLError as e:
    raise ValueError(f"Error parsing YAML configuration: {e}")

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration parameters
class Config:
    """
    Configuration class to hold all settings for TTS and LLM models.
    """

    # GENERAL_TTS
    GENERAL_TTS = config_data.get('GENERAL_TTS', {})
    TTS_PROVIDER = GENERAL_TTS.get('TTS_PROVIDER', "azure")  # Default to Azure
    TTS_CHUNK_SIZE = GENERAL_TTS.get('TTS_CHUNK_SIZE', 1024)
    DELIMITERS = GENERAL_TTS.get('DELIMITERS', [". ", "? ", "! "])
    MINIMUM_PHRASE_LENGTH = GENERAL_TTS.get('MINIMUM_PHRASE_LENGTH', 25)  # Default: 25

    # TTS_MODELS
    TTS_MODELS = config_data.get('TTS_MODELS', {})

    # TTS_MODELS - OpenAI
    OPENAI_TTS_CONFIG = TTS_MODELS.get('OPENAI_TTS', {})
    OPENAI_TTS_SPEED = OPENAI_TTS_CONFIG.get('TTS_SPEED', 1.0)
    OPENAI_TTS_VOICE = OPENAI_TTS_CONFIG.get('TTS_VOICE', "onyx")
    OPENAI_TTS_MODEL = OPENAI_TTS_CONFIG.get('TTS_MODEL', "tts-1")
    OPENAI_AUDIO_RESPONSE_FORMAT = OPENAI_TTS_CONFIG.get('AUDIO_RESPONSE_FORMAT', "pcm")
    OPENAI_PLAYBACK_RATE = OPENAI_TTS_CONFIG.get('PLAYBACK_RATE', 24000)

    # TTS_MODELS - Azure
    AZURE_TTS_CONFIG = TTS_MODELS['AZURE_TTS']  # No fallback, raises KeyError if missing
    AZURE_TTS_SPEED = AZURE_TTS_CONFIG['TTS_SPEED']  # Mandatory, no default
    AZURE_TTS_VOICE = AZURE_TTS_CONFIG['TTS_VOICE']  # Mandatory, no default
    AZURE_AUDIO_FORMAT = AZURE_TTS_CONFIG['AUDIO_FORMAT']  # Mandatory, no default
    AZURE_PLAYBACK_RATE = AZURE_TTS_CONFIG['PLAYBACK_RATE']  # Mandatory, no default

    # LLM_MODEL_CONFIG - OpenAI
    LLM_CONFIG = config_data.get('LLM_MODEL_CONFIG', {}).get('OPENAI', {})
    RESPONSE_MODEL = LLM_CONFIG.get('RESPONSE_MODEL', "gpt-4o-mini")
    TEMPERATURE = LLM_CONFIG.get('TEMPERATURE', 1.0)
    TOP_P = LLM_CONFIG.get('TOP_P', 1.0)
    N = LLM_CONFIG.get('N', 1)
    SYSTEM_PROMPT_CONTENT = LLM_CONFIG.get('SYSTEM_PROMPT_CONTENT', "You are a helpful but witty and dry assistant")
    STREAM_OPTIONS = LLM_CONFIG.get('STREAM_OPTIONS', {"include_usage": True})
    STOP = LLM_CONFIG.get('STOP', None)
    MAX_TOKENS = LLM_CONFIG.get('MAX_TOKENS', None)
    PRESENCE_PENALTY = LLM_CONFIG.get('PRESENCE_PENALTY', 0.0)
    FREQUENCY_PENALTY = LLM_CONFIG.get('FREQUENCY_PENALTY', 0.0)
    LOGIT_BIAS = LLM_CONFIG.get('LOGIT_BIAS', None)
    USER = LLM_CONFIG.get('USER', None)
    TOOLS = LLM_CONFIG.get('TOOLS', None)
    TOOL_CHOICE = LLM_CONFIG.get('TOOL_CHOICE', None)
    MODALITIES = LLM_CONFIG.get('MODALITIES', ["text"])

    # LLM_MODEL_CONFIG - Anthropic
    ANTHROPIC_CONFIG = config_data.get('LLM_MODEL_CONFIG', {}).get('ANTHROPIC', {})
    ANTHROPIC_RESPONSE_MODEL = ANTHROPIC_CONFIG.get('RESPONSE_MODEL', "claude-3-haiku-20240307")
    ANTHROPIC_TEMPERATURE = ANTHROPIC_CONFIG.get('TEMPERATURE', 0.7)
    ANTHROPIC_TOP_P = ANTHROPIC_CONFIG.get('TOP_P', 0.9)
    ANTHROPIC_SYSTEM_PROMPT = ANTHROPIC_CONFIG.get('SYSTEM_PROMPT', "you rhyme all of your replies")
    ANTHROPIC_MAX_TOKENS = ANTHROPIC_CONFIG.get('MAX_TOKENS', 1024)
    ANTHROPIC_STOP_SEQUENCES = ANTHROPIC_CONFIG.get('STOP_SEQUENCES', None)
    ANTHROPIC_STREAM_OPTIONS = ANTHROPIC_CONFIG.get('STREAM_OPTIONS', {"include_usage": True})

    # AUDIO_PLAYBACK_CONFIG
    AUDIO_PLAYBACK_CONFIG = config_data.get('AUDIO_PLAYBACK_CONFIG', {})
    AUDIO_FORMAT = AUDIO_PLAYBACK_CONFIG.get('FORMAT', 16)
    CHANNELS = AUDIO_PLAYBACK_CONFIG.get('CHANNELS', 1)
    DEFAULT_RATE = AUDIO_PLAYBACK_CONFIG.get('RATE', 24000)  # Default if no provider-specific rate

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
            return Config.AZURE_PLAYBACK_RATE
        else:
            raise ValueError(f"Unsupported TTS_PROVIDER: {Config.TTS_PROVIDER}")

# Initialize the OpenAI API client using dependency injection
def get_openai_client() -> AsyncOpenAI:
    api_key = Config.OPENAI_API_KEY
    if not api_key:
        logger.error("OpenAI API key is not set.")
        raise ValueError("OpenAI API key is not set.")
    return AsyncOpenAI(api_key=api_key)

# Initialize the Azure Speech SDK configuration
def get_azure_speech_config() -> speechsdk.SpeechConfig:
    subscription_key = Config.AZURE_SUBSCRIPTION_KEY
    region = Config.AZURE_REGION
    if not subscription_key or not region:
        logger.error("Azure Speech credentials are not set.")
        raise ValueError("Azure Speech credentials are not set.")
    speech_config = speechsdk.SpeechConfig(subscription=subscription_key, region=region)
    speech_config.speech_synthesis_voice_name = Config.AZURE_TTS_VOICE
    speech_config.speech_synthesis_rate = Config.AZURE_TTS_SPEED

    # Set output format
    try:
        speech_config.set_speech_synthesis_output_format(
            getattr(speechsdk.SpeechSynthesisOutputFormat, Config.AZURE_AUDIO_FORMAT)
        )
    except AttributeError:
        logger.error(f"Invalid OUTPUT_FORMAT: {Config.AZURE_AUDIO_FORMAT}")
        raise

    return speech_config
