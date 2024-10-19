from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from endpoints.openai import openai_router
from endpoints.anthropic import anthropic_router
from endpoints.o1 import o1_router 
import asyncio
import logging
from init import connection_manager, SHARED_CONSTANTS, update_audio_format, loop  # Added loop import
import json  # Added import for JSON handling
import threading
import os  # Added import for os

# Import the keyword recognition function
from services.azure_keyword_recognition import speech_recognize_keyword

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
app.include_router(o1_router)

# Set up logging for the application
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # Set the logging level to INFO

# WebSocket endpoint to handle audio connections
@app.websocket("/ws/audio")
async def audio_websocket(websocket: WebSocket):
    logger.debug("Attempting to connect Audio WebSocket.")
    
    try:
        # Call to update the audio format before establishing connection
        update_audio_format(SHARED_CONSTANTS["AUDIO_FORMAT_KEY"])  # This will dynamically update based on the format key
        
        # Attempt to connect the WebSocket
        await connection_manager.connect_audio(websocket)
        logger.info(f"WebSocket connection established: {websocket.client}")
        
        # Send Audio Format Information as Binary Message
        format_info = {
            "type": "format",
            "format": SHARED_CONSTANTS["MIME_TYPE"]  # MIME type dynamically pulled from SHARED_CONSTANTS
        }
        format_message = json.dumps(format_info).encode('utf-8')  # Encode JSON to bytes
        
        # Send the format message as a binary message over WebSocket
        await connection_manager.send_audio(format_message)
        logger.info(f"Sent audio format information: {format_info['format']}")
        
    except Exception as e:
        # Log an error if the connection fails and close the WebSocket
        logger.error(f"Failed to connect Audio WebSocket: {e}")
        await websocket.close()
        logger.debug("WebSocket closed after failed connection attempt.")
        return
    
    try:
        # Keep the connection alive by sleeping in a loop
        while True:
            logger.debug("Sleeping for 1 second in Audio WebSocket loop.")
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        # Handle WebSocket disconnection
        await connection_manager.disconnect_audio(websocket)
        logger.info(f"WebSocket connection closed: {websocket.client}")
        logger.debug("WebSocketDisconnect exception caught and connection_manager notified.")

# WebSocket Endpoint for Keyword Detection
@app.websocket("/ws/keyword")
async def keyword_websocket(websocket: WebSocket):
    logger.debug("Attempting to connect Keyword WebSocket.")
    
    try:
        # Accept the WebSocket connection
        await connection_manager.connect_keyword(websocket)
        logger.info(f"Keyword WebSocket connection established: {websocket.client}")
    except Exception as e:
        logger.error(f"Failed to connect Keyword WebSocket: {e}")
        await websocket.close()
        return
    
    try:
        # Keep the connection alive without trying to receive messages
        while True:
            await asyncio.sleep(10)  # Keep the connection alive
    except WebSocketDisconnect:
        # Handle disconnection
        await connection_manager.disconnect_keyword(websocket)
        logger.info(f"Keyword WebSocket connection closed: {websocket.client}")

# Function to run keyword recognition for a specific keyword and model
def run_keyword_recognition(keyword, model_path):
    speech_recognize_keyword(keyword, model_path)

# Startup event to initiate keyword recognition
@app.on_event("startup")
async def startup_event():
    logger.info("Starting keyword recognition in background threads.")
    
    # Define the keywords and their corresponding model file paths
    keywords = {
        "Hey Computer": "/home/jack/ayyaihome/backend/services/a8fb67d6-474d-49e0-b04b-0692a58a544f.table",
        "Hey GPT": "/home/jack/ayyaihome/backend/services/HeyGPT-tune/b8b52781-97c8-4283-85cd-2cb0d28de71f.table",
        "Hey Claude": "/home/jack/ayyaihome/backend/services/HeyClaude-tune/0e798dbb-41a6-47b9-9d9c-6a9a56f79314.table"
    }

    # Initialize and start a thread for each keyword
    for keyword, model_path in keywords.items():
        if not os.path.exists(model_path):
            logger.error(f"Keyword model file not found for '{keyword}' at {model_path}")
            continue
        thread = threading.Thread(target=run_keyword_recognition, args=(keyword, model_path), daemon=True)
        thread.start()
        logger.info(f"Started keyword recognizer for '{keyword}' in thread {thread.name}.")

# Entry point for running the application with Uvicorn
if __name__ == '__main__':
    import uvicorn
    logger.debug("Starting the Uvicorn server.")
    uvicorn.run(app, host='0.0.0.0', port=8000)  # Run the server on all available IP addresses, port 8000
