from fastapi import Request
from backend.config import Config

async def validate_and_prepare_for_openai_completion(request: Request):
    """
    Validates the incoming request and prepares messages for OpenAI completion.
    """
    data = await request.json()
    messages = data.get('messages', [])
    
    if not isinstance(messages, list):
        raise ValueError("Messages must be a list.")
    
    prepared_messages = [{"role": msg["sender"], "content": msg["text"]} for msg in messages]
    system_prompt = {"role": "system", "content": Config.SYSTEM_PROMPT_CONTENT}
    prepared_messages.insert(0, system_prompt)
    
    return prepared_messages
