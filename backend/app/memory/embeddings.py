import logging
from google import genai
from app.config import settings

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self):
        self.client = None
        if settings.GEMINI_API_KEY:
            self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
            
    async def get_embedding(self, text: str) -> list[float]:
        if not self.client:
            logger.warning("No Gemini API key for embeddings. Returning dummy vector.")
            return [0.0] * 768
            
        try:
            # Google GenAI model for embeddings
            result = await self.client.aio.models.embed_content(
                model='gemini-embedding-001',
                contents=text
            )
            return result.embeddings[0].values
        except Exception as e:
            logger.error(f"Embedding error: {e}")
            return [0.0] * 768
