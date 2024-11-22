# /home/jack/ayyaihome/backend/TTS/phrase_preparation/tokenizer.py

import asyncio

async def tokenize_text(text: str, tokenizer_type: str) -> str:
    """
    Tokenizes the text using the specified tokenizer.

    Args:
        text (str): The text to tokenize.
        tokenizer_type (str): The tokenizer to use ('nltk', 'stanza', 'none').

    Returns:
        str: The tokenized text.
    """
    if tokenizer_type == 'nltk':
        # Perform NLTK tokenization
        import nltk
        nltk.download('punkt', quiet=True)
        tokens = nltk.word_tokenize(text)
        return ' '.join(tokens)
    elif tokenizer_type == 'stanza':
        # Perform Stanza tokenization
        import stanza
        stanza.download('en', processors='tokenize', verbose=False)
        nlp = stanza.Pipeline('en', processors='tokenize', verbose=False)
        doc = nlp(text)
        tokens = [word.text for sent in doc.sentences for word in sent.words]
        return ' '.join(tokens)
    elif tokenizer_type == 'none':
        # No tokenization
        return text
    else:
        # Unknown tokenizer type
        return text
