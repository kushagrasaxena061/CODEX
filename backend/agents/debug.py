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
