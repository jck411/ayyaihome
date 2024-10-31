# streaming_sentence_processor.py

from sentence_processor_interface import SentenceProcessor
import threading
import queue
from functools import reduce
from typing import Callable, Generator, List

class StreamingSentenceProcessor(SentenceProcessor):
    def __init__(
        self,
        text_queue: queue.Queue,
        sentence_queue: queue.Queue,
        text_generation_complete: threading.Event,
        sentence_processing_complete: threading.Event,
        content_transformers: List[Callable[[str], str]] = None,
        phrase_transformers: List[Callable[[str], str]] = None,
        delimiters: List[str] = None,
        minimum_phrase_length: int = 200
    ):
        self.text_queue = text_queue
        self.sentence_queue = sentence_queue
        self.text_generation_complete = text_generation_complete
        self.sentence_processing_complete = sentence_processing_complete
        self.content_transformers = content_transformers or []
        self.phrase_transformers = phrase_transformers or []
        self.delimiters = delimiters or [f"{d} " for d in (".", "?", "!")]
        self.minimum_phrase_length = minimum_phrase_length
        self.stop_event = threading.Event()

    def apply_transformers(self, s: str, transformers: List[Callable[[str], str]]) -> str:
        return reduce(lambda c, transformer: transformer(c), transformers, s)

    def process_sentences(self):
        working_string = ""
        while not (self.text_generation_complete.is_set() and self.text_queue.empty()):
            try:
                content = self.text_queue.get(timeout=0.1)
                if content:
                    # Apply content transformers
                    content = self.apply_transformers(content, self.content_transformers)
                    working_string += content

                    while len(working_string) >= self.minimum_phrase_length:
                        delimiter_index = -1
                        for delimiter in self.delimiters:
                            index = working_string.find(delimiter, self.minimum_phrase_length)
                            if index != -1 and (delimiter_index == -1 or index < delimiter_index):
                                delimiter_index = index

                        if delimiter_index == -1:
                            break

                        phrase, working_string = (
                            working_string[: delimiter_index + len(delimiter)],
                            working_string[delimiter_index + len(delimiter):],
                        )
                        # Apply phrase transformers
                        phrase = self.apply_transformers(phrase, self.phrase_transformers)
                        self.sentence_queue.put(phrase)
                else:
                    continue
            except queue.Empty:
                continue

        # Yield any remaining content that didn't end with the delimiter
        if working_string.strip():
            phrase = self.apply_transformers(working_string.strip(), self.phrase_transformers)
            self.sentence_queue.put(phrase)

        self.sentence_processing_complete.set()
