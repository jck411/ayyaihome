import os
import yaml
from pathlib import Path


class TTSConfig:
    """
    Centralized configuration access for TTS and related settings.
    Loads and provides configurations for OpenAI and Azure TTS, along with general settings.
    """
    CONFIG_PATH = Path(os.getenv("TTS_CONFIG_PATH", Path(__file__).parent / "tts_config.yaml"))
    _instance = None

    def __init__(self):
        try:
            with open(self.CONFIG_PATH, 'r') as config_file:
                config_data = yaml.safe_load(config_file)
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found at {self.CONFIG_PATH}")
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing YAML configuration: {e}")

        # General TTS Settings
        general_tts = config_data.get('GENERAL_TTS', {})
        self.TTS_PROVIDER = general_tts.get('TTS_PROVIDER', 'openai').lower()

        # Processing Pipeline Settings
        pipeline = config_data.get('PROCESSING_PIPELINE', {})
        self.MODULES = pipeline.get('MODULES', [])
        self.USE_PHRASE_SEGMENTATION = pipeline.get('USE_PHRASE_SEGMENTATION', True)
        self.DELIMITERS = pipeline.get('DELIMITERS', [". ", "? ", "! "])

        tokenizer = pipeline.get('TOKENIZER', {})
        self.TOKENIZER_TYPE = tokenizer.get('TYPE', 'none')
        self.NLTK_CONFIG = tokenizer.get('NLTK', {})
        self.STANZA_CONFIG = tokenizer.get('STANZA', {})

        custom_text_modifier = pipeline.get('CUSTOM_TEXT_MODIFIER', {})
        self.CUSTOM_TEXT_MODIFIER_ENABLED = custom_text_modifier.get('ENABLED', False)

        # TTS Models
        tts_models = config_data.get('TTS_MODELS', {})

        # Azure TTS API Keys
        self.AZURE_SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")
        self.AZURE_SPEECH_REGION = os.getenv("AZURE_SPEECH_REGION")

        # OpenAI TTS
        openai_tts = tts_models.get('OPENAI_TTS', {})
        self.OPENAI_TTS_CHUNK_SIZE = openai_tts.get('TTS_CHUNK_SIZE', 1024)
        self.OPENAI_TTS_SPEED = openai_tts.get('TTS_SPEED', 1.0)
        self.OPENAI_TTS_VOICE = openai_tts.get('TTS_VOICE', 'alloy')
        self.OPENAI_TTS_MODEL = openai_tts.get('TTS_MODEL', 'tts-1')
        self.OPENAI_AUDIO_FORMAT = openai_tts.get('AUDIO_RESPONSE_FORMAT', 'pcm')
        self.OPENAI_AUDIO_FORMAT_RATES = openai_tts.get('AUDIO_FORMAT_RATES', {})
        self.OPENAI_PLAYBACK_RATE = openai_tts.get('PLAYBACK_RATE', 24000)

        # Azure TTS
        azure_tts = tts_models.get('AZURE_TTS', {})
        self.AZURE_TTS_SPEED = azure_tts.get('TTS_SPEED', '0%')
        self.AZURE_TTS_VOICE = azure_tts.get('TTS_VOICE', 'en-US-KaiNeural')
        self.AZURE_AUDIO_FORMAT = azure_tts.get('AUDIO_FORMAT', 'Raw24Khz16BitMonoPcm')
        self.AZURE_AUDIO_FORMAT_RATES = azure_tts.get('AUDIO_FORMAT_RATES', {})
        self.AZURE_PLAYBACK_RATE = azure_tts.get('PLAYBACK_RATE', 24000)
        self.AZURE_ENABLE_PROFANITY_FILTER = azure_tts.get('ENABLE_PROFANITY_FILTER', False)
        self.AZURE_STABILITY = azure_tts.get('STABILITY', 0)
        self.AZURE_PROSODY = azure_tts.get('PROSODY', {})

        # Audio Playback Configuration
        audio_playback_config = config_data.get('AUDIO_PLAYBACK_CONFIG', {})
        self.AUDIO_FORMAT = audio_playback_config.get('FORMAT', 16)
        self.AUDIO_CHANNELS = audio_playback_config.get('CHANNELS', 1)
        self.AUDIO_RATE = audio_playback_config.get('RATE', None)

    @classmethod
    def get_instance(cls) -> "TTSConfig":
        """
        Singleton instance of TTSConfig.
        Ensures the configuration is only loaded once.
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
