#!/bin/bash

echo "=========================================="
echo " HARDENING LLM PROMPTS FOR STRICT JSON    "
echo "=========================================="

echo "[1] UPGRADING PLANNER AGENT PROMPT..."
cat << 'INNER_EOF' > backend/agents/planner.py
import logging
from backend.prompts.schemas import ExecutionPlan
from backend.llm.ollama_client import generate_json
from backend.config.settings import settings
from backend.repository.scanner import get_repo_tree

logger = logging.getLogger(__name__)

async def generate_plan(raw_prompt: str) -> ExecutionPlan:
    repo_tree = get_repo_tree()
    
    # Ironclad JSON template for the LLM
    system_prompt = (
        "You are a master Software Architect. Analyze the user request and the repository tree.\n"
        "You MUST output a JSON object EXACTLY matching this structure:\n"
        "{\n"
        "  \"goal\": \"string (The main objective of the task)\",\n"
        "  \"target_files\": [\"string (Exact paths of files to read, create, or edit)\"],\n"
        "  \"implementation_steps\": [\"string (Step by step instructions)\"],\n"
        "  \"acceptance_criteria\": [\"string (How to verify success)\"],\n"
        "  \"risk_level\": \"low\"\n"
        "}\n"
        "CRITICAL: Do NOT omit any fields. ALL fields are required."
    )
    
    prompt = f"USER REQUEST: {raw_prompt}\n\nREPOSITORY TREE:\n{repo_tree}"
    response = await generate_json(prompt, settings.OLLAMA_MODEL_PLANNING, system_prompt)
    
    if "error" in response:
        raise Exception(f"Planner LLM failed: {response['error']}")
        
    return ExecutionPlan(**response)
INNER_EOF

echo "[2] UPGRADING CODE AGENT PROMPT..."
cat << 'INNER_EOF' > backend/agents/code.py
import logging
import os
from backend.agents.base import AgentMessage
from backend.agents.code_schemas import CodeAction
from backend.llm.ollama_client import generate_json
from backend.config.settings import settings
from backend.repository.file_manager import FileManager

logger = logging.getLogger(__name__)

async def implement_step(step_description: str, files_context: dict, workspace_root: str) -> AgentMessage:
    system_prompt = (
        "You are an Expert AI Software Engineer. You are given a task and the contents of relevant files.\n"
        "You MUST output a JSON object EXACTLY matching this structure:\n"
        "{\n"
        "  \"thought_process\": \"string (Your reasoning)\",\n"
        "  \"edits\": [\n"
        "    {\n"
        "      \"file_path\": \"string (exact relative path)\",\n"
        "      \"search_block\": \"string (The EXACT existing text to replace, preserving all whitespace. Empty if creating a new file.)\",\n"
        "      \"replace_block\": \"string (The new text to insert)\"\n"
        "    }\n"
        "  ]\n"
        "}\n"
        "CRITICAL: Do NOT omit any fields. The search_block MUST match the file contents perfectly."
    )
    
    context_str = "\n".join([f"--- {path} ---\n{content}" for path, content in files_context.items()])
    prompt = f"TASK: {step_description}\n\nFILES CONTEXT:\n{context_str}"
    
    response = await generate_json(prompt, settings.OLLAMA_MODEL_CODING, system_prompt)
    
    if "error" in response:
        return AgentMessage(agent_name="code_agent", status="failed", message=response["error"], data=response)
        
    try:
        action = CodeAction(**response)
        fm = FileManager(workspace_root)
        
        applied_edits = []
        for edit in action.edits:
            try:
                current_content = fm.read_file(edit.file_path)
                
                # If creating a new file or search block is empty
                if not current_content or not edit.search_block:
                    fm.write_file(edit.file_path, edit.replace_block)
                    applied_edits.append(edit.file_path)
                elif edit.search_block in current_content:
                    new_content = current_content.replace(edit.search_block, edit.replace_block)
                    fm.write_file(edit.file_path, new_content)
                    applied_edits.append(edit.file_path)
                else:
                    logger.warning(f"Exact search block not found in {edit.file_path}")
            except Exception as e:
                logger.error(f"Failed to edit {edit.file_path}: {e}")
                
        if not applied_edits:
            return AgentMessage(agent_name="code_agent", status="failed", message="No edits were matched against the file system.", data={})
            
        return AgentMessage(
            agent_name="code_agent",
            status="success",
            message=action.thought_process,
            data={"files_changed": applied_edits}
        )
    except Exception as e:
        return AgentMessage(agent_name="code_agent", status="failed", message=f"Failed to parse or apply LLM response: {e}")
INNER_EOF

echo "[3] RESTARTING BACKEND..."
pkill -f uvicorn
sleep 2
source .venv/bin/activate
uvicorn backend.main:app --port 8000 > /dev/null 2>&1 &
BACKEND_PID=$!
sleep 4 

echo "[4] TRIGGERING MULTI-AGENT PIPELINE (Wait ~20-40 seconds)..."
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
