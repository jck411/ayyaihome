from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
from azure.cognitiveservices.speech import SpeechConfig

def get_openai_client(api_key: str = None) -> AsyncOpenAI:
    """
    Creates an OpenAI client.

    Args:
        api_key (str, optional): OpenAI API key. Defaults to the value in Config.

    Returns:
        AsyncOpenAI: Configured OpenAI client.
    """
    if api_key is None:
        from backend.config import Config  # Delayed import to avoid circular dependency
        api_key = Config.OPENAI_API_KEY

    if not api_key:
        raise ValueError("OpenAI API key is not set.")
    return AsyncOpenAI(api_key=api_key)

def get_anthropic_client(api_key: str = None) -> AsyncAnthropic:
    """
    Creates an Anthropic client.

    Args:
        api_key (str, optional): Anthropic API key. Defaults to the value in Config.

    Returns:
        AsyncAnthropic: Configured Anthropic client.
    """
    if api_key is None:
        from backend.config import Config  # Delayed import to avoid circular dependency
        api_key = Config.ANTHROPIC_API_KEY

    if not api_key:
        raise ValueError("Anthropic API key is not set.")
    return AsyncAnthropic(api_key=api_key)

def get_azure_speech_config(subscription_key: str = None, region: str = None) -> SpeechConfig:
    """
    Creates an Azure SpeechConfig instance.

    Args:
        subscription_key (str, optional): Azure subscription key. Defaults to the value in Config.
        region (str, optional): Azure service region. Defaults to the value in Config.

    Returns:
        SpeechConfig: Configured Azure SpeechConfig instance.
    """
    if subscription_key is None:
        from backend.config import Config  # Avoid circular import
        subscription_key = Config.AZURE_SPEECH_KEY
        region = Config.AZURE_SPEECH_REGION

    if not subscription_key:
        raise ValueError("AZURE_SPEECH_KEY is missing. Set it in your environment or configuration.")
    if not region:
        raise ValueError("AZURE_SPEECH_REGION is missing. Set it in your environment or configuration.")

    return SpeechConfig(subscription=subscription_key, region=region)


def get_google_client(api_key: str = None):
    """
    Creates a Google Gemini client.

    Args:
        api_key (str, optional): Google API key. Defaults to the value in Config.

    Returns:
        dict: Placeholder for a Google Gemini client (or equivalent).
    """
    if api_key is None:
        from backend.config import Config  # Delayed import to avoid circular dependency
        api_key = Config.GEMINI_API_KEY

    if not api_key:
        raise ValueError("Google API key is not set.")

    # Example client initialization logic
    return {
        "client": "Google Gemini Client",
        "api_key": api_key,
        "model_version": Config.GEMINI_MODEL_VERSION,
    }