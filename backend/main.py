from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
import dotenv

dotenv.load_dotenv()

from openai_service import aclient, generate_openai_response

app = FastAPI()

# Configure CORS
origins = ["http://localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.get("/")
async def root():
    logger.info("Root endpoint hit")
    return {"message": "Hello, World"}

@app.post("/api/openai")
async def openai_stream(request: Request):
    data = await request.json()
    messages = data.get('messages', [])
    logger.info(f"Received messages: {messages}")

    # Ensure each message has a role
    formatted_messages = [
        {"role": msg["sender"], "content": msg["text"]} for msg in messages
    ]
    logger.info(f"Formatted messages: {formatted_messages}")

    return StreamingResponse(generate_openai_response(formatted_messages), media_type='text/plain')

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=5000, reload=True)
