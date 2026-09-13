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
