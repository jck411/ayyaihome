import os
import yaml
from pathlib import Path
from typing import Any, Dict


class LLMConfig:
    """
    Loads and manages configurations for LLM models (OpenAI, Anthropic, Gemini).
    """
    CONFIG_PATH = Path(os.getenv("LLM_CONFIG_PATH", Path(__file__).parent / "llm_config.yaml"))
    _instance = None

    def __init__(self):
        try:
            with open(self.CONFIG_PATH, 'r') as config_file:
                config_data = yaml.safe_load(config_file)
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found at {self.CONFIG_PATH}")
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing YAML configuration: {e}")

        llm_config = config_data.get('LLM_MODEL_CONFIG', {})

        # OpenAI Configuration
        openai_config = llm_config.get('OPENAI', {})
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # API key fetched from the .env file
        self.OPENAI_RESPONSE_MODEL = openai_config.get('RESPONSE_MODEL', "gpt-4o-mini")
        self.OPENAI_TEMPERATURE = openai_config.get('TEMPERATURE', 1.0)
        self.OPENAI_TOP_P = openai_config.get('TOP_P', 1.0)
        self.OPENAI_N = openai_config.get('N', 1)
        self.OPENAI_SYSTEM_PROMPT = openai_config.get('SYSTEM_PROMPT_CONTENT', "You are a helpful assistant")
        self.OPENAI_STREAM_OPTIONS = openai_config.get('STREAM_OPTIONS', {"include_usage": True})
        self.OPENAI_MAX_TOKENS = openai_config.get('MAX_TOKENS', None)
        self.OPENAI_PRESENCE_PENALTY = openai_config.get('PRESENCE_PENALTY', 0.0)
        self.OPENAI_FREQUENCY_PENALTY = openai_config.get('FREQUENCY_PENALTY', 0.0)

        # Anthropic Configuration
        anthropic_config = llm_config.get('ANTHROPIC', {})
        self.ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")  # API key fetched from the .env file
        self.ANTHROPIC_RESPONSE_MODEL = anthropic_config.get('RESPONSE_MODEL', "claude-3")
        self.ANTHROPIC_TEMPERATURE = anthropic_config.get('TEMPERATURE', 1.0)
        self.ANTHROPIC_TOP_P = anthropic_config.get('TOP_P', 1.0)
        self.ANTHROPIC_SYSTEM_PROMPT = anthropic_config.get('SYSTEM_PROMPT', "You are a dry and witty assistant")
        self.ANTHROPIC_MAX_TOKENS = anthropic_config.get('MAX_TOKENS', 1024)
        self.ANTHROPIC_STREAM_OPTIONS = anthropic_config.get('STREAM_OPTIONS', {"include_usage": True})
        self.ANTHROPIC_STOP_SEQUENCES = anthropic_config.get('STOP_SEQUENCES', None)  # Add this line
        
        # Gemini Configuration
        gemini_config = llm_config.get('GEMINI', {})
        self.GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")  # API key fetched from the .env file
        self.GEMINI_MODEL_VERSION = gemini_config.get('MODEL_VERSION', "gemini-1.5-flash")
        self.GEMINI_TEMPERATURE = gemini_config.get('TEMPERATURE', 0.7)
        self.GEMINI_SYSTEM_PROMPT = gemini_config.get('SYSTEM_PROMPT', "You are a knowledgeable assistant.")
        self.GEMINI_MAX_OUTPUT_TOKENS = gemini_config.get('MAX_OUTPUT_TOKENS', 150)
        self.GEMINI_TOP_P = gemini_config.get('TOP_P', 0.9)
        self.GEMINI_CANDIDATE_COUNT = gemini_config.get('CANDIDATE_COUNT', 1)

        # Mistral Configuration
        mistral_config = llm_config.get('MISTRAL', {})
        self.MISTRAL_API_KEY = os.getenv(mistral_config.get('API_KEY_ENV_VAR', 'MISTRAL_API_KEY'))  # Fetch API key from specified environment variable
        self.MISTRAL_RESPONSE_MODEL = mistral_config.get('RESPONSE_MODEL', "mistral-tiny")
        self.MISTRAL_TEMPERATURE = mistral_config.get('TEMPERATURE', 0.7)
        self.MISTRAL_TOP_P = mistral_config.get('TOP_P', 0.9)
        self.MISTRAL_SYSTEM_PROMPT = mistral_config.get('SYSTEM_PROMPT', "You are a helpful and concise assistant.")
        self.MISTRAL_MAX_TOKENS = mistral_config.get('MAX_TOKENS', 1500)
        self.MISTRAL_STOP_SEQUENCES = mistral_config.get('STOP_SEQUENCES', [])
        self.MISTRAL_STREAM_OPTIONS = mistral_config.get('STREAM_OPTIONS', {"include_usage": True})

        # Grok Configuration
        grok_config = llm_config.get('GROK', {})
        self.GROK_API_KEY = os.getenv("GROK_API_KEY")  # Fetch from environment variable
        self.GROK_API_BASE = grok_config.get('API_BASE', "https://api.x.ai/v1")  # Default API base
        self.GROK_RESPONSE_MODEL = grok_config.get('RESPONSE_MODEL', "grok-beta")
        self.GROK_TEMPERATURE = grok_config.get('TEMPERATURE', 0.7)
        self.GROK_TOP_P = grok_config.get('TOP_P', 0.9)
        self.GROK_SYSTEM_PROMPT = grok_config.get('SYSTEM_PROMPT', "You are a creative assistant.")
        self.GROK_MAX_TOKENS = grok_config.get('MAX_TOKENS', 2000)
        self.GROK_STREAM_OPTIONS = grok_config.get('STREAM_OPTIONS', {"include_usage": True})
        self.GROK_STOP = grok_config.get('STOP', None)

        # Validate critical fields
        if not self.OPENAI_API_KEY:
            raise ValueError("OpenAI API key (OPENAI_API_KEY) is missing from the .env file.")
        if not self.ANTHROPIC_API_KEY:
            raise ValueError("Anthropic API key (ANTHROPIC_API_KEY) is missing from the .env file.")
        if not self.GEMINI_API_KEY:
            raise ValueError("Google API key (GOOGLE_API_KEY) is missing from the .env file.")
        if not self.MISTRAL_API_KEY:
            raise ValueError("Mistral API key (MISTRAL_API_KEY) is missing from the .env file.")
        if not self.GROK_API_KEY:
            raise ValueError("Grok API key (GROK_API_KEY) is missing from the .env file.")

    @classmethod
    def get_instance(cls) -> "LLMConfig":
        """
        Singleton instance of LLMConfig.
        Ensures the configuration is only loaded once.
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
