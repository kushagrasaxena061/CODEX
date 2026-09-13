#!/bin/bash

echo "=========================================="
echo " FORCING REAL E2E PIPELINE EXECUTION      "
echo "=========================================="

echo "[1] DESTROYING OLD .env OVERRIDES & SETTING MODEL TO QWEN3..."
echo "WORKSPACE_ROOT=." > .env
echo "OLLAMA_MODEL_CODING=qwen3:latest" >> .env
echo "OLLAMA_MODEL_PLANNING=qwen3:latest" >> .env

cat << 'INNER_EOF' > backend/config/settings.py
from enum import Enum
from pydantic_settings import BaseSettings, SettingsConfigDict

class AutonomyLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class Settings(BaseSettings):
    WORKSPACE_ROOT: str = "."
    DATABASE_URL: str = "sqlite:///./codex.db"
    LOG_LEVEL: str = "INFO"
    AUTONOMY_LEVEL: AutonomyLevel = AutonomyLevel.MEDIUM
    
    OLLAMA_BASE_URL: str = "http://127.0.0.1:11434"
    OLLAMA_MODEL_CODING: str = "qwen3:latest"
    OLLAMA_MODEL_PLANNING: str = "qwen3:latest"
    OLLAMA_MODEL_FAST: str = "qwen3:latest"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
INNER_EOF

echo "[2] UPGRADING FILE MANAGER TO USE ABSOLUTE PATHS..."
cat << 'INNER_EOF' > backend/repository/file_manager.py
import os
import logging

logger = logging.getLogger(__name__)

class FileManager:
    def __init__(self, root_dir: str):
        self.root = os.path.abspath(root_dir) # Force absolute path to avoid directory confusion

    def read_file(self, path: str) -> str:
        full_path = os.path.join(self.root, path)
        if not os.path.exists(full_path):
            return ""
        with open(full_path, 'r', encoding='utf-8') as f:
            return f.read()

    def write_file(self, path: str, content: str):
        full_path = os.path.join(self.root, path)
        os.makedirs(os.path.dirname(full_path) or '.', exist_ok=True)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
INNER_EOF

echo "[3] ENSURING README.md EXISTS..."
cat << 'INNER_EOF' > README.md
# Codex AI Software Engineer

A local, autonomous, repository-aware multi-agent software engineering system powered primarily by Ollama.
INNER_EOF

echo "[4] RESTARTING BACKEND..."
# Kill any hanging uvicorn processes to ensure a clean slate
pkill -f uvicorn
sleep 2

source .venv/bin/activate
uvicorn backend.main:app --port 8000 > /dev/null 2>&1 &
BACKEND_PID=$!
sleep 4 

echo "[5] TRIGGERING REAL LLM TASK (Wait ~10-30 seconds)..."
curl -s -X POST http://127.0.0.1:8000/api/chat \
     -H "Content-Type: application/json" \
     -d '{"prompt": "Read the README.md file. Find the text \"Codex AI Software Engineer\" and replace it exactly with \"Codex AI Software Engineer (Real Pipeline Active)\"."}' | json_pp

kill $BACKEND_PID

echo -e "\n\n[Checking File System for Actual Changes]"
if grep -q "Real Pipeline Active" README.md; then
    echo "SUCCESS: FILE WAS MODIFIED INDEPENDENTLY!"
else
    echo "FAILURE: FILE WAS NOT MODIFIED."
    echo "--- CURRENT README CONTENT ---"
    cat README.md
    echo "------------------------------"
fi
