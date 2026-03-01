import logging
from typing import List

logger = logging.getLogger(__name__)

class ResponseAggregator:
    """
    Merges outputs from multiple agents/tasks into a final coherent answer.
    """
    def __init__(self):
        pass

    async def aggregate(self, results: List[str]) -> str:
        if not results:
            return "Task completed."
        if len(results) == 1:
            return results[0]
            
        # For multi-agent parallel responses:
        merged = "\n\n".join([f"--- Agent Response ---\n{r}" for r in results])
        return f"**Aggregated Results:**\n\n{merged}"
