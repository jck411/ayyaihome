# abc_classes.py

from abc import ABC, abstractmethod
from typing import List, AsyncIterator
import asyncio

class AIService(ABC):
    @abstractmethod
    async def stream_completion(
        self, 
        messages: List[dict], 
        phrase_queue: asyncio.Queue, 
        stop_event: asyncio.Event, 
        stream_id: str
    ) -> AsyncIterator[str]:
        """Streams AI completion."""
        pass

class TTSService(ABC):
    @abstractmethod
    async def process(
        self, 
        phrase_queue: asyncio.Queue, 
        audio_queue: asyncio.Queue, 
        stop_event: asyncio.Event, 
        stream_id: str
    ):
        """Processes text to speech."""
        pass

class AudioPlayerBase(ABC):
    @abstractmethod
    async def play(
        self, 
        audio_queue: asyncio.Queue, 
        stop_event: asyncio.Event, 
        stream_id: str, 
        start_time: float
    ):
        """Plays audio."""
        pass

    @abstractmethod
    def terminate(self):
        """Terminates the audio player."""
        pass
