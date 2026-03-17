import logging
import asyncio
import json
from typing import AsyncGenerator
from google import genai
from app.config import settings
from app.agents.base_agent import BaseAgent
import app.tools.file_ops as file_ops

logger = logging.getLogger(__name__)

class FileAgent(BaseAgent):
    def __init__(self):
        self._name = "file"
        self._description = "Handles reading, writing, listing, and deleting files strictly within the jarvis_files sandbox."
        self.client = None
        if settings.GEMINI_API_KEY:
            self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    async def _analyze_file_intent(self, task: str) -> dict:
        if not self.client:
            return {"action": "error", "message": "No API key"}
            
        system_instruction = """
        You are a File Operations Agent. Determine the action required by the user.
        Return strictly valid JSON with the following format:
        For read: {"action": "read", "filename": "example.txt"}
        For write: {"action": "write", "filename": "example.txt", "content": "Text to write"}
        For delete: {"action": "delete", "filename": "example.txt"}
        For list: {"action": "list"}
        If you don't understand, return: {"action": "error", "message": "unsupported"}
        DO NOT wrap your JSON in markdown blocks like ```json ... ```. Just return raw JSON.
        """
        
        try:
            response = await self.client.aio.models.generate_content(
                model='gemini-2.5-flash',
                contents=task,
                config={'system_instruction': system_instruction, 'response_mime_type': 'application/json'}
            )
            return json.loads(response.text)
        except Exception as e:
            logger.error(f"FileAgent parsing error: {e}")
            return {"action": "error", "message": "Failed to parse intent"}

    async def process(self, task: str, **kwargs) -> str:
        intent = await self._analyze_file_intent(task)
        action = intent.get("action")
        
        if action == "list":
            return await asyncio.to_thread(file_ops.list_files)
            
        elif action == "read":
            filename = intent.get("filename")
            if not filename: return "Error: Missing filename."
            return f"**Contents of `{filename}`:**\n\n```text\n{await asyncio.to_thread(file_ops.read_file, filename)}\n```"
            
        elif action == "write":
            filename = intent.get("filename")
            content = intent.get("content", "")
            if not filename: return "Error: Missing filename."
            return await asyncio.to_thread(file_ops.write_file, filename, content)
            
        elif action == "delete":
            filename = intent.get("filename")
            if not filename: return "Error: Missing filename."
            return await asyncio.to_thread(file_ops.delete_file, filename)
            
        return "I could not understand the file operation requested."

    async def stream_process(self, task: str, **kwargs) -> AsyncGenerator[str, None]:
        yield "*Processing file operation...*\n"
        await asyncio.sleep(0.5)
        
        result = await self.process(task)
        
        words = result.split(" ")
        for i in range(0, len(words), 5):
            chunk = " ".join(words[i:i+5]) + " "
            yield chunk
            await asyncio.sleep(0.05)
