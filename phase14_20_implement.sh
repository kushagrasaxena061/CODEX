#!/bin/bash

echo "=========================================="
echo " PHASE 14 & 20: MEMORY & GIT INTEGRATION  "
echo "=========================================="

echo "[1] IMPLEMENTING REAL GIT MANAGER (Phase 20)..."
cat << 'INNER_EOF' > backend/git/manager.py
import subprocess
import os
import logging
from backend.config.settings import settings

logger = logging.getLogger(__name__)

class GitManager:
    def __init__(self, repo_path: str = None):
        self.repo_path = repo_path or settings.WORKSPACE_ROOT
        self._init_if_needed()

    def _run(self, cmd: str) -> str:
        try:
            result = subprocess.run(cmd, cwd=self.repo_path, shell=True, capture_output=True, text=True)
            return result.stdout.strip()
        except Exception as e:
            logger.error(f"Git command failed: {e}")
            return ""

    def _init_if_needed(self):
        if not os.path.exists(os.path.join(self.repo_path, '.git')):
            self._run("git init")
            self._run("git config user.name 'Codex AI'")
            self._run("git config user.email 'codex@autonomous.local'")

    def commit(self, message: str) -> str:
        self._run("git add .")
        # Clean up message for CLI safely
        safe_msg = message.replace('"', "'")
        return self._run(f'git commit -m "{safe_msg}"')
        
    def get_log(self) -> str:
        return self._run("git log --oneline -n 3")
INNER_EOF

echo "[2] UPGRADING PLANNER WITH MEMORY (Phase 14)..."
cat << 'INNER_EOF' > backend/agents/planner.py
import logging
from backend.prompts.schemas import ExecutionPlan
from backend.llm.ollama_client import generate_json
from backend.config.settings import settings
from backend.repository.scanner import get_repo_tree

logger = logging.getLogger(__name__)

async def generate_plan(raw_prompt: str, history: str = "") -> ExecutionPlan:
    repo_tree = get_repo_tree()
    
    system_prompt = (
        "You are a Software Architect. Analyze the user request, the conversation history, and the repo tree.\n"
        "You MUST output a JSON object EXACTLY matching this structure:\n"
        "{\n"
        "  \"goal\": \"string (The main objective of the task)\",\n"
        "  \"target_files\": [\"string (Exact paths)\"],\n"
        "  \"implementation_steps\": [\"string\"],\n"
        "  \"acceptance_criteria\": [\"string\"],\n"
        "  \"risk_level\": \"low\"\n"
        "}\n"
        "CRITICAL: ALL fields are required."
    )
    
    prompt = f"CONVERSATION HISTORY:\n{history}\n\nUSER REQUEST: {raw_prompt}\n\nREPOSITORY TREE:\n{repo_tree}"
    response = await generate_json(prompt, settings.OLLAMA_MODEL_PLANNING, system_prompt)
    
    if "error" in response:
        raise Exception(f"Planner LLM failed: {response['error']}")
        
    return ExecutionPlan(**response)
INNER_EOF

echo "[3] UPGRADING CODE AGENT WITH MEMORY..."
cat << 'INNER_EOF' > backend/agents/code.py
import logging
from backend.agents.base import AgentMessage
from backend.agents.code_schemas import CodeAction
from backend.llm.ollama_client import generate_json
from backend.config.settings import settings
from backend.repository.file_manager import FileManager
from backend.execution.terminal import Terminal

logger = logging.getLogger(__name__)

async def implement_step(step_description: str, files_context: dict, workspace_root: str, history: str = "") -> AgentMessage:
    system_prompt = (
        "You are an Expert AI Software Engineer.\n"
        "You MUST output a JSON object EXACTLY matching this structure:\n"
        "{\n"
        "  \"thought_process\": \"string\",\n"
        "  \"edits\": [{\"file_path\": \"string\", \"search_block\": \"string\", \"replace_block\": \"string\"}],\n"
        "  \"commands\": [\"string\"]\n"
        "}\n"
    )
    
    context_str = "\n".join([f"--- {path} ---\n{content}" for path, content in files_context.items()])
    prompt = f"HISTORY:\n{history}\n\nTASK: {step_description}\n\nFILES:\n{context_str}"
    
    response = await generate_json(prompt, settings.OLLAMA_MODEL_CODING, system_prompt)
    
    if "error" in response:
        return AgentMessage(agent_name="code_agent", status="failed", message=response["error"])
        
    try:
        action = CodeAction(**response)
        fm = FileManager(workspace_root)
        term = Terminal(workspace_root)
        
        applied_edits = []
        for edit in action.edits:
            try:
                current_content = fm.read_file(edit.file_path)
                if not current_content or not edit.search_block:
                    fm.write_file(edit.file_path, edit.replace_block)
                    applied_edits.append(edit.file_path)
                elif edit.search_block in current_content:
                    new_content = current_content.replace(edit.search_block, edit.replace_block)
                    fm.write_file(edit.file_path, new_content)
                    applied_edits.append(edit.file_path)
            except Exception as e:
                pass
                
        cmd_logs = []
        for cmd in action.commands:
            res = await term.run(cmd)
            cmd_logs.append(f"$ {cmd}\nEXIT CODE: {res['exit_code']}\nSTDOUT: {res['stdout']}")
            
        return AgentMessage(
            agent_name="code_agent", status="success",
            message=action.thought_process, data={"files_changed": applied_edits, "terminal_logs": cmd_logs}
        )
    except Exception as e:
        return AgentMessage(agent_name="code_agent", status="failed", message=f"Parse Error: {e}")
