# config.py

TEXT_GENERATOR = "openai"         # Options: "openai" or "anthropic"
TTS_SERVICE = "openai"            # Options: "openai" or "azure"
SENTENCE_PROCESSOR = "default"    # Options: "default", "transformers", or "async"

# For transformers and async sentence_processor - shared constants:
CONTENT_TRANSFORMERS = [
    lambda c: c.replace("\n", " ")
]  # List of functions that will be applied to content before sentence processing

PHRASE_TRANSFORMERS = [
    lambda p: p.strip()
]  # List of functions that will be applied to each sentence/phrase

DELIMITERS = [
    f"{d} " for d in (".", "?", "!")
]  # List of delimiters used for splitting sentences

MINIMUM_PHRASE_LENGTH = 25  # Minimum length of phrases to process before attempting to split
