import asyncio
import os
import google.generativeai as genai

async def main():
    # Configure the SDK with your API key
    api_key = os.getenv("GEMINI_API_KEY")  # Ensure your API key is set in the environment variables
    genai.configure(api_key=api_key)

    # Initialize the model
    model = genai.GenerativeModel("gemini-1.5-flash")

    # Define a system prompt
    system_prompt = "You are a helpful assistant who writes creative and engaging stories for children."

    # Combine the system prompt and user input
    user_input = "Write a story about a magic backpack."
    complete_prompt = f"{system_prompt}\n\n{user_input}"

    # Generate content asynchronously with the system prompt
    response = await model.generate_content_async(complete_prompt, stream=True)

    # Process the streamed response
    async for chunk in response:
        print(chunk.text)
        print("_" * 80)

if __name__ == "__main__":
    asyncio.run(main())
