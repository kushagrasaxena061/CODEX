#!/bin/bash

echo "=========================================="
echo " IMPLEMENTING PHASE 1 & 2: REAL PIPELINE  "
echo "=========================================="

# 1. Implement Robust Ollama Client
cat << 'INNER_EOF' > backend/llm/ollama_client.py
import httpx
import logging
import json
from typing import Dict, Any
from backend.config.settings import settings

logger = logging.getLogger(__name__)

async def check_ollama_health() -> str:
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
            resp.raise_for_status()
            return "online"
    except Exception:
        return "offline"

async def generate_json(prompt: str, model: str, system: str = "") -> Dict[str, Any]:
    """Robust Ollama client with timeout, JSON enforcement, and error handling."""
    url = f"{settings.OLLAMA_BASE_URL}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "system": system,
        "stream": False,
        "format": "json"
    }
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            
            data = response.json()
            response_text = data.get("response", "{}")
            
            try:
                return json.loads(response_text)
            except json.JSONDecodeError:
                logger.error(f"Ollama returned malformed JSON: {response_text}")
                return {"error": "Malformed JSON", "raw": response_text}
                
    except httpx.ConnectError:
        return {"error": "Connection failed. Is Ollama running on port 11434?"}
    except httpx.TimeoutException:
        return {"error": "Ollama request timed out."}
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return {"error": f"Model '{model}' not found. You must pull it."}
        return {"error": f"HTTP {e.response.status_code}"}
    except Exception as e:
        return {"error": str(e)}
INNER_EOF

# 2. Implement True API Pipeline
cat << 'INNER_EOF' > backend/api/router.py
import logging
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.database.connection import get_db
from backend.memory.manager import MemoryManager
from backend.prompts.schemas import ExecutionPlan
from backend.agents.orchestrator import TaskOrchestrator
from backend.database.models import Conversation

router = APIRouter(prefix="/api", tags=["agent"])
logger = logging.getLogger(__name__)

class ChatRequest(BaseModel):
    prompt: str

@router.post("/chat")
async def submit_prompt(req: ChatRequest, db: Session = Depends(get_db)):
    logger.info(f"REAL PIPELINE INITIATED: {req.prompt}")
    manager = MemoryManager(db)
    
    # 1. Initialize persistent memory
    conv = db.query(Conversation).first()
    if not conv:
        conv = manager.create_conversation("Main Workspace")
        
    task = manager.add_task(conv.id, req.prompt)
    
    try:
        # 2. Pipeline Execution (To be upgraded with Prompt Optimizer in Phase 3)
        plan = ExecutionPlan(
            goal=req.prompt,
            implementation_steps=[f"Implement: {req.prompt}"],
            acceptance_criteria=["Execution succeeds"],
            risk_level="low"
        )
        
        # 3. Task Orchestrator Execution (Actually runs Code Agent & LLM)
        orchestrator = TaskOrchestrator(plan, max_iterations=2)
        result = await orchestrator.execute()
        
        # 4. Save result
        final_status = "SUCCESS" if result.status == "success" else "FAILED"
        manager.update_task_summary(task.id, final_status, result.message)
        
        return {
            "status": final_status.lower(),
            "prompt": req.prompt,
            "message": result.message,
            "data": result.data if hasattr(result, 'data') else {}
        }
    except Exception as e:
        logger.error(f"Pipeline error: {str(e)}")
        manager.update_task_summary(task.id, "FAILED", str(e))
        return {"status": "failed", "prompt": req.prompt, "message": str(e)}

@router.get("/status")
async def get_status():
    return {"status": "idle", "current_agent": None}
INNER_EOF

# 3. Verify the Pipeline actually executes
echo -e "\n[Booting Backend...]"
source .venv/bin/activate
uvicorn backend.main:app --port 8000 > /dev/null 2>&1 &
BACKEND_PID=$!
sleep 3 

echo -e "\n[Sending REAL task to Orchestrator]"
echo "Task: Replace 'Codex' with 'Codex (Real Pipeline Active)' in README.md"
curl -s -X POST http://127.0.0.1:8000/api/chat \
     -H "Content-Type: application/json" \
     -d '{"prompt": "Read the README.md file. Find the text \"Codex AI Software Engineer\" and replace it exactly with \"Codex AI Software Engineer (Real Pipeline Active)\"."}' | json_pp

kill $BACKEND_PID

echo -e "\n\n[Checking File System for Actual Changes]"
grep "Real Pipeline Active" README.md && echo "SUCCESS: FILE WAS MODIFIED." || echo "FAILURE: FILE WAS NOT MODIFIED."
