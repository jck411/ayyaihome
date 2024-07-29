import asyncio
import openai
from functools import reduce
from typing import Callable, AsyncGenerator, List
import os
import threading
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Constants
DELIMITERS = [f"{d} " for d in (".", "?", "!")]
MINIMUM_PHRASE_LENGTH = 200
DEFAULT_RESPONSE_MODEL = "gpt-3.5-turbo"

# Initialize OpenAI client
aclient = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Define global stop event
stop_event = threading.Event()

async def stream_delimited_completion(
    messages: List[dict],
    client: openai.AsyncOpenAI = aclient,
    model: str = DEFAULT_RESPONSE_MODEL,
    content_transformers: List[Callable[[str], str]] = [],
    phrase_transformers: List[Callable[[str], str]] = [],
    delimiters: List[str] = DELIMITERS,
) -> AsyncGenerator[str, None]:
    """Generates delimited phrases from OpenAI's chat completions."""

    def apply_transformers(s: str, transformers: List[Callable[[str], str]]) -> str:
        return reduce(lambda c, transformer: transformer(c), transformers, s)

    working_string = ""
    response = await client.chat_completions.create(
        messages=messages, model=model, stream=True
    )
    async for chunk in response:
        if stop_event.is_set():
            yield None
            return

        content = chunk.choices[0].delta.content or ""
        if content:
            working_string += apply_transformers(content, content_transformers)
            while len(working_string) >= MINIMUM_PHRASE_LENGTH:
                delimiter_index = -1
                for delimiter in delimiters:
                    index = working_string.find(delimiter, MINIMUM_PHRASE_LENGTH)
                    if index != -1 and (
                        delimiter_index == -1 or index < delimiter_index
                    ):
                        delimiter_index = index

                if delimiter_index == -1:
                    break

                phrase, working_string = (
                    working_string[: delimiter_index + len(delimiter)],
                    working_string[delimiter_index + len(delimiter) :],
                )
                yield apply_transformers(phrase, phrase_transformers)

    if working_string.strip():
        yield working_string.strip()

    yield None  # Sentinel value to signal "no more coming"

async def test_stream_delimited_completion():
    test_messages = [
        {"role": "user", "content": "Explain the theory of relativity."}
    ]
    async for phrase in stream_delimited_completion(test_messages):
        if phrase is None:
            break
        print(phrase)

# Run the test function
if __name__ == "__main__":
    asyncio.run(test_stream_delimited_completion())
