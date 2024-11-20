# backend/utils/request_utils.py

import logging
from fastapi import HTTPException, Request

from backend.config import Config

logger = logging.getLogger(__name__)

async def validate_and_prepare_for_openai_completion(request: Request):
    """
    Validates the incoming request and prepares messages for OpenAI completion.

    Args:
        request (Request): FastAPI request object.

    Returns:
        List[Dict[str, str]]: Prepared list of messages.
    """
    data = await request.json()
    messages = data.get('messages')

    # Validate that 'messages' is a list
    if not isinstance(messages, list):
        logger.error("'messages' is not a list.")
        raise HTTPException(status_code=400, detail="'messages' must be a list.")

    prepared_messages = []

    # Validate each message structure
    for idx, msg in enumerate(messages):
        if not isinstance(msg, dict):
            logger.error(f"Message at index {idx} is not a dictionary.")
            raise HTTPException(
                status_code=400,
                detail=f"Message at index {idx} must be a dictionary."
            )
        sender = msg.get("sender")
        text = msg.get("text")
        if not sender or not isinstance(sender, str):
            logger.error(f"Message at index {idx} missing 'sender' or it's not a string.")
            raise HTTPException(
                status_code=400,
                detail=f"Message at index {idx} must have a 'sender' field of type string."
            )
        if not text or not isinstance(text, str):
            logger.error(f"Message at index {idx} missing 'text' or it's not a string.")
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
            logger.error(f"Invalid 'sender' value at index {idx}.")
            raise HTTPException(
                status_code=400,
                detail=f"Invalid 'sender' value at index {idx}. Must be 'user' or 'assistant'."
            )
        prepared_messages.append({"role": role, "content": text})

    # Insert the system prompt at the start
    system_prompt = {"role": "system", "content": Config.LLM_MODEL_CONFIG.get('OPENAI', {}).get('SYSTEM_PROMPT_CONTENT', "You are a helpful assistant.")}
    prepared_messages.insert(0, system_prompt)

    logger.debug("Prepared messages for OpenAI completion.")
    return prepared_messages


async def validate_and_prepare_for_anthropic(request: Request):
    """
    Validates the incoming request and prepares messages for Anthropic API.

    Args:
        request (Request): FastAPI request object.

    Returns:
        List[Dict[str, str]]: Validated list of messages.
    """
    payload = await request.json()
    messages = payload.get("messages")

    # Validate that 'messages' is a list
    if not isinstance(messages, list):
        logger.error("'messages' is not a list.")
        raise HTTPException(status_code=400, detail="'messages' must be a list.")

    # Validate each message structure
    for msg in messages:
        if not isinstance(msg, dict):
            logger.error("A message is not a dictionary.")
            raise HTTPException(status_code=400, detail="Each message must be a dictionary.")
        if "role" not in msg or "content" not in msg:
            logger.error("A message is missing 'role' or 'content'.")
            raise HTTPException(
                status_code=400,
                detail="Each message must include 'role' and 'content' keys."
            )
        if not isinstance(msg["content"], str):
            logger.error("The 'content' field is not a string.")
            raise HTTPException(
                status_code=400,
                detail="The 'content' field in each message must be a string."
            )
        if msg["role"] not in {"user", "assistant"}:
            logger.error("Invalid 'role' value in a message.")
            raise HTTPException(
                status_code=400,
                detail="The 'role' field must be either 'user' or 'assistant'."
            )

    logger.debug("Validated messages for Anthropic API.")
    return messages
