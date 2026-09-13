from enum import Enum
from pydantic_settings import BaseSettings, SettingsConfigDict

class AutonomyLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class Settings(BaseSettings):
    # CRITICAL FIX: The AI is now permanently restricted to this folder.
    WORKSPACE_ROOT: str = "./isolated_workspace"
    DATABASE_URL: str = "sqlite:///./codex.db"
    LOG_LEVEL: str = "INFO"
    AUTONOMY_LEVEL: AutonomyLevel = AutonomyLevel.MEDIUM
    
    OLLAMA_BASE_URL: str = "http://127.0.0.1:11434"
    OLLAMA_MODEL_CODING: str = "qwen3:latest"
    OLLAMA_MODEL_PLANNING: str = "qwen3:latest"
    OLLAMA_MODEL_FAST: str = "qwen3:latest"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
