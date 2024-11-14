import os
import yaml
import logging
from dotenv import load_dotenv
from openai import AsyncOpenAI

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

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration parameters
class Config:
    # GENERAL_TTS
    TTS_CHUNK_SIZE = config_data.get('GENERAL_TTS', {}).get('TTS_CHUNK_SIZE', 1024)
    DELIMITERS = config_data.get('GENERAL_TTS', {}).get('DELIMITERS', [". ", "? ", "! "])
    MINIMUM_PHRASE_LENGTH = config_data.get('GENERAL_TTS', {}).get('MINIMUM_PHRASE_LENGTH', 25)

    # TTS_MODELS
    OPENAI_TTS_CONFIG = config_data.get('TTS_MODELS', {}).get('OPENAI_TTS', {})
    TTS_SPEED = OPENAI_TTS_CONFIG.get('TTS_SPEED', 1.0)
    TTS_VOICE = OPENAI_TTS_CONFIG.get('TTS_VOICE', "alloy")
    TTS_MODEL = OPENAI_TTS_CONFIG.get('TTS_MODEL', "tts-1")
    AUDIO_RESPONSE_FORMAT = OPENAI_TTS_CONFIG.get('AUDIO_RESPONSE_FORMAT', "pcm")

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

    # Log the Anthropic system prompt
    logger.info(f"Anthropic System Prompt Loaded: {ANTHROPIC_SYSTEM_PROMPT}")

    # AUDIO_PLAYBACK_CONFIG
    AUDIO_FORMAT = config_data.get('AUDIO_PLAYBACK_CONFIG', {}).get('FORMAT', 8)
    CHANNELS = config_data.get('AUDIO_PLAYBACK_CONFIG', {}).get('CHANNELS', 1)
    RATE = config_data.get('AUDIO_PLAYBACK_CONFIG', {}).get('RATE', 24000)


# Initialize the OpenAI API client using dependency injection
def get_openai_client() -> AsyncOpenAI:
    api_key = config_data.get('OPENAI_API_KEY') or os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("OpenAI API key is not set.")
        raise ValueError("OpenAI API key is not set.")
    return AsyncOpenAI(api_key=api_key)
