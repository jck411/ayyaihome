#/home/jack/ayyaihome/backend/app.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from endpoints.chat import chat_router  # Import the unified chat router
from services import stt_service  # Import the STT service

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000"  # Ensure both origins are allowed
    ],  # Adjust based on your frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the unified chat router with the "/ws" prefix
app.include_router(chat_router, prefix="/ws")

# Now you have imported stt_service, but its actual usage will likely happen in chat_router.

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
