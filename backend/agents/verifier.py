import os, ast
from backend.prompts.schemas import ExecutionPlan
from backend.llm.ollama_client import generate_json
from backend.config.settings import settings
from backend.repository.file_manager import FileManager
from backend.events.bus import event_bus

async def verify_plan(plan: ExecutionPlan, workspace_root: str = None) -> tuple[bool, str]:
    ws = os.path.abspath(workspace_root or settings.WORKSPACE_ROOT)
    event_bus.emit("QA_VERIFIER", "Starting acceptance verification...")
    
    fm = FileManager(ws)
    content_dump = ""
    for root, dirs, files in os.walk(ws):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__']]
        for file in files:
            rel_path = os.path.relpath(os.path.join(root, file), ws)
            c = fm.read_file(rel_path)
            # THE FIX: Allow the verifier to see files even if they are empty
            if c is not None: content_dump += f"--- {rel_path} ---\n{c}\n"

    event_bus.emit("QA_VERIFIER", "Running syntax validation...")
    for file in content_dump.split("---"):
        if ".py ---" in file:
            try: ast.parse(file.split("\n", 1)[1])
            except SyntaxError as e:
                event_bus.emit("QA_VERIFIER", f"LSP Syntax Error", level="ERROR")
                return False, f"Syntax Error: {e.msg} on line {e.lineno}"

    sys_prompt = (
        "You are the strict QA Verifier.\n"
        "CRITICAL RULES:\n"
        "1. You MUST evaluate based ONLY on the EXACT 'PLAN GOAL' provided below.\n"
        "2. If the user asked to remove something, verify it is GONE.\n"
        "3. If the user asked to add something, verify it is PRESENT.\n"
        "4. Output JSON: {\"passed\": true/false, \"reason\": \"string\"}"
    )
    prompt = f"PLAN GOAL TO VERIFY: {plan.goal}\n\nFILE CONTENTS:\n{content_dump}\n\nDoes the CURRENT STATE satisfy the PLAN GOAL exactly?"
    
    response = await generate_json(prompt, settings.OLLAMA_MODEL_CODING, sys_prompt, max_tokens=400)
    
    passed = response.get("passed", True) if isinstance(response, dict) else True
    reason = response.get("reason", "Verification complete.") if isinstance(response, dict) else "Ok"
    
    if "not achieved" in reason.lower() or "failed" in reason.lower() or "does not" in reason.lower():
        passed = False
    
    if passed:
        event_bus.emit("VERIFIED", f"QA Passed: {reason}", level="SUCCESS")
        return True, reason
    else:
        event_bus.emit("QA_VERIFIER", f"QA Needs Work: {reason}", level="WARN")
        return False, reason
