# openai_text_generator.py

import time
import timing
import asyncio
import logging

logger = logging.getLogger(__name__)

class OpenAITextGenerator:
    def __init__(self, aclient, text_queue, text_generation_complete):
        self.aclient = aclient  # Use aclient as the async client
        self.text_queue = text_queue
        self.text_generation_complete = text_generation_complete

    async def generate_text(self):
        loop = asyncio.get_event_loop()
        user_prompt = await loop.run_in_executor(None, input, "Please enter your prompt: ")

        timing.prompt_received_time = time.time()

        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": user_prompt}
        ]

        OPENAI_CONSTANTS = {
            "MODEL": "gpt-4o-mini",
            "STREAM": True,
            "TEMPERATURE": 0.7,
            "TOP_P": 1.0,
            "MAX_TOKENS": 1024,
            "FREQUENCY_PENALTY": 0.0,
            "PRESENCE_PENALTY": 0.0,
            "STOP": None,
            "LOGIT_BIAS": {}
        }

        try:
            logger.info("Starting stream from OpenAI API")

            # Offload the blocking OpenAI API call to a separate thread
            response = await loop.run_in_executor(
                None,
                lambda: self.aclient.chat.completions.create(
                    model=OPENAI_CONSTANTS["MODEL"],
                    messages=messages,
                    stream=OPENAI_CONSTANTS["STREAM"],
                    temperature=OPENAI_CONSTANTS["TEMPERATURE"],
                    top_p=OPENAI_CONSTANTS["TOP_P"],
                    max_tokens=OPENAI_CONSTANTS["MAX_TOKENS"],
                    frequency_penalty=OPENAI_CONSTANTS["FREQUENCY_PENALTY"],
                    presence_penalty=OPENAI_CONSTANTS["PRESENCE_PENALTY"],
                    stop=OPENAI_CONSTANTS["STOP"],
                    logit_bias=OPENAI_CONSTANTS["LOGIT_BIAS"]
                )
            )

            working_string = ""
            async for chunk in self._async_stream_response(response):
                content = getattr(chunk.choices[0].delta, 'content', "") if chunk.choices else ""
                if content:
                    print(content, end="", flush=True)
                    await self.text_queue.put(content)
                    working_string += content

            logger.info(f"Full response accumulated: {working_string}")
            self.text_generation_complete.set()

        except Exception as e:
            logger.error(f"Error in generate_text: {e}")
            self.text_generation_complete.set()

    async def _async_stream_response(self, response):
        # Helper async generator to iterate over the synchronous response
        for chunk in response:
            yield chunk
            await asyncio.sleep(0)  # Yield control to the event loop
