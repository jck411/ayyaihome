# config/ai_service.py
from dataclasses import dataclass, field
import os
from typing import Optional, Dict

@dataclass
class BaseAIServiceConfig:
    api_key: str
    default_response_model: str
    temperature: float
    top_p: float

@dataclass
class OpenAIConfig(BaseAIServiceConfig):
    system_prompt: Dict[str, str] = field(default_factory=lambda: {
        "role": "system",
        "content": "You are a helpful but witty and dry assistant"
    })
    api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    default_response_model: str = "gpt-4o-mini"
    temperature: float = 1.0
    top_p: float = 1.0

@dataclass
class AnthropicConfig(BaseAIServiceConfig):
    api_key: str = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
    default_response_model: str = "claude-v1"
    temperature: float = 0.7
    top_p: float = 0.9
    # Anthropic does not use system_prompt

@dataclass
class AIServiceConfig:
    service_type: str  # "openai" or "anthropic"
    config: BaseAIServiceConfig

    @staticmethod
    def load_from_env() -> 'AIServiceConfig':
        service = os.getenv("AI_SERVICE_TYPE", "openai").lower()
        if service == "openai":
            return AIServiceConfig(
                service_type="openai",
                config=OpenAIConfig()
            )
        elif service == "anthropic":
            return AIServiceConfig(
                service_type="anthropic",
                config=AnthropicConfig()
            )
        else:
            raise ValueError(f"Unsupported AI service type: {service}")
