import os
import yaml
from dotenv import load_dotenv
from openai import AsyncOpenAI
import azure.cognitiveservices.speech as speechsdk
from pathlib import Path
from typing import Any, Dict, List, Optional

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

# Configuration parameters
class Config:
    """
    Configuration class to hold all settings for TTS and LLM models.
    """

    # GENERAL_TTS
    GENERAL_TTS: Dict[str, Any] = config_data.get('GENERAL_TTS', {})
    TTS_PROVIDER: str = GENERAL_TTS.get('TTS_PROVIDER', "azure")
    DELIMITERS: List[str] = GENERAL_TTS.get('DELIMITERS', [". ", "? ", "! "])
    MINIMUM_PHRASE_LENGTH: int = GENERAL_TTS.get('MINIMUM_PHRASE_LENGTH', 25)

    # TTS_MODELS
    TTS_MODELS: Dict[str, Any] = config_data.get('TTS_MODELS', {})

    # TTS_MODELS - OpenAI
    OPENAI_TTS_CONFIG: Dict[str, Any] = TTS_MODELS.get('OPENAI_TTS', {})
    OPENAI_TTS_SPEED: float = OPENAI_TTS_CONFIG.get('TTS_SPEED', 1.0)
    OPENAI_TTS_VOICE: str = OPENAI_TTS_CONFIG.get('TTS_VOICE', "onyx")
    OPENAI_TTS_MODEL: str = OPENAI_TTS_CONFIG.get('TTS_MODEL', "tts-1")
    OPENAI_AUDIO_RESPONSE_FORMAT: str = OPENAI_TTS_CONFIG.get('AUDIO_RESPONSE_FORMAT', "pcm")
    OPENAI_PLAYBACK_RATE: int = OPENAI_TTS_CONFIG.get('PLAYBACK_RATE', 24000)
    OPENAI_TTS_CHUNK_SIZE: int = OPENAI_TTS_CONFIG.get('TTS_CHUNK_SIZE', 1024)

    # TTS_MODELS - Azure
    AZURE_TTS_CONFIG: Dict[str, Any] = TTS_MODELS.get('AZURE_TTS', {})
    AZURE_TTS_SPEED: str = AZURE_TTS_CONFIG['TTS_SPEED']  # Mandatory
    AZURE_TTS_VOICE: str = AZURE_TTS_CONFIG['TTS_VOICE']  # Mandatory
    AZURE_AUDIO_FORMAT: str = AZURE_TTS_CONFIG['AUDIO_FORMAT']  # Mandatory
    AZURE_PLAYBACK_RATE: int = AZURE_TTS_CONFIG['PLAYBACK_RATE']  # Mandatory

    # LLM_MODEL_CONFIG - OpenAI
    LLM_CONFIG: Dict[str, Any] = config_data.get('LLM_MODEL_CONFIG', {}).get('OPENAI', {})
    RESPONSE_MODEL: str = LLM_CONFIG.get('RESPONSE_MODEL', "gpt-4o-mini")
    TEMPERATURE: float = LLM_CONFIG.get('TEMPERATURE', 1.0)
    TOP_P: float = LLM_CONFIG.get('TOP_P', 1.0)
    N: int = LLM_CONFIG.get('N', 1)
    SYSTEM_PROMPT_CONTENT: str = LLM_CONFIG.get('SYSTEM_PROMPT_CONTENT', "You are a helpful but witty and dry assistant")
    STREAM_OPTIONS: Dict[str, Any] = LLM_CONFIG.get('STREAM_OPTIONS', {"include_usage": True})
    STOP: Optional[Any] = LLM_CONFIG.get('STOP', None)
    MAX_TOKENS: Optional[int] = LLM_CONFIG.get('MAX_TOKENS', None)
    PRESENCE_PENALTY: float = LLM_CONFIG.get('PRESENCE_PENALTY', 0.0)
    FREQUENCY_PENALTY: float = LLM_CONFIG.get('FREQUENCY_PENALTY', 0.0)
    LOGIT_BIAS: Optional[Any] = LLM_CONFIG.get('LOGIT_BIAS', None)
    USER: Optional[Any] = LLM_CONFIG.get('USER', None)
    TOOLS: Optional[Any] = LLM_CONFIG.get('TOOLS', None)
    TOOL_CHOICE: Optional[Any] = LLM_CONFIG.get('TOOL_CHOICE', None)
    MODALITIES: List[str] = LLM_CONFIG.get('MODALITIES', ["text"])

    # LLM_MODEL_CONFIG - Anthropic
    ANTHROPIC_CONFIG: Dict[str, Any] = config_data.get('LLM_MODEL_CONFIG', {}).get('ANTHROPIC', {})
    ANTHROPIC_RESPONSE_MODEL: str = ANTHROPIC_CONFIG.get('RESPONSE_MODEL', "claude-3-haiku-20240307")
    ANTHROPIC_TEMPERATURE: float = ANTHROPIC_CONFIG.get('TEMPERATURE', 0.7)
    ANTHROPIC_TOP_P: float = ANTHROPIC_CONFIG.get('TOP_P', 0.9)
    ANTHROPIC_SYSTEM_PROMPT: str = ANTHROPIC_CONFIG.get('SYSTEM_PROMPT', "you rhyme all of your replies")
    ANTHROPIC_MAX_TOKENS: int = ANTHROPIC_CONFIG.get('MAX_TOKENS', 1024)
    ANTHROPIC_STOP_SEQUENCES: Optional[Any] = ANTHROPIC_CONFIG.get('STOP_SEQUENCES', None)
    ANTHROPIC_STREAM_OPTIONS: Dict[str, Any] = ANTHROPIC_CONFIG.get('STREAM_OPTIONS', {"include_usage": True})

    # AUDIO_PLAYBACK_CONFIG
    AUDIO_PLAYBACK_CONFIG: Dict[str, Any] = config_data.get('AUDIO_PLAYBACK_CONFIG', {})
    AUDIO_FORMAT: int = AUDIO_PLAYBACK_CONFIG.get('FORMAT', 16)
    CHANNELS: int = AUDIO_PLAYBACK_CONFIG.get('CHANNELS', 1)
    DEFAULT_RATE: Optional[int] = AUDIO_PLAYBACK_CONFIG.get('RATE', 24000)  # Default if no provider-specific rate

    # Azure Credentials from .env
    AZURE_SUBSCRIPTION_KEY: Optional[str] = os.getenv("AZURE_SUBSCRIPTION_KEY")
    AZURE_REGION: Optional[str] = os.getenv("AZURE_REGION")

    # OpenAI Credentials from .env or config.yaml
    OPENAI_API_KEY: Optional[str] = config_data.get('OPENAI_API_KEY') or os.getenv("OPENAI_API_KEY")

    @staticmethod
    def get_playback_rate() -> int:
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
        raise ValueError("OpenAI API key is not set.")
    return AsyncOpenAI(api_key=api_key)

# Initialize the Azure Speech SDK configuration
def get_azure_speech_config() -> speechsdk.SpeechConfig:
    subscription_key = Config.AZURE_SUBSCRIPTION_KEY
    region = Config.AZURE_REGION
    if not subscription_key or not region:
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
        raise ValueError(f"Invalid OUTPUT_FORMAT: {Config.AZURE_AUDIO_FORMAT}")

    return speech_config
