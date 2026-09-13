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
