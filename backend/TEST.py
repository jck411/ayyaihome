import asyncio
import os
from openai import AsyncOpenAI

async def main():
    # Initialize the asynchronous OpenAI client
    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # Define the messages for the chat completion
    messages = [
        {"role": "user", 
         "content": "say some shiz"}    
    ]

    try:
        # Create a chat completion with streaming enabled
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            stream=True
        )

        # Collect all streamed content for TTS input
        collected_content = ""
        async for chunk in response:
            # Access content directly as an attribute
            content = chunk.choices[0].delta.content
            if content:
                collected_content += content
                print(content, end='', flush=True)

        # Generate TTS audio from the collected content
        if collected_content:
            with client.audio.speech.with_streaming_response.create(
                model="tts-1",
                voice="alloy",
                input=collected_content
            ) as tts_response:
                with open("output_audio.wav", 'wb') as f:
                    for chunk in tts_response.iter_bytes():
                        f.write(chunk)

    except Exception as e:
        print(f"An error occurred: {e}")

# Run the async main function
asyncio.run(main())
