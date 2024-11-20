# backend/text_generation/phrase_preparation/SSML_addition.py

import logging

logger = logging.getLogger(__name__)

def create_ssml(
    phrase: str,
    voice_name: str,
    rate: str = "0%",
    pitch: str = "0Hz",
    volume: str = "100%",
    stability: float = 1.0
) -> str:
    """
    Generates SSML to adjust prosody (rate, pitch, volume) and voice settings.
    
    Args:
        phrase (str): The text to convert to speech.
        voice_name (str): The name of the voice to use.
        rate (str): Speaking rate (e.g., "0%", "10%", "-10%").
        pitch (str): Pitch adjustment (e.g., "0Hz", "+2Hz", "-2Hz").
        volume (str): Volume adjustment (e.g., "100%", "+10%", "-10%").
        stability (float): Stability of the voice.

    Returns:
        str: The generated SSML string.
    """
    ssml = f"""
<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='en-US'>
    <voice name='{voice_name}'>
        <prosody rate='{rate}' pitch='{pitch}' volume='{volume}'>
            {phrase}
        </prosody>
    </voice>
</speak>
"""
    logger.debug(f"Generated SSML: {ssml}")
    return ssml
