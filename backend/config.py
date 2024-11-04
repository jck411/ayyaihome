# config.py

import re
import pyaudio
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Type
from abc_classes import AIService, TTSService, AudioPlayerBase


@dataclass
class AIServiceConfig:
    SERVICE: str = "openai"  # Options: 'openai'
    DEFAULT_RESPONSE_MODEL: str = "gpt-4o-mini"
    TEMPERATURE: float = 1.0
    TOP_P: float = 1.0
    FREQUENCY_PENALTY: float = 0.0
    PRESENCE_PENALTY: float = 0.0
    MAX_TOKENS: int = 1000
    STOP: Optional[List[str]] = None
    LOGIT_BIAS: Optional[Dict[str, Any]] = None
    SYSTEM_PROMPT: Dict[str, str] = field(default_factory=lambda: {
        "role": "system",
        "content": "You are a helpful but witty and dry assistant, you rhyme all replies"
    })

@dataclass
class TTSServiceConfig:
    SERVICE: str = "openai"  # Options: 'openai'
    DEFAULT_TTS_MODEL: str = "tts-1"
    DEFAULT_VOICE: str = "alloy"  # other options: echo, fable, onyx, nova, shimmer
    RESPONSE_FORMAT: str = "pcm"  # options: "mp3", "opus", "aac", "flac"

@dataclass
class ResponseFormatConfig:
    SUPPORTED_FORMATS: List[str] = field(default_factory=lambda: ["pcm", "mp3", "opus", "aac", "flac"])

@dataclass
class Config:
    # General Configurations
    MINIMUM_PHRASE_LENGTH: int = 50
    TTS_CHUNK_SIZE: int = 1024
    AUDIO_FORMAT: int = pyaudio.paInt16
    CHANNELS: int = 1
    RATE: int = 24000
    TTS_SPEED: float = 1.0
    DELIMITERS: List[str] = field(default_factory=lambda: [".", "?", "!"])

    # Service Selection
    AI_SERVICE: str = "openai"        # Options: 'openai'
    TTS_SERVICE: str = "openai"       # Options: 'openai'
    AUDIO_PLAYER: str = "pyaudio"     # Options: 'pyaudio'

    # Service-Specific Configurations
    ai_service: AIServiceConfig = field(default_factory=AIServiceConfig)
    tts_service: TTSServiceConfig = field(default_factory=TTSServiceConfig)
    response_format: ResponseFormatConfig = field(default_factory=ResponseFormatConfig)

    # Dynamically create the regex pattern based on DELIMITERS
    DELIMITER_REGEX: str = field(init=False)
    DELIMITER_PATTERN: re.Pattern = field(init=False)

    def __post_init__(self):
        escaped_delimiters = ''.join(re.escape(d) for d in self.DELIMITERS)
        self.DELIMITER_REGEX = f"[{escaped_delimiters}]"
        self.DELIMITER_PATTERN = re.compile(self.DELIMITER_REGEX)

    def get_ai_service_class(self) -> Type['AIService']:
        from services.ai_services import OpenAIService  # Import here to avoid circular dependency
        service_map = {
            'openai': OpenAIService,
            # Removed 'anthropic'
        }
        service_class = service_map.get(self.AI_SERVICE.lower())
        if not service_class:
            raise ValueError(f"Unsupported AI_SERVICE: {self.AI_SERVICE}")
        return service_class

    def get_tts_service_class(self) -> Type['TTSService']:
        from services.tts_services import OpenAITTSService
        service_map = {
            'openai': OpenAITTSService,
            # Removed 'azure'
        }
        service_class = service_map.get(self.TTS_SERVICE.lower())
        if not service_class:
            raise ValueError(f"Unsupported TTS_SERVICE: {self.TTS_SERVICE}")
        return service_class

    def get_audio_player_class(self) -> Type['AudioPlayerBase']:
        from audio_players import PyAudioPlayer
        service_map = {
            'pyaudio': PyAudioPlayer,
            # Removed 'sounddevice'
        }
        service_class = service_map.get(self.AUDIO_PLAYER.lower())
        if not service_class:
            raise ValueError(f"Unsupported AUDIO_PLAYER: {self.AUDIO_PLAYER}")
        return service_class
