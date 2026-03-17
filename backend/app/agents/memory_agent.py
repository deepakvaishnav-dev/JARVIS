import logging
import asyncio
from typing import AsyncGenerator
from google import genai
from app.config import settings
from app.agents.base_agent import BaseAgent
from app.memory.memory_manager import MemoryManager

logger = logging.getLogger(__name__)

class MemoryAgent(BaseAgent):
    def __init__(self):
        self._name = "memory"
        self._description = "Responsible for saving or recalling important facts about the user."
        self.memory_manager = MemoryManager()
        self.client = None
        if settings.GEMINI_API_KEY:
            self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    async def _analyze_memory_intent(self, task: str) -> dict:
        """Determines if user is asking to save a fact or retrieve a fact."""
        if not self.client:
            return {"action": "error", "content": "No API key"}
            
        system_instruction = """
        You are a Memory Agent. Analyze the user's request.
        If the user is stating a fact to remember (e.g., 'My favorite color is blue', 'Remember that I have a dog named Max'),
        return a JSON object with 'action': 'save' and 'content': the exact fact to remember.
        If the user is asking you to recall a fact (e.g., 'What is my favorite color?', 'Do I have a pet?'),
        return a JSON object with 'action': 'recall' and 'query': the search query.
        """
        
        try:
            response = await self.client.aio.models.generate_content(
                model='gemini-2.5-flash',
                contents=task,
                config={'system_instruction': system_instruction, 'response_mime_type': 'application/json'}
            )
            import json
            return json.loads(response.text)
        except Exception as e:
            logger.error(f"MemoryAgent analysis error: {e}")
            return {"action": "error"}

    async def process(self, task: str, **kwargs) -> str:
        intent = await self._analyze_memory_intent(task)
        
        if intent.get("action") == "save":
            fact = intent.get("content", task)
            await self.memory_manager.save_fact(fact)
            return f"I have remembered this: '{fact}'."
            
        elif intent.get("action") == "recall":
            query = intent.get("query", task)
            context = await self.memory_manager.get_relevant_context(query)
            if not context:
                return "I don't have any memories related to that."
                
            # Use Gemini to format the final answer based on context
            if self.client:
                prompt = f"Answer the user's question '{query}' using ONLY this context:\n{context}"
                try:
                    response = await self.client.aio.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=prompt
                    )
                    return response.text
                except Exception:
                    pass
            return context
            
        return "I'm not sure what you want me to do with my memory right now."

    async def stream_process(self, task: str, **kwargs) -> AsyncGenerator[str, None]:
        yield "*Accessing memory bank...*\n"
        await asyncio.sleep(0.5)
        
        result = await self.process(task)
        
        # Fake streaming the result to maintain UX
        words = result.split(" ")
        for i in range(0, len(words), 5):
            chunk = " ".join(words[i:i+5]) + " "
            yield chunk
            await asyncio.sleep(0.05)
