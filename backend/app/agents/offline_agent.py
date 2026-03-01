import logging
import asyncio
from typing import AsyncGenerator
import ollama
from app.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)

class OfflineAgent(BaseAgent):
    def __init__(self, model_name="llama3.2"):
        self._name = "offline"
        self._description = "Fallback agent running entirely on the local machine using Ollama."
        self.model_name = model_name

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    async def _check_ollama(self) -> bool:
        """Check if Ollama is running and the model is available."""
        try:
            # Create a background thread to check ollama list so we don't block
            _ = await asyncio.to_thread(ollama.list)
            return True
        except Exception as e:
            logger.warning(f"Ollama not reachable: {e}")
            return False

    async def process(self, task: str) -> str:
        if not await self._check_ollama():
            return "Error: Local Ollama service is not running or unreachable."

        try:
            response = await asyncio.to_thread(
                ollama.chat,
                model=self.model_name,
                messages=[{'role': 'user', 'content': task}]
            )
            return response['message']['content']
        except Exception as e:
            logger.error(f"OfflineAgent error: {e}")
            return f"Error executing local model: {e}"

    async def stream_process(self, task: str) -> AsyncGenerator[str, None]:
        yield "*(Switching to Offline Processing mode...)*\n\n"
        
        if not await self._check_ollama():
            yield "> **CRITCAL ERROR:** Cloud quota exceeded and local Ollama service is not running.\n"
            yield "> Please start Ollama locally to use the fallback engine."
            return

        try:
            # We must run the streaming chat in a thread chunk by chunk since ollama python sync client blocks
            # But the ollama library provides an async client too!
            from ollama import AsyncClient
            client = AsyncClient()
            
            async for chunk in await client.chat(
                model=self.model_name,
                messages=[{'role': 'user', 'content': task}],
                stream=True,
            ):
                if chunk and 'message' in chunk and 'content' in chunk['message']:
                    yield chunk['message']['content']
                    await asyncio.sleep(0.01)

        except Exception as e:
            logger.error(f"Offline streaming error: {e}")
            yield f"\n\nLocal model error: {e}"
