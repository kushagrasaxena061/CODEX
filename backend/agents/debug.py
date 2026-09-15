import logging

logger = logging.getLogger(__name__)

async def generate_fix(error_reason: str, original_instruction: str) -> str:
    if "No file or code found" in error_reason:
        return (
            f"CRITICAL ERROR: Your previous JSON output did not contain a 'file' name or any 'code'.\n"
            f"You MUST include 'file': '<filename>' and 'code': ['<line1>'] in your JSON object.\n"
            f"Instruction to satisfy: {original_instruction}"
        )
        
    return (
        f"Your previous action resulted in an error:\n"
        f"-----\n{error_reason}\n-----\n\n"
        f"Please correct the issue to satisfy this instruction: {original_instruction}"
    )
