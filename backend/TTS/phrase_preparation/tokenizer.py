import asyncio
from backend.config import Config  # Adjust the import based on your project structure
import nltk

# Ensure the necessary NLTK data is downloaded
nltk.download('punkt', quiet=True)

async def tokenize_text(text: str) -> str:
    tokenizer_type = Config.TOKENIZER_TYPE

    if tokenizer_type == 'nltk':
        language = Config.NLTK_LANGUAGE
        tokenizer_name = Config.NLTK_TOKENIZER

        if tokenizer_name == 'word_tokenize':
            preserve_line = Config.NLTK_PRESERVE_LINE
            tokens = nltk.word_tokenize(text, language=language, preserve_line=preserve_line)
        elif tokenizer_name == 'TreebankWordTokenizer':
            from nltk.tokenize import TreebankWordTokenizer
            tokenizer = TreebankWordTokenizer()
            tokens = tokenizer.tokenize(text)
        elif tokenizer_name == 'TweetTokenizer':
            from nltk.tokenize import TweetTokenizer
            tokenizer = TweetTokenizer()
            tokens = tokenizer.tokenize(text)
        else:
            raise ValueError(f"Unsupported NLTK tokenizer: {tokenizer_name}")

        return ' '.join(tokens)

    elif tokenizer_type == 'stanza':
        import stanza
        language = Config.STANZA_LANGUAGE
        processors = Config.STANZA_PROCESSORS
        tokenize_no_ssplit = Config.STANZA_TOKENIZE_NO_SSPLIT
        use_gpu = Config.STANZA_USE_GPU
        verbose = Config.STANZA_VERBOSE

        stanza.download(language, processors=processors, verbose=verbose)
        nlp = stanza.Pipeline(
            lang=language,
            processors=processors,
            tokenize_no_ssplit=tokenize_no_ssplit,
            use_gpu=use_gpu,
            verbose=verbose
        )
        doc = nlp(text)
        tokens = [word.text for sent in doc.sentences for word in sent.words]
        return ' '.join(tokens)

    elif tokenizer_type == 'none':
        return text
    else:
        raise ValueError(f"Unknown tokenizer type: {tokenizer_type}")
