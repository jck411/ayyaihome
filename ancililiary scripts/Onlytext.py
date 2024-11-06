import os
import asyncio
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from openai import AsyncOpenAI
import logging

# Load environment variables from a .env file
load_dotenv()

logger = logging.getLogger(__name__)

# Initialize FastAPI app and OpenAI client
app = FastAPI()
aclient = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# CORS settings for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/openai")
async def openai_stream(request: Request):
    data = await request.json()
    messages = [{"role": msg["sender"], "content": msg["text"]} for msg in data.get("messages", [])]
    messages.insert(0, {"role": "system", "content": "You are a helpful assistant."})

    return StreamingResponse(
        stream_completion(messages),
        media_type="text/plain"
    )

@app.post("/api/stop")
async def stop_tts():
    # This endpoint is not implemented in this version, but can be added later if needed
    return {"status": "Stopping"}

async def stream_completion(messages: list):
    try:
        response = await aclient.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            stream=True,
        )

        async for chunk in response:
            content = getattr(chunk.choices[0].delta, 'content', "")
            if content:
                yield content

    except Exception as e:
        logger.error(f"Error in stream_completion: {e}")
        yield f"Error: {e}"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("Onlytext:app", host="0.0.0.0", port=8000, reload=True)