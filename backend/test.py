from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from openai import AsyncOpenAI
import os
import dotenv
import logging

dotenv.load_dotenv()

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

aclient = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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

    async def generate():
        try:
            response = await aclient.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=formatted_messages,
                stream=True
            )
            async for chunk in response:
                choice = chunk.choices[0].delta
                content = choice.content if choice else None
                if content:
                    logger.info(f"Streaming content: {content}")
                    yield content
        except Exception as e:
            logger.error(f"Error during OpenAI API call: {e}")
            yield f"Error: {e}"

    return StreamingResponse(generate(), media_type='text/plain')

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=5000, reload=True)
