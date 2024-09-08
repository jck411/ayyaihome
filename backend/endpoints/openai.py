from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
import asyncio
import queue
from init import stop_event, CONSTANTS, aclient
from services.tts_service_openai import process_streams # Import process_streams from tts_service
# Correct the import based on where find_next_phrase_end is located
from services.audio_player import find_next_phrase_end  # Adjust this if necessary

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
    
    data = await request.json()
    messages = [{"role": msg["sender"], "content": msg["text"]} for msg in data.get('messages', [])]
    messages.insert(0, CONSTANTS["SYSTEM_PROMPT"])
    
    phrase_queue, audio_queue = asyncio.Queue(), queue.Queue()
    asyncio.create_task(process_streams(phrase_queue, audio_queue))
    
    return StreamingResponse(stream_completion(messages, phrase_queue), media_type='text/plain')

async def stream_completion(messages: list, phrase_queue: asyncio.Queue, model: str = CONSTANTS["DEFAULT_RESPONSE_MODEL"]):
    """
    Streams the response from the OpenAI API.
    Processes each chunk of the response, adds it to the phrase queue for text-to-speech conversion, 
    and streams the content back to the client.
    """
    try:
        response = await aclient.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
            temperature=CONSTANTS["TEMPERATURE"],
            top_p=CONSTANTS["TOP_P"],
        )
        
        working_string = ""
        in_code_block = False
        
        async for chunk in response:
            if stop_event.is_set():
                await phrase_queue.put(None)
                break

            content = ""
            if chunk.choices and hasattr(chunk.choices[0].delta, 'content'):
                content = chunk.choices[0].delta.content or ""
            
            if content:
                yield content
                working_string += content
                
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
        
        if working_string.strip() and not in_code_block:
            await phrase_queue.put(working_string.strip())
        
        await phrase_queue.put(None)
    
    except Exception as e:
        print(f"Error in stream_completion: {e}")
        await phrase_queue.put(None)
        yield f"Error: {e}"