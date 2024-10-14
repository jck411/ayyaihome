# /home/jack/ayyaihome/backend/websocket_manager.py

import json  # Add this import for JSON handling
from typing import Optional
from fastapi import WebSocket
import logging
import asyncio

# Set up logging for the module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # Ensure INFO level logs are captured

class ConnectionManager:
    def __init__(self):
        # Initialize with no active WebSocket connections
        self.active_audio_connection: Optional[WebSocket] = None
        self.active_keyword_connection: Optional[WebSocket] = None
        # Locks to ensure thread-safe access
        self.audio_lock = asyncio.Lock()
        self.keyword_lock = asyncio.Lock()

    async def connect_audio(self, websocket: WebSocket):
        async with self.audio_lock:
            # Close any existing active audio connection before accepting a new one
            if self.active_audio_connection:
                await self.active_audio_connection.close()
                logger.info(f"Closed previous audio connection: {self.active_audio_connection.client}")
    
            # Accept the new WebSocket connection
            await websocket.accept()
            self.active_audio_connection = websocket
            logger.info(f"Audio Client connected: {websocket.client}")

    async def connect_keyword(self, websocket: WebSocket):
        async with self.keyword_lock:
            # Close any existing active keyword connection before accepting a new one
            if self.active_keyword_connection:
                await self.active_keyword_connection.close()
                logger.info(f"Closed previous keyword connection: {self.active_keyword_connection.client}")
    
            # Accept the new WebSocket connection
            await websocket.accept()
            self.active_keyword_connection = websocket
            logger.info(f"Keyword Client connected: {websocket.client}")

    async def disconnect_audio(self, websocket: WebSocket):
        async with self.audio_lock:
            # Set active_audio_connection to None if the given websocket is the active one
            if self.active_audio_connection == websocket:
                self.active_audio_connection = None
                logger.info(f"Audio Client disconnected: {websocket.client}")

    async def disconnect_keyword(self, websocket: WebSocket):
        async with self.keyword_lock:
            # Set active_keyword_connection to None if the given websocket is the active one
            if self.active_keyword_connection == websocket:
                self.active_keyword_connection = None
                logger.info(f"Keyword Client disconnected: {websocket.client}")

    async def send_audio(self, data: bytes):
        # Send audio data to the active audio WebSocket connection, if one exists
        async with self.audio_lock:
            if self.active_audio_connection:
                try:
                    await self.active_audio_connection.send_bytes(data)
                    logger.info("Audio data sent to client.")
                except Exception as e:
                    # If an error occurs, log it and remove the active connection
                    logger.error(f"Error sending audio data: {e}. Audio connection removed.")
                    self.active_audio_connection = None
            else:
                # Log a warning if there is no active connection to send data to
                logger.warning("No active audio WebSocket connection to send audio.")

    async def send_keyword(self, message: dict):
        # Send keyword message to the active keyword WebSocket connection, if one exists
        async with self.keyword_lock:
            if self.active_keyword_connection:
                try:
                    # Convert the message dictionary to a JSON string
                    json_message = json.dumps(message)
                    logger.info(f"Attempting to send keyword message: {json_message}")
                    await self.active_keyword_connection.send_text(json_message)
                    logger.info("Keyword message sent to client.")
                except Exception as e:
                    # If an error occurs, log it and remove the active connection
                    logger.error(f"Error sending keyword message: {e}. Keyword connection removed.")
                    self.active_keyword_connection = None
            else:
                # Log a warning if there is no active connection to send keyword message
                logger.warning("No active keyword WebSocket connection to send keyword message.")
