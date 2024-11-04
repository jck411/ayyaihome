# services/ai_services.py

import asyncio
import logging
from typing import List, AsyncIterator

from openai import AsyncOpenAI

from abc_classes import AIService
from config import Config
from utils import find_next_phrase_end


logger = logging.getLogger(__name__)

class OpenAIService(AIService):
    def __init__(self, api_key: str, config: Config):
        self.client = AsyncOpenAI(api_key=api_key)
        self.config = config

    async def stream_completion(
        self, 
        messages: List[dict], 
        phrase_queue: asyncio.Queue, 
        stop_event: asyncio.Event, 
        stream_id: str
    ) -> AsyncIterator[str]:
        try:
            response = await self.client.chat.completions.create(
                model=self.config.ai_service.DEFAULT_RESPONSE_MODEL,
                messages=messages,
                stream=True,
                temperature=self.config.ai_service.TEMPERATURE,
                top_p=self.config.ai_service.TOP_P,
                frequency_penalty=self.config.ai_service.FREQUENCY_PENALTY,
                presence_penalty=self.config.ai_service.PRESENCE_PENALTY,
                max_tokens=self.config.ai_service.MAX_TOKENS,
                stop=self.config.ai_service.STOP,
                logit_bias=self.config.ai_service.LOGIT_BIAS,
            )

            working_string, in_code_block = "", False
            async for chunk in response:
                if stop_event.is_set():
                    logger.info(f"Stop event set for stream ID: {stream_id}. Terminating stream_completion.")
                    await phrase_queue.put(None)
                    break

                content = getattr(chunk.choices[0].delta, 'content', "") if chunk.choices else ""
                if content:
                    yield content
                    working_string += content

                    while True:
                        if in_code_block:
                            code_block_end = working_string.find("\n```", 3)
                            if code_block_end != -1:
                                working_string = working_string[code_block_end + 3:]
                                await phrase_queue.put("Code presented on screen")
                                in_code_block = False
                            else:
                                break
                        else:
                            code_block_start = working_string.find("```")
                            if code_block_start != -1:
                                phrase, working_string = working_string[:code_block_start], working_string[code_block_start:]
                                if phrase.strip():
                                    await phrase_queue.put(phrase.strip())
                                in_code_block = True
                            else:
                                next_phrase_end = find_next_phrase_end(working_string, self.config)
                                if next_phrase_end == -1:
                                    break
                                phrase, working_string = working_string[:next_phrase_end + 1].strip(), working_string[next_phrase_end + 1:]
                                await phrase_queue.put(phrase)

            if working_string.strip() and not in_code_block:
                logger.info(f"Final working_string for stream ID {stream_id}: {working_string.strip()}")
                await phrase_queue.put(working_string.strip())
            await phrase_queue.put(None)

        except Exception as e:
            logger.error(f"Error in stream_completion (Stream ID: {stream_id}): {e}")
            await phrase_queue.put(None)
            yield f"Error: {e}"

        finally:
            logger.info(f"Stream completion ended for stream ID: {stream_id}")
