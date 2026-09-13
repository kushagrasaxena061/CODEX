import logging
from backend.prompts.schemas import ExecutionPlan
from backend.llm.ollama_client import generate_json
from backend.config.settings import settings
from backend.repository.scanner import get_repo_tree

logger = logging.getLogger(__name__)

async def generate_plan(raw_prompt: str, history: str = "") -> ExecutionPlan:
    repo_tree = get_repo_tree()
    system_prompt = (
        "You are a highly adaptable Lead Software Architect. Analyze the user request and REPO TREE.\n"
        "You MUST output a JSON object EXACTLY matching this structure:\n"
        "{\n"
        "  \"goal\": \"string\",\n"
        "  \"target_files\": [\"string (Exact paths to create or edit)\"],\n"
        "  \"implementation_steps\": [\n"
        "       {\"agent_role\": \"string (e.g. Backend Engineer, Frontend Engineer)\", \"instruction\": \"string\"}\n"
        "  ],\n"
        "  \"acceptance_criteria\": [\"string\"],\n"
        "  \"risk_level\": \"low\"\n"
        "}\n"
        "CRITICAL RULES FOR AUTONOMY:\n"
        "1. ADAPT TO THE PROMPT: If the user asks to build or create something (like an app, frontend, or backend), you MUST plan the exact files to create and delegate them to agents. Do NOT just say the directory is empty.\n"
        "2. If the user explicitly asks to ONLY read or summarize the folder, and it is empty, then state it is empty.\n"
        "3. Assign specific tasks to specialized agents (e.g., let the Frontend Engineer write HTML/JS, and the Backend Engineer write Python)."
    )
    prompt = f"HISTORY:\n{history}\n\nUSER REQUEST: {raw_prompt}\n\nREPO TREE:\n{repo_tree}"
    response = await generate_json(prompt, settings.OLLAMA_MODEL_PLANNING, system_prompt)
    if "error" in response:
        raise Exception(f"Planner LLM failed: {response['error']}")
    return ExecutionPlan(**response)
