# /home/jack/ayyaihome/backend/app.py

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from endpoints.openai import openai_router
from endpoints.stop import stop_router
from endpoints.anthropic import anthropic_router
import asyncio
import logging
from init import connection_manager

# Initialize the FastAPI app
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Adjust this if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],  # Expose custom headers
)

# Include routers
app.include_router(openai_router)
app.include_router(stop_router)
app.include_router(anthropic_router)

# Set up logging
logger = logging.getLogger(__name__)

@app.websocket("/ws/audio")
async def audio_websocket(websocket: WebSocket):
    await connection_manager.connect(websocket)
    logger.info(f"WebSocket connection established: {websocket.client}")
    try:
        while True:
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)
        logger.info(f"WebSocket connection closed: {websocket.client}")

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
