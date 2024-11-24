from typing import Any, Dict, List, Optional
from .loader import load_environment, load_config
import os

class Config:
    """
    Configuration class to hold all settings for TTS and LLM models.
    """
    
    # Load environment and config data
    load_environment()
    config_data = load_config()

    # === Processing Pipeline Settings ===
    PROCESSING_PIPELINE: Dict[str, Any] = config_data.get('PROCESSING_PIPELINE', {})

    MODULES: List[str] = PROCESSING_PIPELINE.get('MODULES', [])

    TOKENIZER_TYPE: str = PROCESSING_PIPELINE.get('TOKENIZER', {}).get('TYPE', 'none')

    if TOKENIZER_TYPE == 'nltk':
        NLTK_CONFIG: Dict[str, Any] = PROCESSING_PIPELINE.get('TOKENIZER', {}).get('NLTK', {})
        NLTK_LANGUAGE: str = NLTK_CONFIG.get('LANGUAGE')
        NLTK_TOKENIZER: str = NLTK_CONFIG.get('TOKENIZER')
        NLTK_PRESERVE_LINE: bool = NLTK_CONFIG.get('PRESERVE_LINE')
    elif TOKENIZER_TYPE == 'stanza':
        STANZA_CONFIG: Dict[str, Any] = PROCESSING_PIPELINE.get('TOKENIZER', {}).get('STANZA', {})
        STANZA_LANGUAGE: str = STANZA_CONFIG.get('LANGUAGE')
        STANZA_PROCESSORS: str = STANZA_CONFIG.get('PROCESSORS')
        STANZA_TOKENIZE_NO_SSPLIT: bool = STANZA_CONFIG.get('TOKENIZE_NO_SSPLIT')
        STANZA_USE_GPU: bool = STANZA_CONFIG.get('USE_GPU')
        STANZA_VERBOSE: bool = STANZA_CONFIG.get('VERBOSE')
    elif TOKENIZER_TYPE == 'none':
        pass
    else:
        raise ValueError(f"Unsupported TOKENIZER_TYPE: {TOKENIZER_TYPE}")

    USE_PHRASE_SEGMENTATION: bool = PROCESSING_PIPELINE.get('USE_PHRASE_SEGMENTATION', True)
    DELIMITERS: List[str] = PROCESSING_PIPELINE.get('DELIMITERS', [". ", "? ", "! "])
    MINIMUM_PHRASE_LENGTH: int = PROCESSING_PIPELINE.get('MINIMUM_PHRASE_LENGTH', 25)

    CUSTOM_TEXT_MODIFIER_ENABLED: bool = PROCESSING_PIPELINE.get('CUSTOM_TEXT_MODIFIER', {}).get('ENABLED', False)

    # === GENERAL_TTS ===
    GENERAL_TTS: Dict[str, Any] = config_data.get('GENERAL_TTS', {})
    TTS_PROVIDER: str = GENERAL_TTS.get('TTS_PROVIDER', "azure")

    # === TTS_MODELS ===
    TTS_MODELS: Dict[str, Any] = config_data.get('TTS_MODELS', {})

    # OpenAI TTS Configuration
    OPENAI_TTS_CONFIG: Dict[str, Any] = TTS_MODELS.get('OPENAI_TTS', {})
    OPENAI_TTS_SPEED: float = OPENAI_TTS_CONFIG.get('TTS_SPEED', 1.0)
    OPENAI_TTS_VOICE: str = OPENAI_TTS_CONFIG.get('TTS_VOICE', "onyx")
    OPENAI_TTS_MODEL: str = OPENAI_TTS_CONFIG.get('TTS_MODEL', "tts-1")
    OPENAI_AUDIO_RESPONSE_FORMAT: str = OPENAI_TTS_CONFIG.get('AUDIO_RESPONSE_FORMAT', "pcm")
    OPENAI_PLAYBACK_RATE: int = OPENAI_TTS_CONFIG.get('PLAYBACK_RATE', 24000)
    OPENAI_TTS_CHUNK_SIZE: int = OPENAI_TTS_CONFIG.get('TTS_CHUNK_SIZE', 1024)
    OPENAI_AUDIO_FORMAT_RATES: Dict[str, int] = OPENAI_TTS_CONFIG.get('AUDIO_FORMAT_RATES', {})

    # Azure TTS Configuration
    AZURE_TTS_CONFIG: Dict[str, Any] = TTS_MODELS.get('AZURE_TTS', {})
    AZURE_TTS_SPEED: str = AZURE_TTS_CONFIG.get('TTS_SPEED')  # Mandatory
    AZURE_TTS_VOICE: str = AZURE_TTS_CONFIG.get('TTS_VOICE')  # Mandatory
    AZURE_AUDIO_FORMAT: str = AZURE_TTS_CONFIG.get('AUDIO_FORMAT')  # Mandatory
    AZURE_PLAYBACK_RATE: int = AZURE_TTS_CONFIG.get('PLAYBACK_RATE')  # Mandatory
    AZURE_AUDIO_FORMAT_RATES: Dict[str, int] = AZURE_TTS_CONFIG.get('AUDIO_FORMAT_RATES', {})

    # === LLM_MODEL_CONFIG - OpenAI ===
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

    # === LLM_MODEL_CONFIG - Anthropic ===
    ANTHROPIC_CONFIG: Dict[str, Any] = config_data.get('LLM_MODEL_CONFIG', {}).get('ANTHROPIC', {})
    ANTHROPIC_RESPONSE_MODEL: str = ANTHROPIC_CONFIG.get('RESPONSE_MODEL', "claude-3-haiku-20240307")
    ANTHROPIC_TEMPERATURE: float = ANTHROPIC_CONFIG.get('TEMPERATURE', 0.7)
    ANTHROPIC_TOP_P: float = ANTHROPIC_CONFIG.get('TOP_P', 0.9)
    ANTHROPIC_SYSTEM_PROMPT: str = ANTHROPIC_CONFIG.get('SYSTEM_PROMPT', "you rhyme all of your replies")
    ANTHROPIC_MAX_TOKENS: int = ANTHROPIC_CONFIG.get('MAX_TOKENS', 1024)
    ANTHROPIC_STOP_SEQUENCES: Optional[Any] = ANTHROPIC_CONFIG.get('STOP_SEQUENCES', None)
    ANTHROPIC_STREAM_OPTIONS: Dict[str, Any] = ANTHROPIC_CONFIG.get('STREAM_OPTIONS', {"include_usage": True})

    # === LLM_MODEL_CONFIG - Gemini ===
    GEMINI_CONFIG: Dict[str, Any] = config_data.get('LLM_MODEL_CONFIG', {}).get('GEMINI', {})
    GEMINI_MODEL_VERSION: str = GEMINI_CONFIG.get('MODEL_VERSION', "gemini-1.5-flash")
    GEMINI_TEMPERATURE: float = GEMINI_CONFIG.get('TEMPERATURE', 0.7)
    GEMINI_SYSTEM_PROMPT: str = GEMINI_CONFIG.get('SYSTEM_PROMPT', "You are a knowledgeable assistant.")
    GEMINI_MAX_OUTPUT_TOKENS: int = GEMINI_CONFIG.get('MAX_OUTPUT_TOKENS', 150)
    GEMINI_TOP_P: float = GEMINI_CONFIG.get('TOP_P', 0.9)
    GEMINI_CANDIDATE_COUNT: int = GEMINI_CONFIG.get('CANDIDATE_COUNT', 1)

    # === AUDIO_PLAYBACK_CONFIG ===
    AUDIO_PLAYBACK_CONFIG: Dict[str, Any] = config_data.get('AUDIO_PLAYBACK_CONFIG', {})
    AUDIO_FORMAT: int = AUDIO_PLAYBACK_CONFIG.get('FORMAT', 16)
    CHANNELS: int = AUDIO_PLAYBACK_CONFIG.get('CHANNELS', 1)
    DEFAULT_RATE: Optional[int] = AUDIO_PLAYBACK_CONFIG.get('RATE', 24000)  # Default if no provider-specific rate

    # === Credentials ===
    AZURE_SPEECH_KEY: Optional[str] = os.getenv("AZURE_SPEECH_KEY")
    AZURE_SERVICE_REGION: Optional[str] = os.getenv("AZURE_SERVICE_REGION")
    OPENAI_API_KEY: Optional[str] = config_data.get('OPENAI_API_KEY') or os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = config_data.get('ANTHROPIC_API_KEY') or os.getenv("ANTHROPIC_API_KEY")

    # === Logging Configuration ===
    LOGGING: Dict[str, Any] = config_data.get('LOGGING', {})
    LOGGING_ENABLED: bool = LOGGING.get('ENABLED', True)
    LOGGING_LEVEL: str = LOGGING.get('LEVEL', "DEBUG")

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
