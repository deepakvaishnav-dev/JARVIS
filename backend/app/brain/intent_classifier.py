import json
import logging
from google import genai
from pydantic import BaseModel
from app.config import settings

logger = logging.getLogger(__name__)

class IntentClassification(BaseModel):
    agent_type: str
    confidence: float

class IntentClassifier:
    def __init__(self):
        self._client = None
        
    @property
    def client(self):
        if self._client is None and settings.GEMINI_API_KEY:
            self._client = genai.Client(api_key=settings.GEMINI_API_KEY)
        return self._client
            
    async def classify(self, user_input: str) -> IntentClassification:
        DEFAULTResponse = IntentClassification(agent_type="chat", confidence=0.0)
        if not self.client:
            return DEFAULTResponse
            
        system_instruction = """
        You are an Intent Classifier. Given the user input, determine which specialized agent must handle it.
        Return a JSON object with two fields: 'agent_type' (string) and 'confidence' (float between 0.0 and 1.0).
        Available agent types: 'chat', 'system', 'web', 'file', 'memory'.
        If the intent is general conversation, question, or unknown, use 'chat'.
        If it's a request to execute a system command, open an app, or check OS status, use 'system'.
        If the user is asking you to summarize a webpage, read a URL, or fetch live internet data, use 'web'.
        If the user is asking you to create, read, delete, or list files (e.g. text files), use 'file'.
        If the user is stating a fact to remember or asking to recall a fact, use 'memory'.
        Make sure the output is strictly valid JSON matching the schema.
        """
        
        try:
            response = await self.client.aio.models.generate_content(
                model='gemini-2.5-flash',
                contents=user_input,
                config={'system_instruction': system_instruction, 'response_mime_type': 'application/json'}
            )
            
            result = json.loads(response.text)
            return IntentClassification(**result)
            
        except Exception as e:
            logger.error(f"Intent Classification Error: {e}")
            error_str = str(e).lower()
            if "429" in error_str or "quota" in error_str or "too many requests" in error_str or "resource_exhausted" in error_str:
                logger.warning("Quota exceeded for intent classifier. Falling back to offline agent.")
                return IntentClassification(agent_type="offline", confidence=1.0)
            return DEFAULTResponse
