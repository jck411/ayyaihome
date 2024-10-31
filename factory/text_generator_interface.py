# text_generator_interface.py

from abc import ABC, abstractmethod

class TextGenerator(ABC):
    @abstractmethod
    def generate_text(self):
        pass
