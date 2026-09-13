#!/bin/bash

echo "=========================================="
echo " PHASE 5 & 6: MULTI-AGENT PLANNING        "
echo "=========================================="

echo "[1] UPDATING SCHEMAS FOR TARGET FILES..."
cat << 'INNER_EOF' > backend/prompts/schemas.py
from pydantic import BaseModel, Field
from typing import List

class OptimizedTask(BaseModel):
    clarified_intent: str
    files_likely_affected: List[str]
    ambiguities: List[str]

class ExecutionPlan(BaseModel):
    goal: str = Field(..., description="The main objective of the task")
    target_files: List[str] = Field(default=[], description="Exact paths of files to read, create, or edit")
    implementation_steps: List[str] = Field(..., description="Step by step instructions for the code agent")
    acceptance_criteria: List[str] = Field(..., description="How to verify success")
    risk_level: str = Field(default="low")
INNER_EOF

echo "[2] IMPLEMENTING REPOSITORY SCANNER..."
cat << 'INNER_EOF' > backend/repository/scanner.py
import os
from backend.config.settings import settings

def get_repo_tree(root_dir: str = None) -> str:
    """Generates a token-efficient map of the repository."""
    root = root_dir or settings.WORKSPACE_ROOT
    tree = []
    ignore_dirs = {'.git', 'node_modules', '__pycache__', '.venv', 'dist', 'build'}
    
    for dirpath, dirnames, filenames in os.walk(root):
        # Modify dirnames in-place to ignore specific directories
        dirnames[:] = [d for d in dirnames if d not in ignore_dirs and not d.startswith('.')]
        
        level = dirpath.replace(root, '').count(os.sep)
        indent = ' ' * 4 * level
        folder_name = os.path.basename(dirpath)
        if folder_name:
            tree.append(f"{indent}{folder_name}/")
            
        subindent = ' ' * 4 * (level + 1)
        for f in filenames:
            if not f.startswith('.') and not f.endswith('.pyc'):
                tree.append(f"{subindent}{f}")
                
    # Return first 200 lines to protect LLM context window
    return "\n".join(tree[:200])
INNER_EOF

echo "[3] IMPLEMENTING PLANNER AGENT..."
cat << 'INNER_EOF' > backend/agents/planner.py
import logging
from backend.prompts.schemas import ExecutionPlan
from backend.llm.ollama_client import generate_json
from backend.config.settings import settings
from backend.repository.scanner import get_repo_tree

logger = logging.getLogger(__name__)

async def generate_plan(raw_prompt: str) -> ExecutionPlan:
    repo_tree = get_repo_tree()
    system_prompt = (
        "You are a master Software Architect. Analyze the user request and the repository structure. "
        "Output a JSON object matching the ExecutionPlan schema exactly.\n"
        "Crucially, populate 'target_files' with the exact paths of any files that need to be read, edited, or created."
    )
    
    prompt = f"USER REQUEST: {raw_prompt}\n\nREPOSITORY TREE:\n{repo_tree}"
    response = await generate_json(prompt, settings.OLLAMA_MODEL_PLANNING, system_prompt)
    
    if "error" in response:
        raise Exception(f"Planner LLM failed: {response['error']}")
        
    return ExecutionPlan(**response)
INNER_EOF

echo "[4] WIRING ROUTER TO PLANNER AGENT..."
cat << 'INNER_EOF' > backend/api/router.py
import logging
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.database.connection import get_db
from backend.memory.manager import MemoryManager
from backend.agents.planner import generate_plan
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
    
    conv = db.query(Conversation).first()
    if not conv:
        conv = manager.create_conversation("Main Workspace")
        
    task = manager.add_task(conv.id, req.prompt)
    
    try:
        # Phase 5/6: Dynamic Planning
        logger.info("Generating Execution Plan...")
        plan = await generate_plan(req.prompt)
        
        # Phase 6: Orchestrator execution
        orchestrator = TaskOrchestrator(plan, max_iterations=2)
        result = await orchestrator.execute()
        
        final_status = "SUCCESS" if result.status == "success" else "FAILED"
        manager.update_task_summary(task.id, final_status, result.message)
        
        return {
            "status": final_status.lower(),
            "prompt": req.prompt,
            "message": result.message,
            "plan": plan.dict(),
            "data": result.data if hasattr(result, 'data') else {}
        }
    except Exception as e:
        logger.error(f"Pipeline error: {str(e)}")
        manager.update_task_summary(task.id, "FAILED", str(e))
        return {"status": "failed", "prompt": req.prompt, "message": str(e)}

@router.get("/status")
async def get_status():
    return {"status": "idle"}
INNER_EOF

echo "[5] UPGRADING ORCHESTRATOR TARGET INJECTION..."
cat << 'INNER_EOF' > backend/agents/orchestrator.py
import logging
from backend.prompts.schemas import ExecutionPlan
from backend.agents.base import AgentMessage
from backend.agents.code import implement_step
from backend.config.settings import settings
from backend.repository.file_manager import FileManager

logger = logging.getLogger(__name__)

class TaskOrchestrator:
    def __init__(self, plan: ExecutionPlan, max_iterations: int = 2):
        self.plan = plan
        self.state = "PLANNED"
        self.iterations = 0
        self.max_iterations = max_iterations

    async def execute(self) -> AgentMessage:
        fm = FileManager(settings.WORKSPACE_ROOT)
        
        while self.iterations < self.max_iterations:
            self.iterations += 1
            self.state = "IMPLEMENTING"
            
            # Use Planner's targeted files
            mentioned_files = self.plan.target_files
            if not mentioned_files:
                mentioned_files = ["README.md"] # Fallback
                
            files_context = {}
            for f in mentioned_files:
                content = fm.read_file(f)
                # If content is empty, file doesn't exist yet - Code Agent will create it
                files_context[f] = content if content else "(File does not exist yet. Please create it.)"
                    
            # Let Code Agent act
            code_result = await implement_step(self.plan.goal, files_context, settings.WORKSPACE_ROOT)
            
            if code_result.status == "failed":
                self.state = "FAILED"
                return code_result
                
            self.state = "SUCCESS"
            return AgentMessage(
                agent_name="orchestrator", 
                status="success", 
                message=f"Success! Agent thought: {code_result.message}", 
                data=code_result.data
            )
            
        self.state = "FAILED"
        return AgentMessage(agent_name="orchestrator", status="failed", message="Max retries exceeded.")
INNER_EOF

echo "[6] RESTARTING BACKEND..."
pkill -f uvicorn
sleep 2
source .venv/bin/activate
uvicorn backend.main:app --port 8000 > /dev/null 2>&1 &
BACKEND_PID=$!
sleep 4 

echo "[7] TRIGGERING MULTI-AGENT PIPELINE (Wait ~20-40 seconds for Planner + Coder)..."
# We are asking it to create a brand new file
curl -s -X POST http://127.0.0.1:8000/api/chat \
     -H "Content-Type: application/json" \
     -d '{"prompt": "Create a new file in the root directory called architecture.md. Inside it, write a single markdown header that says # Codex Architecture."}' | json_pp

kill $BACKEND_PID

echo -e "\n\n[Checking File System for architecture.md]"
if [ -f "architecture.md" ]; then
    echo "SUCCESS: NEW FILE WAS CREATED BY THE MULTI-AGENT SYSTEM!"
    cat architecture.md
else
    echo "FAILURE: FILE WAS NOT CREATED."
fi
