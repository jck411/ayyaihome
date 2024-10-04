from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
import asyncio
import queue
from init import ANTHROPIC_CONSTANTS, anthropic_client
from services.tts_service import process_streams
from services.audio_player import find_next_phrase_end

anthropic_router = APIRouter()

@anthropic_router.post("/api/anthropic")
async def anthropic_chat(request: Request):
    """
    Handles POST requests to the "/api/anthropic" endpoint.
    """
    print("Received request")

    try:
        # Parse incoming data
        data = await request.json()
        print(f"Parsed request data: {data}")
        messages = [{"role": msg["role"], "content": msg["content"]} for msg in data.get('messages', [])]

        if not messages:
            print("No messages found in the request")
            return {"error": "Prompt is required."}

        tts_enabled = data.get('ttsEnabled', True)  # Get TTS enabled state from the request
        print(f"TTS Enabled: {tts_enabled}")

        # Initialize phrase queue only if TTS is enabled
        phrase_queue = None
        if tts_enabled:
            phrase_queue = asyncio.Queue()
            audio_queue = queue.Queue()  # Synchronous queue for audio processing

            # Start TTS processing in the background
            print("Starting TTS processing")
            asyncio.create_task(process_streams(phrase_queue, audio_queue, ANTHROPIC_CONSTANTS))

        # Stream response back to the client
        response = StreamingResponse(
            stream_completion(messages, phrase_queue),
            media_type='text/plain'
        )
        print("Sending response with streaming content")
        return response

    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return {"error": f"Unexpected error: {str(e)}"}


async def stream_completion(messages: list, phrase_queue: asyncio.Queue):
    """
    Streams the response from the Anthropic API.
    """
    try:
        # Request the response from the Anthropic API with the top-level system prompt
        print("Starting to stream completion from Anthropic API")
        async with anthropic_client.messages.stream(
            model=ANTHROPIC_CONSTANTS["DEFAULT_RESPONSE_MODEL"],
            messages=messages,
            max_tokens=1024,
            temperature=ANTHROPIC_CONSTANTS["TEMPERATURE"],
            system=ANTHROPIC_CONSTANTS["SYSTEM_PROMPT"]["content"]  # Top-level system prompt parameter
        ) as stream:
            working_string = ""  # Accumulates the full response
            in_code_block = False  # Track whether we're inside a code block

            # Stream the response chunks as they arrive
            async for chunk in stream.text_stream:
                content = chunk or ""
                if content:
                    print(f"Received chunk: {content}")
                    yield content
                    working_string += content

                    # Process phrases
                    while True:
                        if in_code_block:
                            code_block_end = working_string.find("```", 3)
                            if code_block_end != -1:
                                working_string = working_string[code_block_end + 3:]
                                if phrase_queue:
                                    await phrase_queue.put("Code presented on screen")
                                in_code_block = False
                            else:
                                break
                        else:
                            code_block_start = working_string.find("```")
                            if code_block_start != -1:
                                phrase, working_string = working_string[:code_block_start], working_string[code_block_start:]
                                if phrase.strip() and phrase_queue:
                                    await phrase_queue.put(phrase.strip())
                                in_code_block = True
                            else:
                                next_phrase_end = find_next_phrase_end(working_string)
                                if next_phrase_end == -1:
                                    break
                                phrase, working_string = working_string[:next_phrase_end + 1].strip(), working_string[next_phrase_end + 1:]
                                if phrase_queue and phrase:
                                    await phrase_queue.put(phrase)

            # Process any remaining text after streaming ends
            while working_string:
                if in_code_block:
                    code_block_end = working_string.find("```", 3)
                    if code_block_end != -1:
                        working_string = working_string[code_block_end + 3:]
                        if phrase_queue:
                            await phrase_queue.put("Code presented on screen")
                        in_code_block = False
                    else:
                        break
                else:
                    code_block_start = working_string.find("```")
                    if code_block_start != -1:
                        phrase, working_string = working_string[:code_block_start], working_string[code_block_start:]
                        if phrase.strip() and phrase_queue:
                            await phrase_queue.put(phrase.strip())
                        in_code_block = True
                    else:
                        if working_string.strip() and phrase_queue:
                            await phrase_queue.put(working_string.strip())
                        working_string = ''

            # End the TTS processing
            if phrase_queue:
                print("Ending TTS processing")
                await phrase_queue.put(None)

    except Exception as e:
        print(f"Error during streaming: {str(e)}")
        if phrase_queue:
            await phrase_queue.put(None)
        yield f"Error: {e}"
