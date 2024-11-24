import os
import yaml
from dotenv import load_dotenv
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic

from pathlib import Path
from typing import Any, Dict, List, Optional

# Load environment variables from a .env file
load_dotenv()

# Load configuration from YAML file
CONFIG_PATH = Path(__file__).parent / "llm_config.yaml"

try:
    with open(CONFIG_PATH, 'r') as config_file:
        config_data = yaml.safe_load(config_file)
except FileNotFoundError:
    raise FileNotFoundError(f"Configuration file not found at {CONFIG_PATH}")
except yaml.YAMLError as e:
    raise ValueError(f"Error parsing YAML configuration: {e}")

# LLMConfig class to manage LLM-related configurations
class LLMConfig:
    """
    Configuration for LLM models.
    """

    def __init__(self, config_data: Dict[str, Any]):
        llm_config = config_data.get('LLM_MODEL_CONFIG', {})

        # OpenAI Config
        openai_config = llm_config.get('OPENAI', {})
        self.RESPONSE_MODEL: str = openai_config.get('RESPONSE_MODEL', "gpt-4o-mini")
        self.TEMPERATURE: float = openai_config.get('TEMPERATURE', 1.0)
        self.TOP_P: float = openai_config.get('TOP_P', 1.0)
        self.N: int = openai_config.get('N', 1)
        self.SYSTEM_PROMPT_CONTENT: str = openai_config.get('SYSTEM_PROMPT_CONTENT', "You are a helpful but witty and dry assistant")
        self.STREAM_OPTIONS: Dict[str, Any] = openai_config.get('STREAM_OPTIONS', {"include_usage": True})
        self.STOP: Optional[Any] = openai_config.get('STOP', None)
        self.MAX_TOKENS: Optional[int] = openai_config.get('MAX_TOKENS', None)
        self.PRESENCE_PENALTY: float = openai_config.get('PRESENCE_PENALTY', 0.0)
        self.FREQUENCY_PENALTY: float = openai_config.get('FREQUENCY_PENALTY', 0.0)
        self.LOGIT_BIAS: Optional[Any] = openai_config.get('LOGIT_BIAS', None)
        self.USER: Optional[Any] = openai_config.get('USER', None)
        self.TOOLS: Optional[Any] = openai_config.get('TOOLS', None)
        self.TOOL_CHOICE: Optional[Any] = openai_config.get('TOOL_CHOICE', None)
        self.MODALITIES: List[str] = openai_config.get('MODALITIES', ["text"])

        # Anthropic Config
        anthropic_config = llm_config.get('ANTHROPIC', {})
        self.ANTHROPIC_RESPONSE_MODEL: str = anthropic_config.get('RESPONSE_MODEL', "claude-3-haiku-20240307")
        self.ANTHROPIC_TEMPERATURE: float = anthropic_config.get('TEMPERATURE', 0.7)
        self.ANTHROPIC_TOP_P: float = anthropic_config.get('TOP_P', 0.9)
        self.ANTHROPIC_SYSTEM_PROMPT: str = anthropic_config.get('SYSTEM_PROMPT', "you rhyme all of your replies")
        self.ANTHROPIC_MAX_TOKENS: int = anthropic_config.get('MAX_TOKENS', 1024)
        self.ANTHROPIC_STOP_SEQUENCES: Optional[Any] = anthropic_config.get('STOP_SEQUENCES', None)
        self.ANTHROPIC_STREAM_OPTIONS: Dict[str, Any] = anthropic_config.get('STREAM_OPTIONS', {"include_usage": True})

        # API Keys
        self.OPENAI_API_KEY: Optional[str] = config_data.get('OPENAI_API_KEY') or os.getenv("OPENAI_API_KEY")
        self.ANTHROPIC_API_KEY: Optional[str] = config_data.get('ANTHROPIC_API_KEY') or os.getenv("ANTHROPIC_API_KEY")

# Main Config class
class Config:
    """
    Main configuration class to load all configurations.
    """

    LLM_CONFIG = LLMConfig(config_data)


# Initialize the OpenAI API client using dependency injection
def get_openai_client() -> AsyncOpenAI:
    api_key = Config.LLM_CONFIG.OPENAI_API_KEY
    if not api_key:
        raise ValueError("OpenAI API key is not set.")
    return AsyncOpenAI(api_key=api_key)

# Initialize the Anthropic API client using dependency injection
def get_anthropic_client() -> AsyncAnthropic:
    api_key = Config.LLM_CONFIG.ANTHROPIC_API_KEY
    if not api_key:
        raise ValueError("Anthropic API key is not set.")
    return AsyncAnthropic(api_key=api_key)
