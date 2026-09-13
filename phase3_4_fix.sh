#!/bin/bash

echo "=========================================="
echo " FIXING WORKSPACE PATH & PULLING LLM      "
echo "=========================================="

echo -e "\n[1] UPDATING SETTINGS TO POINT TO PROJECT ROOT..."
cat << 'INNER_EOF' > backend/config/settings.py
from enum import Enum
from pydantic_settings import BaseSettings, SettingsConfigDict

class AutonomyLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class Settings(BaseSettings):
    # Changed from ./workspaces to . so it can see the project's README.md
    WORKSPACE_ROOT: str = "." 
    DATABASE_URL: str = "sqlite:///./codex.db"
    LOG_LEVEL: str = "INFO"
    AUTONOMY_LEVEL: AutonomyLevel = AutonomyLevel.MEDIUM
    
    # Using the lightweight 'latest' model to avoid timeouts
    OLLAMA_BASE_URL: str = "http://127.0.0.1:11434"
    OLLAMA_MODEL_CODING: str = "deepseek-coder:latest"
    OLLAMA_MODEL_PLANNING: str = "llama3:latest"
    OLLAMA_MODEL_FAST: str = "phi3:latest"

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
INNER_EOF

echo -e "\n[2] PULLING LIGHTWEIGHT CODING MODEL..."
# This is ~700MB and should not time out
ollama pull deepseek-coder:latest

echo -e "\n[3] ENSURING README.md EXISTS..."
cat << 'INNER_EOF' > README.md
# Codex AI Software Engineer

A local, autonomous, repository-aware multi-agent software engineering system powered primarily by Ollama.
INNER_EOF

echo -e "\n[4] RE-VERIFYING END-TO-END EXECUTION..."
source .venv/bin/activate
uvicorn backend.main:app --port 8000 > /dev/null 2>&1 &
BACKEND_PID=$!
sleep 3 

echo "-> Triggering real LLM pipeline (Wait ~10-20 seconds for the model to think)..."
curl -s -X POST http://127.0.0.1:8000/api/chat \
     -H "Content-Type: application/json" \
     -d '{"prompt": "Read the README.md file. Find the text \"Codex AI Software Engineer\" and replace it exactly with \"Codex AI Software Engineer (Real Pipeline Active)\"."}' | json_pp

kill $BACKEND_PID

echo -e "\n\n[Checking File System for Actual Changes]"
grep "Real Pipeline Active" README.md && echo "SUCCESS: FILE WAS MODIFIED INDEPENDENTLY." || echo "FAILURE: FILE WAS NOT MODIFIED."
