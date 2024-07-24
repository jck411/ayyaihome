from openai import AsyncOpenAI
import os

aclient = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def generate_openai_response(formatted_messages):
    full_content = ""
    try:
        response = await aclient.chat.completions.create(
            model="gpt-4o-mini",
            messages=formatted_messages,
            stream=True,
            stream_options={"include_usage": True}, 
        )
        async for chunk in response:
            if chunk.choices:
                delta = chunk.choices[0].delta
                if delta.content:
                    full_content += delta.content
                    yield delta.content
                if chunk.choices[0].finish_reason == 'stop':
                    break

    except Exception as e:
        yield f"Error: {e}"

    yield full_content
