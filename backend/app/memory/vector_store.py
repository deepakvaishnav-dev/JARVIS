import os
import uuid
import logging
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from app.memory.embeddings import EmbeddingService

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self):
        # Initialize ChromaDB persistent client
        self.db_dir = os.path.join(os.getcwd(), "chroma_db")
        os.makedirs(self.db_dir, exist_ok=True)
        self.client = chromadb.PersistentClient(path=self.db_dir)
        self.collection = self.client.get_or_create_collection(name="jarvis_memory")
        self.embedder = EmbeddingService()

    async def add_memory(self, content: str, memory_type: str = "semantic", tags: List[str] = None):
        """Adds a new memory with its embedding to the ChromaDB."""
        if tags is None:
            tags = []
            
        # Get embedding
        vector = await self.embedder.get_embedding(content)
        memory_id = str(uuid.uuid4())
        
        metadata = {
            "type": memory_type,
            "tags": ",".join(tags)
        }
        
        try:
            self.collection.add(
                ids=[memory_id],
                embeddings=[vector],
                metadatas=[metadata],
                documents=[content]
            )
            logger.info(f"Added memory: {content[:30]}...")
            return memory_id
        except Exception as e:
            logger.error(f"Failed to add memory: {e}")
            return None

    async def search_memory(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Searches ChromaDB for the most relevant memories."""
        if self.collection.count() == 0:
            return []
            
        query_vector = await self.embedder.get_embedding(query)
        
        try:
            results = self.collection.query(
                query_embeddings=[query_vector],
                n_results=min(n_results, self.collection.count())
            )
            
            memories = []
            for i in range(len(results['ids'][0])):
                memories.append({
                    "id": results['ids'][0][i],
                    "content": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                    "distance": results['distances'][0][i] if results['distances'] else 0.0
                })
            return memories
        except Exception as e:
            logger.error(f"Search memory failed: {e}")
            return []

    async def get_all_memories(self) -> List[Dict[str, Any]]:
        count = self.collection.count()
        if count == 0:
            return []
        
        try:
            results = self.collection.get(limit=count)
            memories = []
            for i in range(len(results['ids'])):
                memories.append({
                    "id": results['ids'][i],
                    "content": results['documents'][i],
                    "metadata": results['metadatas'][i] if results['metadatas'] else {}
                })
            return memories
        except Exception as e:
            logger.error(f"Failed to get all memories: {e}")
            return []

    async def delete_memory(self, memory_id: str) -> bool:
        try:
            self.collection.delete(ids=[memory_id])
            return True
        except Exception as e:
            logger.error(f"Failed to delete memory {memory_id}: {e}")
            return False

    async def clear_all(self):
        try:
            all_ids = self.collection.get()['ids']
            if all_ids:
                self.collection.delete(ids=all_ids)
            return True
        except Exception as e:
            logger.error(f"Failed to clear memories: {e}")
            return False
