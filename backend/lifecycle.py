# lifecycle.py

import logging
from contextlib import asynccontextmanager

from stream_manager import StreamManager
from abc_classes import AudioPlayerBase

logger = logging.getLogger(__name__)

class AppLifecycle:
    def __init__(self, stream_manager: StreamManager, audio_player: AudioPlayerBase):
        self.stream_manager = stream_manager
        self.audio_player = audio_player

    @asynccontextmanager
    async def lifespan(self, app):
        logger.info("Starting up application...")
        try:
            yield
        finally:
            logger.info("Shutting down application...")
            await self.stream_manager.stop_all()
            self.audio_player.terminate()
            logger.info("Shutdown complete.")
