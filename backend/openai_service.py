from openai import AsyncOpenAI
import os
import logging

aclient = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Configure logging
logger = logging.getLogger(__name__)

async def generate_openai_response(formatted_messages):
    total_tokens = 0
    try:
        response = await aclient.chat.completions.create(
            model="gpt-4o-mini",
            messages=formatted_messages,
            stream=True
        )
        async for chunk in response:
            logger.info(f"Chunk received: {chunk}")  # Log entire chunk
            choice = chunk.choices[0].delta
            content = choice.content if choice else None
            if content:
                logger.info(f"Streaming content: {content}")
                yield content

            # Check for token usage in the last chunk
            if 'usage' in chunk:
                total_tokens = chunk.usage.total_tokens

        # Log the total tokens used and estimated cost at the end of the response
        logger.info(f"Total tokens used: {total_tokens}")
        cost_per_token = 0.00006  # Example cost per token
        total_cost = total_tokens * cost_per_token
        logger.info(f"Estimated cost: ${total_cost:.4f}")

    except Exception as e:
        logger.error(f"Error during OpenAI API call: {e}")
        yield f"Error: {e}"
