import logging
import json
from backend.llm.ollama_client import generate_json
from backend.config.settings import settings
from backend.repository.file_manager import FileManager
from backend.events.bus import event_bus

logger = logging.getLogger(__name__)

def extract_operations(data):
    ops = []
    if isinstance(data, dict):
        file_key = data.get("file") or data.get("filename") or data.get("name") or data.get("path")
        code_key = data.get("code") or data.get("content") or data.get("text")
        action_val = str(data.get("action", "create")).lower()
        
        # THE FIX: Explicitly allow operations that don't need 'code' or 'search', like rename and delete!
        if file_key and (code_key is not None or data.get("search") is not None or data.get("new_name") or "rename" in action_val or "delete" in action_val or "remove" in action_val):
            ops.append({
                "action": action_val,
                "file": str(file_key),
                "code": code_key,
                "search": data.get("search"),
                "replace": data.get("replace", ""),
                "new_name": data.get("new_name", ""),
                "command": data.get("command", "")
            })
        elif "execute" in action_val and data.get("command"):
            ops.append({
                "action": "execute",
                "command": data.get("command")
            })
        else:
            for v in data.values():
                ops.extend(extract_operations(v))
    elif isinstance(data, list):
        for i in data:
            ops.extend(extract_operations(i))
    return ops

async def implement_step(instruction: str, role: str, files_context: dict, workspace_root: str, history: str):
    event_bus.emit("CODE_AGENT", f"[{role}] Synthesizing operations (CRUD + Terminal)...")
    
    # Git Push Bypass remains perfectly intact
    if "push to github" in instruction.lower() or "git push" in instruction.lower():
        operations = [{"action": "execute", "command": "git push origin HEAD"}]
        event_bus.emit("CODE_AGENT", "Bypassing LLM to execute hardcoded git push.", level="SUCCESS")
    else:
        context_str = "\n".join([f"--- {f} ---\n{c}" for f, c in files_context.items()])

        sys_prompt = (
            f"You are DARWIN, an elite autonomous AI.\n"
            "You MUST output valid JSON.\n"
            "ACTIONS AVAILABLE:\n"
            "1. 'create': Create NEW file. {\"action\": \"create\", \"file\": \"main.py\", \"code\": [\"print('hi')\"]}\n"
            "2. 'modify': Edit or DELETE. {\"action\": \"modify\", \"file\": \"main.py\", \"search\": [\"old\"], \"replace\": [\"new\"]}\n"
            "3. 'append': Add code to bottom. {\"action\": \"append\", \"file\": \"main.py\", \"code\": [\"print('end')\"]}\n"
            "4. 'rename': Rename a file. {\"action\": \"rename\", \"file\": \"old.py\", \"new_name\": \"new.py\"}\n"
            "5. 'execute': Run terminal commands. {\"action\": \"execute\", \"command\": \"npm install\"}\n"
        )
        
        prompt = f"HISTORY:\n{history}\n\nCURRENT FILES:\n{context_str}\n\nSTRICT INSTRUCTION TO EXECUTE: {instruction}"
        
        response = await generate_json(prompt, settings.OLLAMA_MODEL_CODING, sys_prompt, max_tokens=6000, timeout_sec=240)
        
        if "error" in response:
            event_bus.emit("CODE_AGENT", f"LLM JSON Error: {response['error']}", level="ERROR")
            return

        operations = extract_operations(response)

        if not operations:
            event_bus.emit("CODE_AGENT", f"CRITICAL ERROR: No file or code found in AI response. Dump: {str(response)[:100]}...", level="ERROR")
            return

    fm = FileManager(workspace_root)
    for op in operations:
        action = op.get("action", "create").lower()
        file_path = op.get("file")
        
        if "execute" in action:
            cmd = op.get("command")
            if cmd: fm.execute_terminal(cmd)
            continue
            
        if not file_path: continue
        
        if "delete" in action or "remove" in action: fm.delete_file(file_path)
        elif "rename" in action:
            new_name = op.get("new_name")
            if new_name: fm.rename_file(file_path, new_name)
            else: event_bus.emit("FILE_IO", "Missing 'new_name' for rename operation.", level="ERROR")
        elif "append" in action or "add" in action:
            fm.append_file(file_path, op.get("code", ""))
        elif "modify" in action or "edit" in action or "update" in action:
            search, replace = op.get("search"), op.get("replace", "")
            if search: fm.modify_file_diff(file_path, search, replace)
        else:
            code = op.get("code", "")
            if code is not None: fm.write_file(file_path, code)
            
    event_bus.emit("CODE_AGENT", "Operations execution completed.", level="INFO")
