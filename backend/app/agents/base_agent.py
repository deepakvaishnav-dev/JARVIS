from abc import ABC, abstractmethod
from typing import AsyncGenerator

class BaseAgent(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        pass

    @abstractmethod
    async def process(self, task: str, **kwargs) -> str:
        """Process a task and return a full string response."""
        pass

    @abstractmethod
    async def stream_process(self, task: str, **kwargs) -> AsyncGenerator[str, None]:
        """Process a task and yield string chunks (for streaming)."""
        pass
