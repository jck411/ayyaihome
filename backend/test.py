import os
import yaml
from dotenv import load_dotenv
from pathlib import Path
from typing import Any, Dict, List, Optional
import azure.cognitiveservices.speech as speechsdk

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

    # === Processing Pipeline Settings ===
    try:
        PROCESSING_PIPELINE: Dict[str, Any] = config_data['PROCESSING_PIPELINE']
    except KeyError:
        raise ValueError("PROCESSING_PIPELINE section is missing in the configuration.")

    # List of modules to include in the processing pipeline.
    # The modules are applied in the order they appear in the list.
    try:
        MODULES: List[str] = PROCESSING_PIPELINE['MODULES']
    except KeyError:
        raise ValueError("MODULES is missing in PROCESSING_PIPELINE configuration.")

    # Segmentation settings
    try:
        USE_PHRASE_SEGMENTATION: bool = PROCESSING_PIPELINE['USE_PHRASE_SEGMENTATION']
        DELIMITERS: List[str] = PROCESSING_PIPELINE['DELIMITERS']
        MINIMUM_PHRASE_LENGTH: int = PROCESSING_PIPELINE['MINIMUM_PHRASE_LENGTH']
    except KeyError as e:
        raise ValueError(f"{e} is missing in PROCESSING_PIPELINE configuration.")

    # Tokenizer settings
    try:
        TOKENIZER_CONFIG: Dict[str, Any] = PROCESSING_PIPELINE['TOKENIZER']
        TOKENIZER_TYPE: str = TOKENIZER_CONFIG['TYPE']
    except KeyError as e:
        raise ValueError(f"Missing TOKENIZER configuration: {e}")

    if TOKENIZER_TYPE == 'nltk':
        try:
            NLTK_CONFIG: Dict[str, Any] = TOKENIZER_CONFIG['NLTK']
            NLTK_LANGUAGE: str = NLTK_CONFIG['LANGUAGE']
            NLTK_TOKENIZER: str = NLTK_CONFIG['TOKENIZER']
            NLTK_PRESERVE_LINE: bool = NLTK_CONFIG['PRESERVE_LINE']
        except KeyError as e:
            raise ValueError(f"Missing NLTK configuration option: {e}")

    elif TOKENIZER_TYPE == 'stanza':
        try:
            STANZA_CONFIG: Dict[str, Any] = TOKENIZER_CONFIG['STANZA']
            STANZA_LANGUAGE: str = STANZA_CONFIG['LANGUAGE']
            STANZA_PROCESSORS: str = STANZA_CONFIG['PROCESSORS']
            STANZA_TOKENIZE_NO_SSPLIT: bool = STANZA_CONFIG['TOKENIZE_NO_SSPLIT']
            STANZA_USE_GPU: bool = STANZA_CONFIG['USE_GPU']
            STANZA_VERBOSE: bool = STANZA_CONFIG['VERBOSE']
        except KeyError as e:
            raise ValueError(f"Missing STANZA configuration option: {e}")

    elif TOKENIZER_TYPE == 'none':
        pass  # No additional configuration needed
    else:
        raise ValueError(f"Unsupported TOKENIZER_TYPE: {TOKENIZER_TYPE}")

    # Custom Text Modifier settings
    try:
        CUSTOM_TEXT_MODIFIER_ENABLED: bool = PROCESSING_PIPELINE['CUSTOM_TEXT_MODIFIER']['ENABLED']
    except KeyError:
        raise ValueError("CUSTOM_TEXT_MODIFIER.ENABLED is missing in PROCESSING_PIPELINE configuration.")

    # === GENERAL_TTS ===
    try:
        GENERAL_TTS: Dict[str, Any] = config_data['GENERAL_TTS']
        TTS_PROVIDER: str = GENERAL_TTS['TTS_PROVIDER']
    except KeyError as e:
        raise ValueError(f"Missing GENERAL_TTS configuration: {e}")

    # === TTS_MODELS ===
    try:
        TTS_MODELS: Dict[str, Any] = config_data['TTS_MODELS']
    except KeyError:
        raise ValueError("TTS_MODELS section is missing in the configuration.")

    if TTS_PROVIDER.lower() == "openai":
        try:
            OPENAI_TTS_CONFIG: Dict[str, Any] = TTS_MODELS['OPENAI_TTS']
            OPENAI_TTS_CHUNK_SIZE: int = OPENAI_TTS_CONFIG['TTS_CHUNK_SIZE']
            OPENAI_TTS_SPEED: float = OPENAI_TTS_CONFIG['TTS_SPEED']
            OPENAI_TTS_VOICE: str = OPENAI_TTS_CONFIG['TTS_VOICE']
            OPENAI_TTS_MODEL: str = OPENAI_TTS_CONFIG['TTS_MODEL']
            OPENAI_AUDIO_RESPONSE_FORMAT: str = OPENAI_TTS_CONFIG['AUDIO_RESPONSE_FORMAT']
            OPENAI_AUDIO_FORMAT_RATES: Dict[str, int] = OPENAI_TTS_CONFIG['AUDIO_FORMAT_RATES']
            OPENAI_PLAYBACK_RATE: int = OPENAI_TTS_CONFIG['PLAYBACK_RATE']
        except KeyError as e:
            raise ValueError(f"Missing OPENAI_TTS configuration option: {e}")

    elif TTS_PROVIDER.lower() == "azure":
        try:
            AZURE_TTS_CONFIG: Dict[str, Any] = TTS_MODELS['AZURE_TTS']
            AZURE_TTS_SPEED: str = AZURE_TTS_CONFIG['TTS_SPEED']
            AZURE_TTS_VOICE: str = AZURE_TTS_CONFIG['TTS_VOICE']
            AZURE_SPEECH_SYNTHESIS_RATE: str = AZURE_TTS_CONFIG['SPEECH_SYNTHESIS_RATE']
            AZURE_AUDIO_FORMAT: str = AZURE_TTS_CONFIG['AUDIO_FORMAT']
            AZURE_AUDIO_FORMAT_RATES: Dict[str, int] = AZURE_TTS_CONFIG['AUDIO_FORMAT_RATES']
            AZURE_PLAYBACK_RATE: int = AZURE_TTS_CONFIG['PLAYBACK_RATE']
            AZURE_ENABLE_PROFANITY_FILTER: bool = AZURE_TTS_CONFIG['ENABLE_PROFANITY_FILTER']
            AZURE_STABILITY: int = AZURE_TTS_CONFIG['STABILITY']
            AZURE_PROSODY: Dict[str, Any] = AZURE_TTS_CONFIG['PROSODY']
            # Extract PROSODY options
            AZURE_PROSODY_RATE: str = AZURE_PROSODY['rate']
            AZURE_PROSODY_PITCH: str = AZURE_PROSODY['pitch']
            AZURE_PROSODY_VOLUME: str = AZURE_PROSODY['volume']
        except KeyError as e:
            raise ValueError(f"Missing AZURE_TTS configuration option: {e}")
    else:
        raise ValueError(f"Unsupported TTS_PROVIDER: {TTS_PROVIDER}")

    # === LLM_MODEL_CONFIG ===
    try:
        LLM_MODEL_CONFIG: Dict[str, Any] = config_data['LLM_MODEL_CONFIG']
    except KeyError:
        raise ValueError("LLM_MODEL_CONFIG section is missing in the configuration.")

    # OpenAI LLM Config
    try:
        OPENAI_CONFIG: Dict[str, Any] = LLM_MODEL_CONFIG['OPENAI']
        OPENAI_RESPONSE_MODEL: str = OPENAI_CONFIG['RESPONSE_MODEL']
        OPENAI_TEMPERATURE: float = OPENAI_CONFIG['TEMPERATURE']
        OPENAI_TOP_P: float = OPENAI_CONFIG['TOP_P']
        OPENAI_N: int = OPENAI_CONFIG['N']
        OPENAI_SYSTEM_PROMPT_CONTENT: str = OPENAI_CONFIG['SYSTEM_PROMPT_CONTENT']
        OPENAI_STREAM_OPTIONS: Dict[str, Any] = OPENAI_CONFIG['STREAM_OPTIONS']
        OPENAI_STOP: Optional[Any] = OPENAI_CONFIG['STOP']
        OPENAI_MAX_TOKENS: Optional[int] = OPENAI_CONFIG['MAX_TOKENS']
        OPENAI_PRESENCE_PENALTY: float = OPENAI_CONFIG['PRESENCE_PENALTY']
        OPENAI_FREQUENCY_PENALTY: float = OPENAI_CONFIG['FREQUENCY_PENALTY']
        OPENAI_LOGIT_BIAS: Optional[Any] = OPENAI_CONFIG['LOGIT_BIAS']
        OPENAI_USER: Optional[Any] = OPENAI_CONFIG['USER']
        OPENAI_TOOLS: Optional[Any] = OPENAI_CONFIG['TOOLS']
        OPENAI_TOOL_CHOICE: Optional[Any] = OPENAI_CONFIG['TOOL_CHOICE']
        OPENAI_MODALITIES: List[str] = OPENAI_CONFIG['MODALITIES']
    except KeyError as e:
        raise ValueError(f"Missing OPENAI LLM configuration option: {e}")

    # Anthropic LLM Config
    try:
        ANTHROPIC_CONFIG: Dict[str, Any] = LLM_MODEL_CONFIG['ANTHROPIC']
        ANTHROPIC_RESPONSE_MODEL: str = ANTHROPIC_CONFIG['RESPONSE_MODEL']
        ANTHROPIC_TEMPERATURE: float = ANTHROPIC_CONFIG['TEMPERATURE']
        ANTHROPIC_TOP_P: float = ANTHROPIC_CONFIG['TOP_P']
        ANTHROPIC_SYSTEM_PROMPT: str = ANTHROPIC_CONFIG['SYSTEM_PROMPT']
        ANTHROPIC_MAX_TOKENS: int = ANTHROPIC_CONFIG['MAX_TOKENS']
        ANTHROPIC_STOP_SEQUENCES: Optional[Any] = ANTHROPIC_CONFIG['STOP_SEQUENCES']
        ANTHROPIC_STREAM_OPTIONS: Dict[str, Any] = ANTHROPIC_CONFIG['STREAM_OPTIONS']
    except KeyError as e:
        raise ValueError(f"Missing ANTHROPIC LLM configuration option: {e}")

    # === AUDIO_PLAYBACK_CONFIG ===
    try:
        AUDIO_PLAYBACK_CONFIG: Dict[str, Any] = config_data['AUDIO_PLAYBACK_CONFIG']
        AUDIO_FORMAT: int = AUDIO_PLAYBACK_CONFIG['FORMAT']
        CHANNELS: int = AUDIO_PLAYBACK_CONFIG['CHANNELS']
        DEFAULT_RATE: Optional[int] = AUDIO_PLAYBACK_CONFIG['RATE']  # May be null
    except KeyError as e:
        raise ValueError(f"Missing AUDIO_PLAYBACK_CONFIG option: {e}")

    # === LOGGING CONFIGURATION ===
    try:
        LOGGING_CONFIG: Dict[str, Any] = config_data['LOGGING']
        LOGGING_ENABLED: bool = LOGGING_CONFIG['ENABLED']
        LOGGING_LEVEL: str = LOGGING_CONFIG['LEVEL']
    except KeyError as e:
        raise ValueError(f"Missing LOGGING configuration option: {e}")

    # Azure Credentials from .env
    AZURE_SPEECH_KEY: Optional[str] = os.getenv("AZURE_SPEECH_KEY")
    AZURE_SERVICE_REGION: Optional[str] = os.getenv("AZURE_SERVICE_REGION")

    # OpenAI Credentials from .env or config.yaml
    OPENAI_API_KEY: Optional[str] = config_data.get('OPENAI_API_KEY') or os.getenv("OPENAI_API_KEY")

    # Anthropic Credentials from .env or config.yaml
    ANTHROPIC_API_KEY: Optional[str] = config_data.get('ANTHROPIC_API_KEY') or os.getenv("ANTHROPIC_API_KEY")

    @staticmethod
    def get_playback_rate() -> int:
        if Config.TTS_PROVIDER.lower() == "openai":
            audio_format = Config.OPENAI_AUDIO_RESPONSE_FORMAT
            format_rates = Config.OPENAI_AUDIO_FORMAT_RATES
        elif Config.TTS_PROVIDER.lower() == "azure":
            audio_format = Config.AZURE_AUDIO_FORMAT
            format_rates = Config.AZURE_AUDIO_FORMAT_RATES
        else:
            raise ValueError(f"Unsupported TTS_PROVIDER: {Config.TTS_PROVIDER}")

        # Fetch the rate dynamically based on the chosen audio format
        playback_rate = format_rates.get(audio_format)
        if playback_rate is None:
            raise ValueError(f"Unsupported AUDIO_FORMAT: {audio_format}. Please specify a valid audio format.")

        return playback_rate

