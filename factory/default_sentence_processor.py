# default_sentence_processor.py

from sentence_processor_interface import SentenceProcessor
import re
import queue

class DefaultSentenceProcessor(SentenceProcessor):
    def __init__(self, text_queue, sentence_queue, text_generation_complete, sentence_processing_complete):
        self.text_queue = text_queue
        self.sentence_queue = sentence_queue
        self.text_generation_complete = text_generation_complete
        self.sentence_processing_complete = sentence_processing_complete

    def process_sentences(self):
        sentence_buffer = ""
        while not (self.text_generation_complete.is_set() and self.text_queue.empty()):
            try:
                new_text = self.text_queue.get(timeout=0.1)
                sentence_buffer += new_text

                # Split sentences properly
                sentences = re.split(r'(?<=[.!?])\s+', sentence_buffer)
                if sentences:
                    # If the last character is not a sentence terminator, keep the last part in buffer
                    if sentence_buffer[-1] not in '.!?':
                        sentence_buffer = sentences.pop()
                    else:
                        sentence_buffer = ''
                    for sentence in sentences:
                        self.sentence_queue.put(sentence.strip())
                else:
                    # No complete sentences yet, keep buffering
                    continue
            except queue.Empty:
                continue

        # Process any remaining text
        if sentence_buffer:
            self.sentence_queue.put(sentence_buffer.strip())

        self.sentence_processing_complete.set()
