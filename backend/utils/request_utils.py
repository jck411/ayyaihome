from fastapi import Request

async def validate_and_prepare_for_openai_completion(request: Request):
    """
    Validates the incoming request and prepares messages for OpenAI completion.
    """
    data = await request.json()
    messages = data.get('messages', [])
    
    if not isinstance(messages, list):
        raise ValueError("Messages must be a list.")
    
    # Convert messages to the OpenAI format
    prepared_messages = [{"role": msg["sender"], "content": msg["text"]} for msg in messages]
    # Insert the system prompt at the start
    system_prompt = {"role": "system", "content": "You are a helpful assistant"}
    prepared_messages.insert(0, system_prompt)
    
    return prepared_messages


async def validate_and_prepare_for_anthropic_completion(request: Request):
    """
    Validates the incoming request and prepares messages for Anthropic completion.
    """
    # Parse the JSON payload from the request
    data = await request.json()
    messages = data.get('messages', [])
    
    # Ensure messages are in a list format
    if not isinstance(messages, list):
        raise ValueError("Messages must be a list.")
    
    # Prepare messages for Anthropic's format without a system prompt
    prepared_messages = [{"role": msg["role"], "content": msg["content"]} for msg in messages]
    
    # Define the system prompt separately, as Anthropic expects a top-level parameter
    system_prompt_content = "You are a helpful assistant"

    return prepared_messages, system_prompt_content
