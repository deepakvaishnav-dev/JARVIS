import logging
import asyncio
import json
from typing import AsyncGenerator
from google import genai
from app.config import settings
from app.agents.base_agent import BaseAgent
from app.tools.web_search import scrape_url

logger = logging.getLogger(__name__)

class WebAgent(BaseAgent):
    def __init__(self):
        self._name = "web"
        self._description = "Fetches and analyzes content from the live internet/web."
        self.client = None
        if settings.GEMINI_API_KEY:
            self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    async def _extract_url(self, task: str) -> str:
        if not self.client:
            return ""
            
        system_instruction = "Extract the full URL (http or https) to fetch from the user query. Return only the raw URL, nothing else. If there is no URL, you must guess the URL the user implies. Example: if asked 'summarize wikipedia AI', return 'https://en.wikipedia.org/wiki/Artificial_intelligence'."
        
        try:
            response = await self.client.aio.models.generate_content(
                model='gemini-2.5-flash',
                contents=task,
                config={'system_instruction': system_instruction}
            )
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error extracting URL: {e}")
            return ""

    async def _format_response(self, task: str, scraped_content: str) -> str:
        if not self.client:
            return scraped_content[:1500] + "..."
            
        system_instruction = "You are a Web Summarization Agent. Using the scraped content provided, answer the user's original request directly."
        
        prompt = f"User Request: '{task}'\n\nScraped Content:\n{scraped_content}"
        
        try:
            response = await self.client.aio.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config={'system_instruction': system_instruction}
            )
            return response.text
        except Exception as e:
            logger.error(f"WebAgent formatting error: {e}")
            return "Failed to synthesize web response."

    async def process(self, task: str) -> str:
        url = await self._extract_url(task)
        if not url or not url.startswith("http"):
            return "I couldn't identify a valid URL to scrape in your request."
            
        logger.info(f"WebAgent extracted URL: {url}")
        
        content = await scrape_url(url)
        if content.startswith("Failed to scrape"):
            return content
            
        final_answer = await self._format_response(task, content)
        return final_answer

    async def stream_process(self, task: str) -> AsyncGenerator[str, None]:
        yield "*Fetching the requested webpage. This may take a moment to bypass captchas and load JS...*\n\n"
        
        url = await self._extract_url(task)
        if not url or not url.startswith("http"):
            yield "I couldn't identify a valid URL to scrape."
            return
            
        yield f"*(Targeting `{url}`)*\n"
        
        # Scrape
        content = await scrape_url(url)
        if content.startswith("Failed to scrape"):
            yield f"\n{content}"
            return
            
        yield "*(Reading content...)*\n\n"
        
        # Stream response back
        if self.client:
            system_instruction = "You are a Web Summarization Agent. Answer the user's original request using ONLY the provided scraped content."
            prompt = f"User Request: '{task}'\n\nScraped Content:\n{content}"
            try:
                # We need to use async generation for the final answer
                response_stream = await self.client.aio.models.generate_content_stream(
                    model='gemini-2.5-flash',
                    contents=prompt,
                    config={'system_instruction': system_instruction}
                )
                async for chunk in response_stream:
                    yield chunk.text
                    await asyncio.sleep(0.01)
                return
            except Exception as e:
                logger.error(f"Streaming answer error: {e}")
        
        # Fallback if streaming failed
        yield "An error occurred formatting the final answer."
