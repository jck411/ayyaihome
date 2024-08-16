import threading
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
import anthropic
import asyncio

# Load environment variables from .env
load_dotenv()

# Global stop event
stop_event = threading.Event()

# Initialize FastAPI app
app = FastAPI()

# Add CORS middleware to allow requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Adjust to your frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the Anthropic client
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

@app.post("/api/anthropic")
async def anthropic_chat(request: Request):
    data = await request.json()
    messages = data.get('messages', [])

    if not messages:
        return {"error": "Prompt is required."}

    # Validate and correct the sequence of messages
    validated_messages = []
    last_role = None
    for msg in messages:
        role = msg.get("role")
        if role not in ["user", "assistant"]:
            return {"error": f"Invalid role: {role}"}

        # Ensure roles alternate between "user" and "assistant"
        if role == last_role:
            return {"error": 'Messages roles must alternate between "user" and "assistant"'}
        
        validated_messages.append(msg)
        last_role = role

    # Prepare the message for the Anthropic API
    def response_stream():
        try:
            with client.messages.stream(
                max_tokens=1024,
                temperature=0.7,
                messages=validated_messages,  # Use the validated messages array
                model="claude-3-5-sonnet-20240620",  # Use the appropriate model
            ) as stream:
                for text in stream.text_stream:
                    if stop_event.is_set():  # Stop if a stop signal is triggered
                        break
                    yield text
        except Exception as e:
            yield f"Error: {e}"

    return StreamingResponse(response_stream(), media_type='text/plain')

@app.post("/api/stop")
async def stop_processing():
    """
    Endpoint to stop any ongoing processing gracefully.
    Triggered by a specific user action (like pressing enter).
    """
    stop_event.set()
    return {"status": "Stopping"}

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
