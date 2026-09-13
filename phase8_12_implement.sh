#!/bin/bash

echo "=========================================="
echo " PHASES 8-12: VERIFICATION & SELF-HEALING "
echo "=========================================="

echo "[1] PATCHING FILE MANAGER PATH SECURITY..."
cat << 'INNER_EOF' > backend/repository/file_manager.py
import os
import logging

logger = logging.getLogger(__name__)

class FileManager:
    def __init__(self, root_dir: str):
        self.root = os.path.abspath(root_dir)

    def _safe_path(self, path: str) -> str:
        # Strip leading slashes so os.path.join doesn't jump to the OS root
        return os.path.join(self.root, path.lstrip('/\\'))

    def read_file(self, path: str) -> str:
        full_path = self._safe_path(path)
        if not os.path.exists(full_path):
            return ""
        with open(full_path, 'r', encoding='utf-8') as f:
            return f.read()

    def write_file(self, path: str, content: str):
        full_path = self._safe_path(path)
        os.makedirs(os.path.dirname(full_path) or '.', exist_ok=True)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
INNER_EOF

echo "[2] IMPLEMENTING TERMINAL (Phase 8)..."
cat << 'INNER_EOF' > backend/execution/terminal.py
import asyncio
import logging

logger = logging.getLogger(__name__)

class Terminal:
    def __init__(self, cwd: str):
        self.cwd = cwd

    async def run(self, command: str, timeout: int = 15) -> dict:
        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.cwd
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            return {
                "exit_code": proc.returncode,
                "stdout": stdout.decode().strip(),
                "stderr": stderr.decode().strip()
            }
        except asyncio.TimeoutError:
            return {"exit_code": -1, "stdout": "", "stderr": "Command timed out."}
        except Exception as e:
            return {"exit_code": -1, "stdout": "", "stderr": str(e)}
INNER_EOF

echo "[3] IMPLEMENTING VERIFICATION & DEBUG AGENTS (Phase 9 & 12)..."
cat << 'INNER_EOF' > backend/agents/verifier.py
import logging
from backend.prompts.schemas import ExecutionPlan
from backend.llm.ollama_client import generate_json
from backend.config.settings import settings
from backend.repository.file_manager import FileManager

logger = logging.getLogger(__name__)

async def verify_plan(plan: ExecutionPlan) -> tuple[bool, str]:
    fm = FileManager(settings.WORKSPACE_ROOT)
    
    evidence = ""
    for f in plan.target_files:
        content = fm.read_file(f)
        evidence += f"--- {f} ---\n{content}\n\n"
        
    system_prompt = (
        "You are a strict QA Verification Agent. Review the acceptance criteria and the actual file evidence.\n"
        "You MUST output a JSON object EXACTLY matching this structure:\n"
        "{\n"
        "  \"passed\": boolean,\n"
        "  \"reason\": \"string (Explanation of why it passed or exactly what is wrong)\"\n"
        "}\n"
        "CRITICAL: Be unforgiving. If the evidence does not PERFECTLY match the criteria, 'passed' must be false."
    )
    
    prompt = f"ACCEPTANCE CRITERIA:\n{plan.acceptance_criteria}\n\nACTUAL FILE EVIDENCE:\n{evidence}"
    response = await generate_json(prompt, settings.OLLAMA_MODEL_FAST, system_prompt)
    
    if "error" in response:
        return False, f"Verifier LLM Error: {response['error']}"
        
    return response.get("passed", False), response.get("reason", "No reason provided.")
INNER_EOF

cat << 'INNER_EOF' > backend/agents/debug.py
import logging
from backend.llm.ollama_client import generate_json
from backend.config.settings import settings

logger = logging.getLogger(__name__)

async def generate_fix(error_reason: str, failed_step: str) -> str:
    system_prompt = (
        "You are a Debugging Agent. The previous code change failed QA verification.\n"
        "You MUST output a JSON object EXACTLY matching this structure:\n"
        "{\n"
        "  \"corrected_instructions\": \"string (Clear, updated step-by-step instructions for the Code Agent to fix the failure)\"\n"
        "}\n"
        "CRITICAL: Do NOT omit any fields."
    )
    prompt = f"ORIGINAL TASK: {failed_step}\nQA VERIFICATION FAILURE:\n{error_reason}"
    
    response = await generate_json(prompt, settings.OLLAMA_MODEL_FAST, system_prompt)
    if "error" in response:
        return f"Fix the errors. Previous attempt failed: {error_reason}"
        
    return response.get("corrected_instructions", f"Fix the errors: {error_reason}")
INNER_EOF

echo "[4] WIRING ORCHESTRATOR FOR SELF-HEALING..."
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
    def __init__(self, plan: ExecutionPlan, max_iterations: int = 3):
        self.plan = plan
        self.state = "PLANNED"
        self.iterations = 0
        self.max_iterations = max_iterations
        self.current_instruction = self.plan.goal

    async def execute(self) -> AgentMessage:
        fm = FileManager(settings.WORKSPACE_ROOT)
        
        while self.iterations < self.max_iterations:
            self.iterations += 1
            
            # --- IMPLEMENTATION PHASE ---
            self.state = "IMPLEMENTING"
            mentioned_files = self.plan.target_files if self.plan.target_files else ["README.md"]
                
            files_context = {}
            for f in mentioned_files:
                content = fm.read_file(f)
                files_context[f] = content if content else "(File does not exist yet.)"
                    
            logger.info(f"Iteration {self.iterations}: Coding...")
            code_result = await implement_step(self.current_instruction, files_context, settings.WORKSPACE_ROOT)
            
            if code_result.status == "failed":
                self.state = "FAILED"
                return code_result
                
            # --- VERIFICATION PHASE ---
            self.state = "VERIFYING"
            logger.info("Verifying changes...")
            passed, reason = await verify_plan(self.plan)
            
            if passed:
                self.state = "SUCCESS"
                return AgentMessage(
                    agent_name="orchestrator", 
                    status="success", 
                    message=f"Verified successfully in {self.iterations} iterations. QA Note: {reason}", 
                    data=code_result.data
                )
            else:
                # --- SELF-HEALING PHASE ---
                self.state = "DEBUGGING"
                logger.warning(f"Verification failed: {reason}. Generating fix...")
                self.current_instruction = await generate_fix(reason, self.current_instruction)
                
        self.state = "FAILED"
        return AgentMessage(agent_name="orchestrator", status="failed", message=f"Max retries exceeded. Last QA Error: {reason}")
INNER_EOF

echo "[5] RESTARTING BACKEND..."
pkill -f uvicorn
sleep 2
source .venv/bin/activate
uvicorn backend.main:app --port 8000 > /dev/null 2>&1 &
BACKEND_PID=$!
sleep 4 

echo "[6] TRIGGERING SELF-HEALING TASK (Wait ~30-60 seconds)..."
echo "We are explicitly demanding '# Codex Architecture' to force the system to correct its previous hallucination."

curl -s -X POST http://127.0.0.1:8000/api/chat \
     -H "Content-Type: application/json" \
     -d '{"prompt": "Read architecture.md. Replace whatever header is in there so it explicitly says # Codex Architecture and absolutely nothing else."}' | json_pp

kill $BACKEND_PID

echo -e "\n\n[Checking File System for Corrected architecture.md]"
cat architecture.md
