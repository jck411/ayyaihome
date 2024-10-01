# /home/jack/ayyaihome/backend/endpoints/stop.py

from fastapi import APIRouter, Request
from stop_events import stop_events  # Import stop_events from the new module

stop_router = APIRouter()

@stop_router.post("/api/stop")
async def stop_tts(request: Request):
    """
    Handles requests to stop TTS processing for a specific request.
    """
    data = await request.json()
    request_id = data.get('request_id')
    if request_id and request_id in stop_events:
        stop_events[request_id].set()
        del stop_events[request_id]  # Remove the stop event after setting it
        return {"status": f"Stopping request {request_id}"}
    else:
        return {"error": "Invalid request ID"}
