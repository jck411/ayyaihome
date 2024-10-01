# /home/jack/ayyaihome/backend/websocket_manager.py

from typing import Optional
from fastapi import WebSocket
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connection: Optional[WebSocket] = None

    async def connect(self, websocket: WebSocket):
        if self.active_connection:
            await self.active_connection.close()
            logger.info(f"Closed previous connection: {self.active_connection.client}")
        await websocket.accept()
        self.active_connection = websocket
        logger.info(f"Client connected: {websocket.client}")

    def disconnect(self, websocket: WebSocket):
        if self.active_connection == websocket:
            self.active_connection = None
            logger.info(f"Client disconnected: {websocket.client}")

    async def send_audio(self, data: bytes):
        if self.active_connection:
            try:
                await self.active_connection.send_bytes(data)
            except Exception as e:
                self.active_connection = None
                logger.error(f"Error sending audio data: {e}. Connection removed.")
        else:
            logger.warning("No active WebSocket connection to send audio.")
