import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

def extract_content_from_gemini_chunk(chunk: Any) -> Optional[str]:
    """
    Extracts content from Gemini's streaming response.

    Args:
        chunk (Any): The chunk object from Gemini's streaming response.

    Returns:
        Optional[str]: The extracted content string or None if not available.
    """
    try:
        # Example structure based on Gemini's response format
        if hasattr(chunk, 'result') and chunk.result and chunk.result.candidates:
            candidate = chunk.result.candidates[0]
            
            if candidate.content and candidate.content.parts:
                text = candidate.content.parts[0].text or ""
                return text.strip() if text else None
        
        return None
    except Exception as e:
        logger.error(f"Error extracting content from Gemini chunk: {e}")
        return None
