import logging
import asyncio
from typing import AsyncGenerator
from google import genai
from app.config import settings
from app.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)

class ChatAgent(BaseAgent):
    def __init__(self):
        self._name = "chat"
        self._description = "General conversation, Q&A, and answering questions."
        self._client = None
        self._chat_session = None

    @property
    def client(self):
        if self._client is None and settings.GEMINI_API_KEY:
            self._client = genai.Client(api_key=settings.GEMINI_API_KEY)
        return self._client
        
    @property
    def chat_session(self):
        if self._chat_session is None and self.client:
            system_instruction = (
                "You are JARVIS, an advanced, highly intelligent AI assistant designed to "
                "help the user with extreme efficiency, deep reasoning, and a touch of "
                "charming wit. You directly address the user seamlessly without filler statements. "
                "Your objective is to be the best Agent possible, providing concise, "
                "accurate, and sophisticated answers."
            )
            
            self._chat_session = self.client.aio.chats.create(
                model='gemini-2.5-flash',
                config={'system_instruction': system_instruction}
            )
        return self._chat_session

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    async def process(self, task: str) -> str:
        if not self.client:
            return "Internal Error: Gemini API key not configured for ChatAgent."
        try:
            response = await self.chat_session.send_message(task)
            return response.text
        except Exception as e:
            logger.error(f"ChatAgent processing error: {e}")
            raise e

    async def stream_process(self, task: str) -> AsyncGenerator[str, None]:
        if not self.client:
            yield "Internal Error: Gemini API key not configured for ChatAgent."
            return
            
        response = await self.chat_session.send_message_stream(task)
        async for chunk in response:
            yield chunk.text
            await asyncio.sleep(0.01)
