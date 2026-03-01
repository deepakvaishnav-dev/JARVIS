import logging
from typing import List, Dict, Any
from app.memory.vector_store import VectorStore

logger = logging.getLogger(__name__)

class MemoryManager:
    """High-level abstraction over the vector store to manage JARVIS's context."""
    def __init__(self):
        self.store = VectorStore()

    async def save_fact(self, fact: str, tags: List[str] = None):
        """Used by agents to explicitly remember important facts."""
        return await self.store.add_memory(fact, memory_type="semantic", tags=tags)

    async def get_relevant_context(self, query: str, context_window: int = 5) -> str:
        """Retrieves and formats memories relevant to a query."""
        results = await self.store.search_memory(query, n_results=context_window)
        if not results:
            return ""
            
        context_str = "Relevant context from past interactions:\n"
        for i, res in enumerate(results):
            # Only include highly relevant context based on distance (Chroma L2 distance, lower is better)
            context_str += f"- {res['content']}\n"
            
        return context_str
