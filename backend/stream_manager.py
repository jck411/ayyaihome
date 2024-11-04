# stream_manager.py

import asyncio
import logging

logger = logging.getLogger(__name__)

class StreamManager:
    def __init__(self):
        self.active_streams = {}
        self.lock = asyncio.Lock()

    async def add_stream(self, stream_id: str, stop_event: asyncio.Event, task: asyncio.Task):
        async with self.lock:
            self.active_streams[stream_id] = {
                "stop_event": stop_event,
                "task": task
            }

    async def remove_stream(self, stream_id: str):
        async with self.lock:
            if stream_id in self.active_streams:
                del self.active_streams[stream_id]
                logger.info(f"Cleaned up stream with ID: {stream_id}")

    async def stop_all(self):
        async with self.lock:
            if not self.active_streams:
                logger.info("No active streams to stop.")
                return

            logger.info("Stopping all active streams...")
            for stream_id, stream_info in self.active_streams.items():
                logger.info(f"Setting stop_event for stream ID: {stream_id}")
                stream_info["stop_event"].set()
                stream_info["task"].cancel()

            await asyncio.sleep(0.1)
            self.active_streams.clear()
            logger.info("All active streams have been stopped.")

    async def stop_stream(self, stream_id: str):
        async with self.lock:
            if stream_id not in self.active_streams:
                logger.warning(f"Attempted to stop non-existent stream ID: {stream_id}")
                return False

            logger.info(f"Stopping specific stream with ID: {stream_id}")
            stream_info = self.active_streams[stream_id]
            stream_info["stop_event"].set()
            stream_info["task"].cancel()
            await asyncio.sleep(0.1)
            if stream_id in self.active_streams:
                await self.remove_stream(stream_id)
            return True
