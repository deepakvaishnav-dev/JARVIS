import logging
import asyncio
import os
import subprocess
from typing import AsyncGenerator
from google import genai
from app.config import settings
from app.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)

class SystemAgent(BaseAgent):
    def __init__(self):
        self._name = "system"
        self._description = "Executes safe system commands."
        self.client = None
        if settings.GEMINI_API_KEY:
            self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    async def _analyze_command(self, task: str) -> str:
        """Determines the safe command to run based on user input."""
        if not self.client:
            return "echo 'Gemini API not configured'"
            
        system_instruction = "You are a Windows System Agent. Convert the user's request into a single, safe PowerShell command. Only return the raw command string, no markdown, no quotes unless needed for the command. If the command requested is unsafe (like rm -rf, formatting disks, etc.), return 'echo unsafe command denied'. Focus on safe ops: disk usage, current directory listing, getting time, showing system info."
        
        try:
            response = await self.client.aio.models.generate_content(
                model='gemini-2.5-flash',
                contents=task,
                config={'system_instruction': system_instruction}
            )
            return response.text.strip()
        except Exception as e:
            logger.error(f"SystemAgent analysis error: {e}")
            return f"echo 'Error generating command: {e}'"

    async def process(self, task: str, **kwargs) -> str:
        command = await self._analyze_command(task)
        logger.info(f"SystemAgent determined command: {command}")
        
        try:
            # Execute safely
            result = await asyncio.to_thread(
                subprocess.run, 
                ["powershell.exe", "-Command", command], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            output = result.stdout.strip() if result.stdout else result.stderr.strip()
            return f"**System Output for:** `{command}`\n```\n{output}\n```"
        except Exception as e:
            logger.error(f"SystemAgent execution error: {e}")
            return f"Execution Error: {str(e)}"

    async def stream_process(self, task: str, **kwargs) -> AsyncGenerator[str, None]:
        yield "*Thinking about system command...*\n"
        await asyncio.sleep(0.5)
        
        result = await self.process(task)
        
        # Fake streaming the result to maintain UX
        words = result.split(" ")
        for i in range(0, len(words), 5):
            chunk = " ".join(words[i:i+5]) + " "
            yield chunk
            await asyncio.sleep(0.05)
