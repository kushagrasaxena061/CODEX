import logging
from backend.agents.base import AgentMessage
from backend.agents.code_schemas import CodeAction
from backend.llm.ollama_client import generate_json
from backend.config.settings import settings
from backend.repository.file_manager import FileManager
from backend.execution.terminal import Terminal

logger = logging.getLogger(__name__)

async def implement_step(step_description: str, files_context: dict, workspace_root: str, history: str = "") -> AgentMessage:
    system_prompt = (
        "You are an Expert AI Software Engineer.\n"
        "You MUST output a JSON object EXACTLY matching this structure:\n"
        "{\n"
        "  \"thought_process\": \"string\",\n"
        "  \"edits\": [{\"file_path\": \"string\", \"search_block\": \"string\", \"replace_block\": \"string\"}],\n"
        "  \"commands\": [\"string\"]\n"
        "}\n"
    )
    
    context_str = "\n".join([f"--- {path} ---\n{content}" for path, content in files_context.items()])
    prompt = f"HISTORY:\n{history}\n\nTASK: {step_description}\n\nFILES:\n{context_str}"
    
    response = await generate_json(prompt, settings.OLLAMA_MODEL_CODING, system_prompt)
    
    if "error" in response:
        return AgentMessage(agent_name="code_agent", status="failed", message=response["error"])
        
    try:
        action = CodeAction(**response)
        fm = FileManager(workspace_root)
        term = Terminal(workspace_root)
        
        applied_edits = []
        for edit in action.edits:
            try:
                current_content = fm.read_file(edit.file_path)
                if not current_content or not edit.search_block:
                    fm.write_file(edit.file_path, edit.replace_block)
                    applied_edits.append(edit.file_path)
                elif edit.search_block in current_content:
                    new_content = current_content.replace(edit.search_block, edit.replace_block)
                    fm.write_file(edit.file_path, new_content)
                    applied_edits.append(edit.file_path)
            except Exception as e:
                pass
                
        cmd_logs = []
        for cmd in action.commands:
            res = await term.run(cmd)
            cmd_logs.append(f"$ {cmd}\nEXIT CODE: {res['exit_code']}\nSTDOUT: {res['stdout']}")
            
        return AgentMessage(
            agent_name="code_agent", status="success",
            message=action.thought_process, data={"files_changed": applied_edits, "terminal_logs": cmd_logs}
        )
    except Exception as e:
        return AgentMessage(agent_name="code_agent", status="failed", message=f"Parse Error: {e}")
