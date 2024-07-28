# text_preparer.py

def prepare_text(messages):
    # Ensure messages is a list and has at least one element
    if not isinstance(messages, list) or not messages:
        return None

    # Create a list of message dictionaries suitable for the OpenAI API
    prompt = [{"role": msg.get("sender", "user"), "content": msg.get("text", "")} for msg in messages if msg.get("text")]
    return prompt if prompt else None
