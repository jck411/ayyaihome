from abc import ABC, abstractmethod
from typing import AsyncGenerator

class BaseTTSService(ABC):
    @abstractmethod
    async def synthesize(self, text: str) -> AsyncGenerator[bytes, None]:
        pass
