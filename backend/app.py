from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from endpoints.openai import openai_router
from endpoints.stop import stop_router
from endpoints.anthropic import anthropic_router  # Import the new router

# Initialize the FastAPI app
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Adjust this based on your frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(openai_router)
app.include_router(stop_router)
app.include_router(anthropic_router)  # Include the new Anthropomorphic router

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)