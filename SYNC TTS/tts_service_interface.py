from abc import ABC, abstractmethod

class TTSService(ABC):
    @abstractmethod
    def generate_audio(self):
        pass
