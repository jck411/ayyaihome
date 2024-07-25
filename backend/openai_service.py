from openai import AsyncOpenAI
import os

aclient = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def generate_openai_response(formatted_messages):
    full_content = ""
    last_chunk = None
    try:
        response = await aclient.chat.completions.create(
            model="gpt-4o-mini",
            messages=formatted_messages,
            stream=True,
            stream_options={"include_usage": True},
        )
        async for chunk in response:
            last_chunk = chunk  # Store the current chunk as the last chunk - for token count
            # print(f"Full chunk data: {chunk}") # Print the entire chunk object to the terminal

            if chunk.choices:
                delta = chunk.choices[0].delta
                if delta.content:
                    full_content += delta.content
                    yield delta.content

        # Print the last chunk after all chunks have been processed - token count
        if last_chunk:
            print(f"Last chunk data: {last_chunk}")

    except Exception as e:
        yield f"Error: {e}"
