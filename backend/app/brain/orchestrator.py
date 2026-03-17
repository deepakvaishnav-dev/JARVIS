import logging
import asyncio
from typing import AsyncGenerator
from app.brain.intent_classifier import IntentClassifier
from app.agents.chat_agent import ChatAgent
from app.agents.system_agent import SystemAgent
from app.agents.memory_agent import MemoryAgent
from app.agents.file_agent import FileAgent
from app.agents.web_agent import WebAgent
from app.agents.offline_agent import OfflineAgent

logger = logging.getLogger(__name__)

class Orchestrator:
    def __init__(self):
        self.classifier = IntentClassifier()
        
        # Initialize registry of agents
        self.agents = {
            "chat": ChatAgent(),
            "system": SystemAgent(),
            "memory": MemoryAgent(),
            "file": FileAgent(),
            "web": WebAgent(),
            "offline": OfflineAgent(),
            # Fallback to chat for unimplemented agents currently
        }
        
    def _get_agent(self, agent_type: str):
        # Default to chat if unknown agent type is returned
        return self.agents.get(agent_type, self.agents["chat"])

    async def _log_agent_decision(self, intent, confidence):
        yield f"*(Routed to `{intent}` agent, confidence: {confidence:.2f})*\n\n"

    async def handle_request_stream(self, user_input: str, language: str = "en", file_ids: list[str] = None) -> AsyncGenerator[str, None]:
        """
        Main entry point for websocket text streams.
        1. Classifies intent.
        2. Selects appropriate agent.
        3. Streams the output back.
        """
        try:
            # Send immediate feedback to the UI
            yield "*Analyzing directive...*\n\n"
            await asyncio.sleep(0.01) # flush yield
            
            # 1. Classify
            classification = await self.classifier.classify(user_input)
            agent_type = classification.agent_type
            
            logger.info(f"Orchestrator routed '{user_input[:20]}...' to '{agent_type}'")
            
            # 2. Select Agent
            agent = self._get_agent(agent_type)

            agent_input = user_input
            if file_ids:
                agent = self.agents["chat"] # Force routing to chat agent if there are file attachments
                
            if language == "hi":
                agent_input = f"{user_input}\n\n[SYSTEM DICTATE: The user is speaking in Hindi. You MUST respond ENTIRELY in Hindi language.]"

            # 3. Stream Process
            try:
                async for chunk in agent.stream_process(agent_input, file_ids=file_ids or []):
                    yield chunk
            except Exception as e:
                error_str = str(e).lower()
                if "429" in error_str or "quota" in error_str or "too many requests" in error_str or "resource_exhausted" in error_str:
                    logger.warning("Caught 429 Quota Exceeded. Falling back to local Offline Agent.")
                    yield "\n\n> **SYSTEM ALERT**: Cloud API Quota Exceeded.\n"
                    offline_agent = self.agents["offline"]
                    async for chunk in offline_agent.stream_process(agent_input, file_ids=file_ids or []):
                        yield chunk
                else:
                    logger.error(f"{agent.__class__.__name__} streaming error: {e}")
                    yield f"\n[Error executing task: {e}]"
                
        except Exception as e:
            logger.error(f"Orchestrator error: {e}")
            yield f"System Error: {str(e)}"
