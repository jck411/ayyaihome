# /home/jack/ayyaihome/backend/app.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from endpoints.openai import openai_router
from endpoints.anthropic import anthropic_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Adjust based on your frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(openai_router)
app.include_router(anthropic_router)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
