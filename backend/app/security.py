import logging
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.requests import HTTPConnection
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.config import settings

logger = logging.getLogger(__name__)

# Initialize rate limiter using client IP
limiter = Limiter(key_func=get_remote_address, default_limits=[settings.RATE_LIMIT_DEFAULT])

async def verify_api_key(connection: HTTPConnection):
    """Dependency to check for API Custom Header"""
    api_key_header = connection.headers.get("X-API-Key") or connection.query_params.get("api_key")
    
    # In development, you might bypass this if the key is default/empty
    if settings.API_KEY == "your_secret_api_key_here":
        return
        
    if api_key_header != settings.API_KEY:
        logger.warning(f"Unauthorized access attempt from {connection.client.host if connection.client else 'Unknown'}")
        raise HTTPException(status_code=401, detail="Invalid API Key")

def setup_exception_handlers(app):
    """Configures global structured error handling to prevent leaking tracebacks."""
    
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": True, "message": exc.detail},
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled Server Error: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": True, "message": "Internal Server Error. Please try again later."},
        )
