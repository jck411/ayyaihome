# backend/websocket_manager.py

from typing import Optional
from fastapi import WebSocket
import logging

# Set up logging for the module
logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        # Initialize with no active WebSocket connection
        self.active_connection: Optional[WebSocket] = None

    async def connect(self, websocket: WebSocket):
        # Close any existing active connection before accepting a new one
        if self.active_connection:
            await self.active_connection.close()
            logger.info(f"Closed previous connection: {self.active_connection.client}")
        
        # Accept the new WebSocket connection
        await websocket.accept()
        self.active_connection = websocket
        logger.info(f"Client connected: {websocket.client}")

    def disconnect(self, websocket: WebSocket):
        # Set active_connection to None if the given websocket is the active one
        if self.active_connection == websocket:
            self.active_connection = None
            logger.info(f"Client disconnected: {websocket.client}")

    async def send_audio(self, data: bytes):
        # Send audio data to the active WebSocket connection, if one exists
        if self.active_connection:
            try:
                await self.active_connection.send_bytes(data)
            except Exception as e:
                # If an error occurs, log it and remove the active connection
                self.active_connection = None
                logger.error(f"Error sending audio data: {e}. Connection removed.")
        else:
            # Log a warning if there is no active connection to send data to
            logger.warning("No active WebSocket connection to send audio.")
