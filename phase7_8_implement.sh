#!/bin/bash

echo "=========================================="
echo " PHASE 7 & 8: TERMINAL EXECUTION & QA FIX "
echo "=========================================="

echo "[1] FIXING VERIFIER STRICTNESS..."
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
        content = fm.read_file(f).strip() # Strip surrounding whitespace to prevent LLM pedantry
        evidence += f"--- {f} ---\n{content}\n\n"
        
    system_prompt = (
        "You are a QA Verification Agent. Review the acceptance criteria and the actual file evidence.\n"
        "You MUST output a JSON object EXACTLY matching this structure:\n"
        "{\n"
        "  \"passed\": boolean,\n"
        "  \"reason\": \"string (Explanation)\"\n"
        "}\n"
        "CRITICAL: If the semantic intent is met, passed must be true. Ignore trivial whitespace differences."
    )
    
    prompt = f"ACCEPTANCE CRITERIA:\n{plan.acceptance_criteria}\n\nEVIDENCE:\n{evidence}"
    response = await generate_json(prompt, settings.OLLAMA_MODEL_FAST, system_prompt)
    
    if "error" in response:
        return False, f"Verifier Error: {response['error']}"
        
    return response.get("passed", False), response.get("reason", "No reason.")
INNER_EOF

echo "[2] UPGRADING CODE SCHEMAS WITH TERMINAL CAPABILITIES..."
cat << 'INNER_EOF' > backend/agents/code_schemas.py
from pydantic import BaseModel, Field
from typing import List

class FileEdit(BaseModel):
    file_path: str = Field(..., description="Path to the file relative to workspace root")
    search_block: str = Field(..., description="The exact existing code block to replace.")
    replace_block: str = Field(..., description="The new code block to insert")

class CodeAction(BaseModel):
    thought_process: str = Field(..., description="Implementation strategy")
    edits: List[FileEdit] = Field(default=[], description="File modifications")
    commands: List[str] = Field(default=[], description="Terminal commands to run")
INNER_EOF

echo "[3] UPGRADING CODE AGENT WITH TERMINAL EXECUTION..."
cat << 'INNER_EOF' > backend/agents/code.py
import logging
from backend.agents.base import AgentMessage
from backend.agents.code_schemas import CodeAction
from backend.llm.ollama_client import generate_json
from backend.config.settings import settings
from backend.repository.file_manager import FileManager
from backend.execution.terminal import Terminal

logger = logging.getLogger(__name__)

async def implement_step(step_description: str, files_context: dict, workspace_root: str) -> AgentMessage:
    system_prompt = (
        "You are an Expert AI Software Engineer. You can edit files and run terminal commands.\n"
        "You MUST output a JSON object EXACTLY matching this structure:\n"
        "{\n"
        "  \"thought_process\": \"string (Your reasoning)\",\n"
        "  \"edits\": [\n"
        "    {\n"
        "      \"file_path\": \"string\",\n"
        "      \"search_block\": \"string (Exact text to replace. Empty if creating new file)\",\n"
        "      \"replace_block\": \"string (New text)\"\n"
        "    }\n"
        "  ],\n"
        "  \"commands\": [\"string (Optional: Terminal commands to run after edits, e.g., 'python3 script.py')\"]\n"
        "}\n"
        "CRITICAL: Do NOT omit any fields."
    )
    
    context_str = "\n".join([f"--- {path} ---\n{content}" for path, content in files_context.items()])
    prompt = f"TASK: {step_description}\n\nFILES CONTEXT:\n{context_str}"
    
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
                logger.error(f"File Edit Error: {e}")
                
        cmd_logs = []
        for cmd in action.commands:
            res = await term.run(cmd)
            cmd_logs.append(f"$ {cmd}\nEXIT CODE: {res['exit_code']}\nSTDOUT: {res['stdout']}\nSTDERR: {res['stderr']}")
            
        msg = action.thought_process
        if cmd_logs:
            msg += "\n\n--- Terminal Output ---\n" + "\n".join(cmd_logs)
            
        return AgentMessage(
            agent_name="code_agent",
            status="success",
            message=msg,
            data={"files_changed": applied_edits, "terminal_logs": cmd_logs}
        )
    except Exception as e:
        return AgentMessage(agent_name="code_agent", status="failed", message=f"Parse Error: {e}")
INNER_EOF

echo "[4] RESTARTING BACKEND..."
pkill -f uvicorn
sleep 2
source .venv/bin/activate
uvicorn backend.main:app --port 8000 > /dev/null 2>&1 &
BACKEND_PID=$!
sleep 4 

echo "[5] TRIGGERING TERMINAL & FILE TASK (Wait ~30-60 seconds)..."
curl -s -X POST http://127.0.0.1:8000/api/chat \
     -H "Content-Type: application/json" \
     -d '{"prompt": "Create a file named script.py that prints exactly Hello Codex. Then execute it using python3."}' | json_pp

kill $BACKEND_PID

echo -e "\n\n[Checking File System for script.py]"
cat script.py
