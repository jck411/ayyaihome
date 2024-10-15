from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import logging
import os
from openai import OpenAI  # Import OpenAI client

logger = logging.getLogger(__name__)

o1_router = APIRouter()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@o1_router.post("/api/o1")
async def o1_stream(request: Request):
    """
    Handles POST requests to the "/api/o1" endpoint using the o1-preview model.
    """
    try:
        logger.info("Received request at /api/o1")
        
        # Parse incoming JSON data from the request
        data = await request.json()
        logger.info(f"Request data: {data}")

        # Extract messages from the request
        messages = data.get('messages', [])
        logger.info(f"Messages: {messages}")

        # Send the request to the OpenAI API to generate a completion
        response = client.chat.completions.create(
            model="o1-preview",
            messages=messages
        )
        logger.info(f"Full API response: {response}")
        
        # Correct way to access content
        content = response.choices[0].message.content
        
        # Ensure code blocks are presented properly
        # This will return the message content with code blocks intact.
        return JSONResponse(content={"response": content})

    except Exception as e:
        logger.error(f"Error in o1_stream: {e}")
        return {"error": f"Unexpected error: {str(e)}"}
