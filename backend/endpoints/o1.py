from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse
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
    Expects plain text input and returns plain text output.
    """
    try:
        logger.info("Received request at /api/o1")
        
        # Read the raw text data from the request body
        input_text = await request.body()
        input_text = input_text.decode('utf-8')
        logger.info(f"Input text: {input_text}")

        # Create a message structure for OpenAI API
        messages = [{"role": "user", "content": input_text}]

        # Send the request to the OpenAI API to generate a completion
        response = client.chat.completions.create(
            model="o1-preview",
            messages=messages
        )
        logger.info(f"Full API response: {response}")
        
        # Correct way to access content
        content = response.choices[0].message.content
        
        # Return the response as plain text
        return PlainTextResponse(content=content)

    except Exception as error:
        logger.error(f"Error in o1_stream: {error}")
        return PlainTextResponse(content=f"Unexpected error: {str(error)}", status_code=500)
