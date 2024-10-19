# /home/jack/ayyaihome/backend/services/tts_manager.py

import asyncio
import logging
from typing import Optional
from pynput import keyboard
import threading

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
            self._start_key_listener()

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

    def _start_key_listener(self):
        """
        Starts a keyboard listener in a separate thread.
        """
        listener_thread = threading.Thread(target=self._keyboard_listener, daemon=True)
        listener_thread.start()
        logger.info("Keyboard listener started.")

    def _keyboard_listener(self):
        """
        Listens for the Shift key press and triggers TTS stop.
        """
        def on_press(key):
            try:
                if key == keyboard.Key.shift:
                    logger.info("Shift key pressed. Stopping TTS.")
                    # Schedule the stop_active_tts coroutine in the event loop
                    asyncio.run_coroutine_threadsafe(self.stop_active_tts(), asyncio.get_event_loop())
            except Exception as e:
                logger.error(f"Error in keyboard listener: {e}")

        with keyboard.Listener(on_press=on_press) as listener:
            listener.join()

# Create a global instance
tts_manager = TTSManager()
