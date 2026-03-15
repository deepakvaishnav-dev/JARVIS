import logging
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.routes import chat, voice, memory
from app.tools.scheduler import start_scheduler, stop_scheduler, schedule_task, heartbeat_job, CronTrigger
from app.security import setup_exception_handlers, verify_api_key
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    start_scheduler()
    # Add a simple debug heartbeat job every minute
    schedule_task("heartbeat", heartbeat_job, CronTrigger(minute='*'))
    yield
    # Shutdown
    stop_scheduler()

# Configure standard logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

# Initialize app with global API Key dependency
app = FastAPI(
    title=settings.PROJECT_NAME, 
    lifespan=lifespan,
    dependencies=[Depends(verify_api_key)]
)

# Setup security handlers (Rate Limiting & Error masking)
setup_exception_handlers(app)

# CORS Middleware Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check route
@app.get("/health")
async def health_check():
    return {"status": "ok"}

# Include routers
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
app.include_router(voice.router, prefix="/api/v1/voice", tags=["voice"])
app.include_router(memory.router, prefix="/api/v1/memory", tags=["memory"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
