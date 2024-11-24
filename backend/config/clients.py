from .settings import Config
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
import azure.cognitiveservices.speech as speechsdk

def get_openai_client() -> AsyncOpenAI:
    api_key = Config.OPENAI_API_KEY
    if not api_key:
        raise ValueError("OpenAI API key is not set.")
    return AsyncOpenAI(api_key=api_key)

def get_anthropic_client() -> AsyncAnthropic:
    api_key = Config.ANTHROPIC_API_KEY
    if not api_key:
        raise ValueError("Anthropic API key is not set.")
    return AsyncAnthropic(api_key=api_key)

def get_azure_speech_config() -> speechsdk.SpeechConfig:
    subscription_key = Config.AZURE_SPEECH_KEY
    region = Config.AZURE_SERVICE_REGION
    if not subscription_key or not region:
        raise ValueError("Azure Speech credentials are not set.")
    speech_config = speechsdk.SpeechConfig(subscription=subscription_key, region=region)
    speech_config.speech_synthesis_voice_name = Config.AZURE_TTS_VOICE
    speech_config.speech_synthesis_rate = Config.AZURE_TTS_SPEED

    # Set output format
    try:
        speech_config.set_speech_synthesis_output_format(
            getattr(speechsdk.SpeechSynthesisOutputFormat, Config.AZURE_AUDIO_FORMAT)
        )
    except AttributeError:
        raise ValueError(f"Invalid AUDIO_FORMAT: {Config.AZURE_AUDIO_FORMAT}")
    
    return speech_config
