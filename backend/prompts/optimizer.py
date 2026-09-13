from backend.llm.ollama_client import generate_json
from backend.config.settings import settings
from backend.prompts.schemas import OptimizedTask, ExecutionPlan

async def optimize_user_prompt(raw_prompt: str, repo_map: str = "") -> OptimizedTask:
    """Uses a fast model to translate user requests into technical tasks."""
    system_prompt = (
        "You are a Principal Software Architect. Analyze the user's request. "
        "Return a JSON object with: 'clarified_intent' (string), 'files_likely_affected' (list of strings), "
        "and 'ambiguities' (list of strings)."
    )
    
    prompt = f"USER REQUEST: {raw_prompt}\n\nREPOSITORY CONTEXT:\n{repo_map}"
    
    response = await generate_json(prompt, settings.OLLAMA_MODEL_FAST, system_prompt)
    
    # Graceful fallback if LLM fails formatting
    if "error" in response:
        return OptimizedTask(clarified_intent=raw_prompt, files_likely_affected=[], ambiguities=[])
        
    return OptimizedTask(**response)

async def generate_execution_plan(task: OptimizedTask) -> ExecutionPlan:
    """Generates a step-by-step plan with explicit acceptance criteria."""
    system_prompt = (
        "You are an AI Task Planner. Create an execution plan for the given task. "
        "Return a JSON object with: 'goal' (string), 'implementation_steps' (list of strings), "
        "'acceptance_criteria' (list of strictly verifiable strings), and 'risk_level' (string)."
    )
    
    prompt = f"TASK INTENT: {task.clarified_intent}"
    
    response = await generate_json(prompt, settings.OLLAMA_MODEL_PLANNING, system_prompt)
    
    if "error" in response:
        return ExecutionPlan(
            goal=task.clarified_intent,
            implementation_steps=["Analyze codebase", "Implement changes", "Verify"],
            acceptance_criteria=["Code runs without errors"],
            risk_level="low"
        )
        
    return ExecutionPlan(**response)