# Initialize the Azure Speech SDK configuration
def get_azure_speech_config() -> speechsdk.SpeechConfig:
    subscription_key = Config.AZURE_SPEECH_KEY
    region = Config.AZURE_SERVICE_REGION
    if not subscription_key or not region:
        raise ValueError("Azure Speech credentials are not set.")
    speech_config = speechsdk.SpeechConfig(subscription=subscription_key, region=region)
    speech_config.speech_synthesis_voice_name = Config.AZURE_TTS_VOICE
    speech_config.speech_synthesis_rate = Config.AZURE_SPEECH_SYNTHESIS_RATE

    # Set output format
    try:
        speech_config.set_speech_synthesis_output_format(
            getattr(speechsdk.SpeechSynthesisOutputFormat, Config.AZURE_AUDIO_FORMAT)
        )
    except AttributeError:
        raise ValueError(f"Invalid OUTPUT_FORMAT: {Config.AZURE_AUDIO_FORMAT}")

    # Set profanity option
    if Config.AZURE_ENABLE_PROFANITY_FILTER:
        speech_config.set_profanity(speechsdk.ProfanityOption.Removed)
    else:
        speech_config.set_profanity(speechsdk.ProfanityOption.Raw)

    # Note: Stability and prosody adjustments may require SSML or other advanced configurations

    return speech_config

# Initialize the OpenAI API client (if needed in your application)
def get_openai_api_key() -> str:
    if not Config.OPENAI_API_KEY:
        raise ValueError("OpenAI API key is not set.")
    return Config.OPENAI_API_KEY

# Initialize the Anthropic API client (if needed in your application)
def get_anthropic_api_key() -> str:
    if not Config.ANTHROPIC_API_KEY:
        raise ValueError("Anthropic API key is not set.")
    return Config.ANTHROPIC_API_KEY