INNER_EOF

echo "[4] WIRING ORCHESTRATOR TO ACCEPT MEMORY..."
cat << 'INNER_EOF' > backend/agents/orchestrator.py
import logging
from backend.prompts.schemas import ExecutionPlan
from backend.agents.base import AgentMessage
from backend.agents.code import implement_step
from backend.agents.verifier import verify_plan
from backend.agents.debug import generate_fix
from backend.config.settings import settings
from backend.repository.file_manager import FileManager

logger = logging.getLogger(__name__)

class TaskOrchestrator:
    def __init__(self, plan: ExecutionPlan, history: str = "", max_iterations: int = 3):
        self.plan = plan
        self.history = history
        self.state = "PLANNED"
        self.iterations = 0
        self.max_iterations = max_iterations
        self.current_instruction = self.plan.goal

    async def execute(self) -> AgentMessage:
        fm = FileManager(settings.WORKSPACE_ROOT)
        
        while self.iterations < self.max_iterations:
            self.iterations += 1
            self.state = "IMPLEMENTING"
            mentioned_files = self.plan.target_files if self.plan.target_files else ["README.md"]
                
            files_context = {}
            for f in mentioned_files:
                content = fm.read_file(f)
                files_context[f] = content if content else "(File does not exist yet.)"
                    
            code_result = await implement_step(self.current_instruction, files_context, settings.WORKSPACE_ROOT, self.history)
            
            if code_result.status == "failed":
                return code_result
                
            self.state = "VERIFYING"
            passed, reason = await verify_plan(self.plan)
            
            if passed:
                self.state = "SUCCESS"
                return AgentMessage(agent_name="orchestrator", status="success", message=f"Success: {reason}", data=code_result.data)
            else:
                self.state = "DEBUGGING"
                self.current_instruction = await generate_fix(reason, self.current_instruction)
                
        self.state = "FAILED"
        return AgentMessage(agent_name="orchestrator", status="failed", message=f"Max retries exceeded.")
INNER_EOF

echo "[5] UPDATING ROUTER TO PASS MEMORY & TRIGGER GIT COMMIT..."
cat << 'INNER_EOF' > backend/api/router.py
import logging
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.database.connection import get_db
from backend.memory.manager import MemoryManager
from backend.agents.planner import generate_plan
from backend.agents.orchestrator import TaskOrchestrator
from backend.database.models import Conversation, Task
from backend.git.manager import GitManager

router = APIRouter(prefix="/api", tags=["agent"])
logger = logging.getLogger(__name__)

class ChatRequest(BaseModel):
    prompt: str

@router.post("/chat")
async def submit_prompt(req: ChatRequest, db: Session = Depends(get_db)):
    manager = MemoryManager(db)
    git = GitManager()
    
    conv = db.query(Conversation).first()
    if not conv:
        conv = manager.create_conversation("Main Workspace")
        
    # Extract Conversation History for Memory (Phase 14)
    recent_tasks = db.query(Task).filter(Task.conversation_id == conv.id).order_by(Task.created_at.asc()).all()[-4:]
    history = "\n".join([f"User: {t.prompt}\nSystem: {t.context_summary}" for t in recent_tasks if t.context_summary])
        
    task = manager.add_task(conv.id, req.prompt)
    
    try:
        plan = await generate_plan(req.prompt, history)
        orchestrator = TaskOrchestrator(plan, history=history, max_iterations=2)
        result = await orchestrator.execute()
        
        final_status = "SUCCESS" if result.status == "success" else "FAILED"
        manager.update_task_summary(task.id, final_status, result.message)
        
        # Git Commit (Phase 20)
        if final_status == "SUCCESS":
            git.commit(f"Codex AI: {req.prompt[:50]}")
            
        return {
            "status": final_status.lower(),
            "prompt": req.prompt,
            "message": result.message,
            "data": result.data if hasattr(result, 'data') else {}
        }
    except Exception as e:
        manager.update_task_summary(task.id, "FAILED", str(e))
        return {"status": "failed", "prompt": req.prompt, "message": str(e)}
INNER_EOF

echo "[6] RESTARTING BACKEND..."
pkill -f uvicorn
sleep 2
source .venv/bin/activate
uvicorn backend.main:app --port 8000 > /dev/null 2>&1 &
BACKEND_PID=$!
sleep 4 

echo "[7] EXECUTING TASK 1 (Setting Baseline)..."
curl -s -X POST http://127.0.0.1:8000/api/chat \
     -H "Content-Type: application/json" \
     -d '{"prompt": "Create a file called memory_test.txt and write the word RED in it."}' > /dev/null

echo "[8] EXECUTING TASK 2 (Vague Follow-Up testing Memory Phase 14)..."
echo "Sending: 'Now add BLUE to that file.'"
curl -s -X POST http://127.0.0.1:8000/api/chat \
     -H "Content-Type: application/json" \
     -d '{"prompt": "Now add BLUE to that file."}' | json_pp

kill $BACKEND_PID

echo -e "\n\n[Checking File System for memory_test.txt]"
cat memory_test.txt

echo -e "\n\n[Checking Git Log (Phase 20)]"
python -c "from backend.git.manager import GitManager; print(GitManager().get_log())"
