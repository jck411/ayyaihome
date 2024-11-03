# config/tts_service.py
from dataclasses import dataclass, field
import os
from typing import Optional, List

@dataclass
class BaseTTSServiceConfig:
    api_key: str
    default_tts_model: str
    default_voice: str
    speed: float
    chunk_size: int
    response_format: str = "pcm"  # Default response format set to "pcm"

@dataclass
class OpenAITTSConfig(BaseTTSServiceConfig):
    api_key: str = field(default_factory=lambda: os.getenv("OPENAI_TTS_API_KEY", ""))
    default_tts_model: str = "tts-1"
    default_voice: str = "alloy"
    speed: float = 1.0
    chunk_size: int = 1024
    # response_format inherited from BaseTTSServiceConfig

@dataclass
class AzureTTSConfig(BaseTTSServiceConfig):
    api_key: str = field(default_factory=lambda: os.getenv("AZURE_TTS_API_KEY", ""))
    default_tts_model: str = "azure-tts-1"
    default_voice: str = "azure-voice"
    speed: float = 1.0
    chunk_size: int = 1024
    available_voices: List[str] = field(default_factory=lambda: ["azure-voice-1", "azure-voice-2"])
    response_format: str = "pcm"  # Set default to "pcm" or as required

    def select_voice(self, voice_name: Optional[str] = None) -> str:
        if voice_name and voice_name in self.available_voices:
            return voice_name
        return self.default_voice

@dataclass
class TTSServiceConfig:
    service_type: str  # "openai" or "azure"
    config: BaseTTSServiceConfig

    @staticmethod
    def load_from_env() -> 'TTSServiceConfig':
        service = os.getenv("TTS_SERVICE_TYPE", "openai").lower()
        if service == "openai":
            return TTSServiceConfig(
                service_type="openai",
                config=OpenAITTSConfig()
            )
        elif service == "azure":
            return TTSServiceConfig(
                service_type="azure",
                config=AzureTTSConfig()
            )
        else:
            raise ValueError(f"Unsupported TTS service type: {service}")
