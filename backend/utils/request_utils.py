from fastapi import HTTPException, Request

async def validate_and_prepare_for_openai_completion(request: Request):
    """
    Validates the incoming request and prepares messages for OpenAI completion.
    """
    data = await request.json()
    messages = data.get('messages')

    # Validate that 'messages' is a list
    if not isinstance(messages, list):
        raise HTTPException(status_code=400, detail="'messages' must be a list.")

    prepared_messages = []

    # Validate each message structure
    for idx, msg in enumerate(messages):
        if not isinstance(msg, dict):
            raise HTTPException(
                status_code=400,
                detail=f"Message at index {idx} must be a dictionary."
            )
        sender = msg.get("sender")
        text = msg.get("text")
        if not sender or not isinstance(sender, str):
            raise HTTPException(
                status_code=400,
                detail=f"Message at index {idx} must have a 'sender' field of type string."
            )
        if not text or not isinstance(text, str):
            raise HTTPException(
                status_code=400,
                detail=f"Message at index {idx} must have a 'text' field of type string."
            )
        # Map 'sender' to OpenAI's 'role'
        if sender.lower() == 'user':
            role = 'user'
        elif sender.lower() == 'assistant':
            role = 'assistant'
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid 'sender' value at index {idx}. Must be 'user' or 'assistant'."
            )
        prepared_messages.append({"role": role, "content": text})

    # Insert the system prompt at the start
    system_prompt = {"role": "system", "content": "You are a helpful assistant."}
    prepared_messages.insert(0, system_prompt)

    return prepared_messages


async def validate_and_prepare_for_anthropic(request: Request):
    """
    Validates the incoming request and prepares messages for Anthropic API.
    """
    payload = await request.json()
    messages = payload.get("messages")

    # Validate that 'messages' is a list
    if not isinstance(messages, list):
        raise HTTPException(status_code=400, detail="'messages' must be a list.")

    # Validate each message structure
    for msg in messages:
        if not isinstance(msg, dict):
            raise HTTPException(status_code=400, detail="Each message must be a dictionary.")
        if "role" not in msg or "content" not in msg:
            raise HTTPException(
                status_code=400,
                detail="Each message must include 'role' and 'content' keys."
            )
        if not isinstance(msg["content"], str):
            raise HTTPException(
                status_code=400,
                detail="The 'content' field in each message must be a string."
            )
        if msg["role"] not in {"user", "assistant"}:
            raise HTTPException(
                status_code=400,
                detail="The 'role' field must be either 'user' or 'assistant'."
            )

    # Return the validated messages
    return messages


from fastapi import Request

async def validate_and_prepare_for_google_completion(request: Request):
    """
    Validates and prepares the request for Google's Gemini API.
    """
    body = await request.json()
    if "messages" not in body or not isinstance(body["messages"], list):
        raise HTTPException(status_code=400, detail="Invalid or missing 'messages' field.")

    for message in body["messages"]:
        if "content" not in message:
            raise HTTPException(status_code=400, detail="Each message must have a 'content' field.")

    return body["messages"]
