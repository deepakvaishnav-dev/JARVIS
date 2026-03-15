from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "JARVIS OS"
    GEMINI_API_KEY: str = ""
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    API_KEY: str = "your_secret_api_key_here"  # Default placeholder
    RATE_LIMIT_DEFAULT: str = "100/minute"
    RATE_LIMIT_VOICE: str = "10/minute"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
