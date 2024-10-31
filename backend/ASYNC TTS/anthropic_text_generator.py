# anthropic_text_generator.py

from text_generator_interface import TextGenerator
import anthropic
import asyncio
import time
import timing  # Import the timing module

class AnthropicTextGenerator(TextGenerator):
    def __init__(self, client, text_queue, text_generation_complete):
        self.client = client
        self.text_queue = text_queue
        self.text_generation_complete = text_generation_complete

    async def generate_text(self):
        # Get the prompt from the terminal asynchronously
        loop = asyncio.get_event_loop()
        user_prompt = await loop.run_in_executor(None, input, "Please enter your prompt: ")

        # Record the time when the prompt is received
        timing.prompt_received_time = time.time()

        # Prepare the messages
        messages = [{"role": "user", "content": user_prompt}]

        # Start streaming response from Claude asynchronously
        async for text in self.client.completions.stream(
            max_tokens_to_sample=1024,
            prompt=anthropic.HUMAN_PROMPT + user_prompt + anthropic.AI_PROMPT,
            model="claude-1"
        ):
            print(text, end="", flush=True)
            await self.text_queue.put(text)

        self.text_generation_complete.set()
