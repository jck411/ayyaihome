#/home/jack/ayyaihome/backend/app.py

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from endpoints.openai import openai_router
from endpoints.anthropic import anthropic_router
import asyncio
import logging
from init import connection_manager, SHARED_CONSTANTS, update_audio_format  # Added update_audio_format import
import json  # Added import for JSON handling

# Initialize the FastAPI app
app = FastAPI()

# Add CORS middleware to handle cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Adjust this if needed to allow requests from specific origins
    allow_credentials=True,  # Allow credentials such as cookies or authorization headers
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
    expose_headers=["X-Request-ID"],  # Expose custom headers to the client
)

# Include routers for different endpoints
app.include_router(openai_router)  # Router for OpenAI-related endpoints
app.include_router(anthropic_router)  # Router for Anthropic-related endpoints

# Set up logging for the application
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # Set the logging level to INFO

# WebSocket endpoint to handle audio connections
@app.websocket("/ws/audio")
async def audio_websocket(websocket: WebSocket):
    logger.debug("Attempting to connect WebSocket.")
    
    try:
        # **Call to update the audio format before establishing connection** #THIS IS WHERE YOU CHANGE THE FORMAT FOR AUDIO
        update_audio_format("ogg-opus")  # Change to "mp3", "aac", or "ogg-opus" as needed
        
        # Attempt to connect the WebSocket
        await connection_manager.connect(websocket)
        logger.info(f"WebSocket connection established: {websocket.client}")
        
        # **Begin Modification: Send Audio Format Information as Binary Message**
        # Create a JSON message with the audio format
        format_info = {
            "type": "format",
            "format": SHARED_CONSTANTS.get("MIME_TYPE", "audio/mpeg")  # Default to 'audio/mpeg' if MIME_TYPE not set
        }
        format_message = json.dumps(format_info).encode('utf-8')  # Encode JSON to bytes
        
        # Send the format message as a binary message over WebSocket
        await connection_manager.send_audio(format_message)
        logger.info(f"Sent audio format information: {format_info['format']}")
        # **End Modification**
        
    except Exception as e:
        # Log an error if the connection fails and close the WebSocket
        logger.error(f"Failed to connect WebSocket: {e}")
        await websocket.close()
        logger.debug("WebSocket closed after failed connection attempt.")
        return
    
    try:
        # Keep the connection alive by sleeping in a loop
        while True:
            logger.debug("Sleeping for 1 second in WebSocket loop.")
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        # Handle WebSocket disconnection
        connection_manager.disconnect(websocket)
        logger.info(f"WebSocket connection closed: {websocket.client}")
        logger.debug("WebSocketDisconnect exception caught and connection_manager notified.")

# Entry point for running the application with Uvicorn
if __name__ == '__main__':
    import uvicorn
    logger.debug("Starting the Uvicorn server.")
    uvicorn.run(app, host='0.0.0.0', port=8000)  # Run the server on all available IP addresses, port 8000
