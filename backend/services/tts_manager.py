# /home/jack/ayyaihome/backend/services/tts_manager.py

import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class TTSManager:
    active_task: Optional[asyncio.Task]
    lock: asyncio.Lock

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TTSManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        # Initialize only once
        if not hasattr(self, 'active_task'):
            self.active_task = None
            self.lock = asyncio.Lock()

    async def stop_active_tts(self):
        """
        Stops the currently active TTS task, if any.
        """
        async with self.lock:
            if self.active_task and not self.active_task.done():
                logger.info("Stopping active TTS task...")
                self.active_task.cancel()
                try:
                    await self.active_task
                except asyncio.CancelledError:
                    logger.info("Active TTS task has been cancelled.")
                except Exception as e:
                    logger.error(f"Error while stopping TTS task: {e}")
                self.active_task = None
            else:
                logger.info("No active TTS task to stop.")

    def register_task(self, task: asyncio.Task):
        """
        Registers a new TTS task as the active task.
        """
        self.active_task = task
        logger.info("Registered new TTS task.")

    def clear_task(self):
        """
        Clears the reference to the active TTS task.
        """
        self.active_task = None
        logger.info("Cleared active TTS task.")

# Create a global instance
tts_manager = TTSManager()
