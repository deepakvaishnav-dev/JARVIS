import logging
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.brain.orchestrator import Orchestrator

logger = logging.getLogger(__name__)
router = APIRouter()

# Instantiate the global orchestrator once
orchestrator = Orchestrator()

@router.websocket("/stream")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    
    try:
        while True:
            # Receive text data from client
            user_message = await websocket.receive_text()
            
            if user_message == "__ping__":
                await websocket.send_json({"pong": True})
                continue
                
            logger.info(f"Received message: {user_message[:50]}...")
            
            try:
                # Call Orchestrator to handle intent routing and generation
                async for chunk in orchestrator.handle_request_stream(user_message):
                    # Yield token-by-token back to the client
                    await websocket.send_json({"token": chunk})
                    await asyncio.sleep(0.01)
                    
                # Send 'done' signal
                await websocket.send_json({"done": True})
                
            except Exception as e:
                logger.error(f"Unexpected Orchestrator Error: {e}")
                await websocket.send_json({"error": f"Error processing task: {str(e)}"})
                
    except WebSocketDisconnect:
        logger.info("Client disconnected from WebSocket.")
