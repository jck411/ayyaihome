# sentence_processor_interface.py

from abc import ABC, abstractmethod

class SentenceProcessor(ABC):
    @abstractmethod
    def process_sentences(self):
        pass
