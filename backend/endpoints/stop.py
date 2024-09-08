from fastapi import APIRouter  # Import FastAPI's APIRouter to define a route for the stop event
from init import stop_event  # Import stop_event from the init module, used to signal stopping the TTS service

# Create a new router for the stop endpoint
stop_router = APIRouter()

# Define an endpoint to handle POST requests to "/api/stop"
@stop_router.post("/api/stop")
async def stop_tts():
    """
    This function handles requests to stop the TTS (Text-to-Speech) service.
    When a POST request is sent to this endpoint, it triggers the stop_event,
    which signals other processes to stop their execution.
    """
    stop_event.set()  # Set the stop_event, signaling to other components to stop (e.g., halting TTS or audio playback)
    return {"status": "Stopping"}  # Return a JSON response indicating that the stop command was issued
