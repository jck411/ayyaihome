from openai import AsyncOpenAI
import os
import asyncio
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# Initialize the AsyncOpenAI client
aclient = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def test_aclose():
    # Start a streaming request
    stream = await aclient.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is streaming?"}
        ],
        stream=True
    )

    try:
        # Process the stream asynchronously
        async for chunk in stream:
            # Access the content directly
            print(chunk.choices[0].delta.content, end="")
    finally:
        # Explicitly close the stream
        await stream.close()

# Run the async function
asyncio.run(test_aclose())
