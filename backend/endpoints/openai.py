from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
import asyncio
import queue
from init import stop_event, OPENAI_CONSTANTS, aclient
from services.tts_service import process_streams
from services.audio_player import find_next_phrase_end

# Define the router for OpenAI-related endpoints
openai_router = APIRouter()

@openai_router.post("/api/openai")
async def openai_stream(request: Request):
    """
    Handles POST requests to the "/api/openai" endpoint.
    Processes user input, sends it to the OpenAI API for response generation, and streams the output back.
    """
    stop_event.set()
    await asyncio.sleep(0.1)
    stop_event.clear()

    try:
        # Parse incoming data
        data = await request.json()

        # Adjust to handle "role" and "content"
        messages = [{"role": msg["role"], "content": msg["content"]} for msg in data.get('messages', [])]
        messages.insert(0, OPENAI_CONSTANTS["SYSTEM_PROMPT"])  # Add system prompt

        # Initialize queues for TTS processing
        phrase_queue, audio_queue = asyncio.Queue(), queue.Queue()

        # Use OpenAI TTS service with OpenAI-specific constants
        asyncio.create_task(process_streams(phrase_queue, audio_queue, OPENAI_CONSTANTS))

        return StreamingResponse(stream_completion(messages, phrase_queue), media_type='text/plain')

    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}

async def stream_completion(messages: list, phrase_queue: asyncio.Queue, model: str = OPENAI_CONSTANTS["DEFAULT_RESPONSE_MODEL"]):
    """
    Streams the response from the OpenAI API.
    Processes each chunk of the response, adds it to the phrase queue for text-to-speech conversion,
    and streams the content back to the client.
    """
    try:
        # Send the request to OpenAI API
        response = await aclient.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
            temperature=OPENAI_CONSTANTS["TEMPERATURE"],
            top_p=OPENAI_CONSTANTS["TOP_P"],
        )

        working_string = ""
        in_code_block = False

        async for chunk in response:
            if stop_event.is_set():
                await phrase_queue.put(None)
                break

            # Get the content from the response chunk
            content = ""
            if chunk.choices and hasattr(chunk.choices[0].delta, 'content'):
                content = chunk.choices[0].delta.content or ""

            if content:
                yield content  # Stream content back to the client
                working_string += content

                # Check for code blocks and regular text
                while True:
                    code_block_start = working_string.find("```")

                    if in_code_block:
                        code_block_end = working_string.find("```", 3)
                        if code_block_end != -1:
                            working_string = working_string[code_block_end + 3:]
                            await phrase_queue.put("Code presented on screen")
                            in_code_block = False
                        else:
                            break
                    else:
                        if code_block_start != -1:
                            phrase, working_string = working_string[:code_block_start], working_string[code_block_start:]
                            if phrase.strip():
                                await phrase_queue.put(phrase.strip())
                            in_code_block = True
                        else:
                            next_phrase_end = find_next_phrase_end(working_string)
                            if next_phrase_end == -1:
                                break
                            phrase, working_string = working_string[:next_phrase_end + 1].strip(), working_string[next_phrase_end + 1:]
                            await phrase_queue.put(phrase)

        # Final text after streaming
        if working_string.strip() and not in_code_block:
            await phrase_queue.put(working_string.strip())

        # End of TTS
        await phrase_queue.put(None)

    except Exception as e:
        print(f"Error in stream_completion: {e}")
        await phrase_queue.put(None)
        yield f"Error: {e}"
