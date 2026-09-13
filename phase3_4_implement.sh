#!/bin/bash

echo "=========================================="
echo " PHASE 3 & 4: REAL CONTEXT & LLM EXECUTION"
echo "=========================================="

echo -e "\n[1] PULLING MISSING MODEL (This may take a minute)..."
ollama pull deepseek-coder:6.7b

echo -e "\n[2] IMPLEMENTING REAL FILE MANAGER (Phase 4)..."
cat << 'INNER_EOF' > backend/repository/file_manager.py
import os
import logging

logger = logging.getLogger(__name__)

class FileManager:
    def __init__(self, root_dir: str):
        self.root = root_dir

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

echo -e "\n[3] UPGRADING CODE AGENT TO APPLY REAL EDITS..."
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
        "Return a JSON object containing a 'thought_process' and a list of 'edits' to implement the task.\n"
        "Each edit MUST have 'file_path', 'search_block' (the EXACT existing text to replace, preserving all whitespace), "
        "and 'replace_block' (the new text to insert)."
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
                if edit.search_block and edit.search_block in current_content:
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

echo -e "\n[4] UPGRADING ORCHESTRATOR TO FEED REAL CONTEXT..."
cat << 'INNER_EOF' > backend/agents/orchestrator.py
import logging
import re
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
            
            # Phase 4: Naive repository context extraction (To be expanded)
            mentioned_files = re.findall(r'[\w\.\-/]+\.\w+', self.plan.goal)
            if not mentioned_files:
                mentioned_files = ["README.md"] # Fallback if no specific file is found in prompt
                
            files_context = {}
            for f in mentioned_files:
                content = fm.read_file(f)
                if content:
                    files_context[f] = content
                    
            if not files_context:
                return AgentMessage(agent_name="orchestrator", status="failed", message="Could not locate target files on disk.")
                
            # Execute with real context
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

echo -e "\n[5] VERIFYING END-TO-END EXECUTION..."
source .venv/bin/activate
uvicorn backend.main:app --port 8000 > /dev/null 2>&1 &
BACKEND_PID=$!
sleep 3 

echo "-> Triggering real LLM pipeline (Wait ~10 seconds for the model to think)..."
curl -s -X POST http://127.0.0.1:8000/api/chat \
     -H "Content-Type: application/json" \
     -d '{"prompt": "Read the README.md file. Find the text \"Codex AI Software Engineer\" and replace it exactly with \"Codex AI Software Engineer (Real Pipeline Active)\"."}' | json_pp

kill $BACKEND_PID

echo -e "\n\n[Checking File System for Actual Changes]"
grep "Real Pipeline Active" README.md && echo "SUCCESS: FILE WAS MODIFIED INDEPENDENTLY." || echo "FAILURE: FILE WAS NOT MODIFIED."
