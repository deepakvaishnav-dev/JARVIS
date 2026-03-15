from fastapi import APIRouter, HTTPException, Request
from typing import List, Dict, Any
from app.memory.vector_store import VectorStore
from pydantic import BaseModel
from app.security import limiter
from app.config import settings
import logging
logger = logging.getLogger(__name__)

router = APIRouter()
store = VectorStore()

class MemoryContent(BaseModel):
    content: str
    type: str = "semantic"
    tags: List[str] = []

@router.get("/")
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def list_memories(request: Request) -> List[Dict[str, Any]]:
    memories = await store.get_all_memories()
    return memories

@router.post("/")
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def create_memory(request: Request, memory: MemoryContent):
    memory_id = await store.add_memory(memory.content, memory.type, memory.tags)
    if memory_id:
        return {"status": "success", "id": memory_id}
    raise HTTPException(status_code=500, detail="Failed to save memory")

@router.delete("/{memory_id}")
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def delete_memory(request: Request, memory_id: str):
    success = await store.delete_memory(memory_id)
    if success:
        return {"status": "success"}
    raise HTTPException(status_code=500, detail="Failed to delete memory")

@router.delete("/all")
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def clear_all_memories(request: Request):
    success = await store.clear_all()
    if success:
        return {"status": "success"}
    raise HTTPException(status_code=500, detail="Failed to clear memories")
