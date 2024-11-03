# config/__init__.py
from dataclasses import dataclass
from .ai_service import AIServiceConfig
from .tts_service import TTSServiceConfig
from .tts_processing import TTSProcessingConfig
from .audio_player import AudioPlayerConfig

@dataclass
class AppConfig:
    ai_service: AIServiceConfig
    tts_service: TTSServiceConfig
    tts_processing: TTSProcessingConfig
    audio_player: AudioPlayerConfig

    @staticmethod
    def load_from_env() -> 'AppConfig':
        return AppConfig(
            ai_service=AIServiceConfig.load_from_env(),
            tts_service=TTSServiceConfig.load_from_env(),
            tts_processing=TTSProcessingConfig(),
            audio_player=AudioPlayerConfig.load_from_env()
        )
