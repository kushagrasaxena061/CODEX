import logging
from pydantic import BaseModel, Field
from typing import List
from backend.llm.ollama_client import generate_json
from backend.config.settings import settings
from backend.repository.scanner import get_repo_tree
from backend.events.bus import event_bus
from backend.repository.rag_manager import rag_db

logger = logging.getLogger(__name__)

class ImplementationStep(BaseModel):
    agent_role: str = Field(default="Software Developer")
    instruction: str = Field(default="")

class AdvancedExecutionPlan(BaseModel):
    feature_already_exists: bool = Field(default=False)
    duplication_reason: str = Field(default="")
    goal: str = Field(default="")
    target_files: List[str] = Field(default_factory=list)
    implementation_steps: List[ImplementationStep] = Field(default_factory=list)

async def generate_plan(raw_prompt: str, history: str = "", session_id: int = 0, workspace_root: str = None) -> AdvancedExecutionPlan:
    ws = workspace_root or settings.WORKSPACE_ROOT
    event_bus.emit("ARCHITECT", f"Analyzing architecture for Session #{session_id}...")
    repo_tree = get_repo_tree(ws)
    rag_context = rag_db.query_code(raw_prompt, session_id)
    
    sys_prompt = (
        "You are DARWIN, a Lead Software Architect.\n"
        "Output ONLY JSON representing the execution plan.\n"
        "{\n"
        "  \"feature_already_exists\": false,\n"
        "  \"duplication_reason\": \"\",\n"
        "  \"goal\": \"string\",\n"
        "  \"target_files\": [\"string\"],\n"
        "  \"implementation_steps\": [{\"agent_role\": \"Software Developer\", \"instruction\": \"string\"}]\n"
        "}\n"
    )
    
    prompt = f"USER REQUEST: {raw_prompt}\n\nCURRENT REPO TREE:\n{repo_tree}\n\nRELEVANT CODE CONTEXT:\n{rag_context}"
    response = await generate_json(prompt, settings.OLLAMA_MODEL_PLANNING, sys_prompt, max_tokens=1500, timeout_sec=90)
    
    try: 
        plan = AdvancedExecutionPlan(**response)
        plan.goal = raw_prompt
    except Exception:
        plan = AdvancedExecutionPlan(feature_already_exists=False, goal=raw_prompt, target_files=[], implementation_steps=[ImplementationStep(agent_role="Software Developer", instruction=raw_prompt)])
    
    prompt_lower = raw_prompt.lower()
    action_keywords = ["add", "remove", "delete", "fix", "update", "modify", "change", "edit", "rename", "create", "write", "make", "generate", "build"]
    has_file_extension = any(ext in prompt_lower for ext in [".py", ".js", ".html", ".css", ".json", ".md", ".txt", ".sh"])
    
    if any(keyword in prompt_lower for keyword in action_keywords) or has_file_extension:
        plan.feature_already_exists = False
        plan.duplication_reason = ""
        
    # THE FIX: Prevent the "0 Steps" Infinite Loop!
    # If the LLM tried to reject the prompt and generated 0 steps, we MUST inject a 
    # fallback step here so the Code Agent actually executes the task.
    if not plan.feature_already_exists and not plan.implementation_steps:
        plan.implementation_steps = [ImplementationStep(agent_role="Software Developer", instruction=raw_prompt)]
    
    if plan.feature_already_exists:
        event_bus.emit("ARCHITECT", f"Feature already exists: {plan.duplication_reason}", level="WARN")
    else:
        event_bus.emit("PLANNER", f"Formulated {len(plan.implementation_steps)} step(s).", level="SUCCESS")
    return plan
