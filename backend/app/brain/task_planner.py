import logging
from typing import List
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class PlannedTask(BaseModel):
    id: int
    description: str
    agent_type: str

class TaskPlanner:
    """
    Decomposes multi-step user requests into sequential sub-tasks.
    Currently a simplified pass-through for Phase 2 MVP.
    """
    def __init__(self):
        pass

    async def decompose(self, request: str, primary_agent: str) -> List[PlannedTask]:
        logger.info(f"Task Planner evaluating: {request}")
        # MVP: single step execution
        return [PlannedTask(id=1, description=request, agent_type=primary_agent)]
