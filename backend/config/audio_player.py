# config/audio_player.py
from dataclasses import dataclass, field
import pyaudio
import os

@dataclass
class BaseAudioPlayerConfig:
    audio_format: int
    channels: int
    rate: int
    frames_per_buffer: int

@dataclass
class PyAudioConfig(BaseAudioPlayerConfig):
    audio_format: int = pyaudio.paInt16
    channels: int = 1
    rate: int = 24000
    frames_per_buffer: int = 2048

@dataclass
class AudioPlayerConfig:
    player_type: str  # e.g., "pyaudio"
    config: BaseAudioPlayerConfig

    @staticmethod
    def load_from_env() -> 'AudioPlayerConfig':
        player = os.getenv("AUDIO_PLAYER_TYPE", "pyaudio").lower()
        if player == "pyaudio":
            return AudioPlayerConfig(
                player_type="pyaudio",
                config=PyAudioConfig()
            )
        else:
            raise ValueError(f"Unsupported audio player type: {player}")
