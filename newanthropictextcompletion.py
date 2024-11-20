import asyncio
from fastapi import HTTPException
from anthropic import AsyncAnthropic
import nltk
from stanza.pipeline.core import Pipeline as StanzaPipeline
import logging

client = AsyncAnthropic()

# Initialize global variables
stanza_pipeline = None
stanza_lock = asyncio.Lock()
nltk_downloaded = False  # Flag to check if NLTK data is downloaded

async def initialize_stanza():
    global stanza_pipeline
    async with stanza_lock:
        if stanza_pipeline is None:
            stanza_pipeline = StanzaPipeline(lang="en", processors="tokenize", use_gpu=False)

def initialize_nltk():
    global nltk_downloaded
    if not nltk_downloaded:
        nltk.download("punkt", quiet=True)
        nltk_downloaded = True

async def stream_and_process_chunks(
    messages: list,
    phrase_queue: asyncio.Queue,
    request_timestamp: float,
    tokenizer: str = "nltk",
    delimiters: list = None,
    min_phrase_length: int = 25
):
    try:
        working_string = ""
        tokenization_tasks = []
        sequence_number = 0  # To maintain order of phrases
        logging.info("Starting chunk streaming and processing.")
        
        # Initialize tokenizer if necessary
        if tokenizer.lower() == "stanza":
            await initialize_stanza()
        elif tokenizer.lower() == "nltk":
            initialize_nltk()
        else:
            raise ValueError(f"Unsupported tokenizer: {tokenizer}")
        
        async with client.messages.stream(
            max_tokens=Config.ANTHROPIC_MAX_TOKENS,
            messages=messages,
            model=Config.ANTHROPIC_RESPONSE_MODEL,
            system=Config.ANTHROPIC_SYSTEM_PROMPT,
            temperature=Config.ANTHROPIC_TEMPERATURE,
            top_p=Config.ANTHROPIC_TOP_P,
            stop_sequences=Config.ANTHROPIC_STOP_SEQUENCES,
        ) as stream:
            async for chunk in stream.text_stream:
                content = chunk or ""

                # Immediately yield the raw content to the frontend
                if content:
                    yield content

                # Append the chunk to the working string
                working_string += content

                # Process the working string for delimiters
                while len(working_string) >= min_phrase_length:
                    delimiter_index = -1
                    for delimiter in delimiters:
                        index = working_string.find(delimiter, min_phrase_length)
                        if index != -1 and (delimiter_index == -1 or index < delimiter_index):
                            delimiter_index = index
                    if delimiter_index == -1:
                        break
                    
                    # Extract the phrase and update the working string
                    phrase = working_string[:delimiter_index + 1].strip()
                    working_string = working_string[delimiter_index + 1:]
                    
                    # Create a tokenization task
                    task = asyncio.create_task(tokenize_and_queue(phrase, phrase_queue, tokenizer, sequence_number))
                    tokenization_tasks.append(task)
                    sequence_number += 1  # Increment sequence number

            # Final processing for leftover text
            if working_string.strip():
                phrase = working_string.strip()
                task = asyncio.create_task(tokenize_and_queue(phrase, phrase_queue, tokenizer, sequence_number))
                tokenization_tasks.append(task)

            # Wait for all tokenization tasks to complete
            await asyncio.gather(*tokenization_tasks)

            # Signal the end of processing
            await phrase_queue.put(None)

    except Exception as e:
        await phrase_queue.put(None)
        logging.error(f"Error during streaming and processing: {e}")
        raise HTTPException(status_code=500, detail=f"Error during streaming: {str(e)}")


async def tokenize_and_queue(phrase: str, phrase_queue: asyncio.Queue, tokenizer: str, sequence_number: int):
    try:
        if tokenizer.lower() == "nltk":
            tokens = nltk.word_tokenize(phrase)
        elif tokenizer.lower() == "stanza":
            if stanza_pipeline is None:
                raise ValueError("Stanza pipeline is not initialized.")
            doc = stanza_pipeline(phrase)
            tokens = [word.text for sentence in doc.sentences for word in sentence.words]
        else:
            raise ValueError(f"Unsupported tokenizer: {tokenizer}")

        # Re-queue the tokenized phrase with its sequence number
        tokenized_phrase = " ".join(tokens)
        await phrase_queue.put((sequence_number, tokenized_phrase))

    except Exception as e:
        logging.error(f"Tokenization failed for phrase '{phrase[:30]}...': {e}")
        # Handle the exception as needed
