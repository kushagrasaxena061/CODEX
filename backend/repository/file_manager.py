import os, logging, shutil, subprocess
from backend.events.bus import event_bus

logger = logging.getLogger(__name__)

class FileManager:
    def __init__(self, workspace_root: str):
        self.workspace = os.path.abspath(workspace_root)
        os.makedirs(self.workspace, exist_ok=True)

    def _get_safe_path(self, rel_path: str) -> str:
        safe = os.path.abspath(os.path.join(self.workspace, rel_path))
        if not safe.startswith(self.workspace): raise ValueError("SECURITY LOCK: Path traversal detected")
        return safe

    def _sanitize(self, text) -> str:
        # THE FIX: If the AI sends an array of strings, join them properly first!
        if isinstance(text, list):
            text = "\n".join([str(x) for x in text])
            
        if not isinstance(text, str): 
            return ""
            
        for token in ["</think>", "<|endoftext|>", "<|im_end|>", "Human:", "Assistant:", "```python\n", "```json\n", "```\n", "```", "```python", "```json"]:
            text = text.replace(token, "")
        return text

    def read_file(self, rel_path: str):
        try:
            with open(self._get_safe_path(rel_path), 'r', encoding='utf-8') as f: return f.read()
        except Exception: return None

    def write_file(self, rel_path: str, code):
        path = self._get_safe_path(rel_path)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f: f.write(self._sanitize(code))
        event_bus.emit("FILE_IO", f"Wrote/Created '{rel_path}'", level="SUCCESS")

    def append_file(self, rel_path: str, code):
        path = self._get_safe_path(rel_path)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        clean_code = self._sanitize(code)
        with open(path, 'a', encoding='utf-8') as f:
            if clean_code:
                if not clean_code.startswith('\n'): f.write('\n')
                f.write(clean_code)
        event_bus.emit("FILE_IO", f"Appended code to '{rel_path}'", level="SUCCESS")

    def modify_file_diff(self, rel_path: str, search, replace) -> bool:
        path = self._get_safe_path(rel_path)
        if not os.path.exists(path): return False
        
        search = self._sanitize(search).strip('\r\n')
        replace = self._sanitize(replace)
        if not search.strip(): return False

        with open(path, 'r', encoding='utf-8') as f: content = f.read()

        if search in content:
            with open(path, 'w', encoding='utf-8') as f: f.write(content.replace(search, replace, 1))
            event_bus.emit("FILE_IO", f"Modified '{rel_path}' (Exact Match).", level="SUCCESS")
            return True

        search_lines = [l.strip() for l in search.splitlines() if l.strip()]
        content_lines = content.splitlines()

        if not search_lines: return False

        for i in range(len(content_lines) - len(search_lines) + 1):
            match = True
            for j in range(len(search_lines)):
                if search_lines[j] not in content_lines[i+j]:
                    match = False
                    break
            
            if match:
                prefix = "\n".join(content_lines[:i])
                suffix = "\n".join(content_lines[i+len(search_lines):])
                new_content = (prefix + "\n" if prefix else "") + replace + ("\n" + suffix if suffix else "")
                with open(path, 'w', encoding='utf-8') as f: f.write(new_content)
                event_bus.emit("FILE_IO", f"Modified '{rel_path}' (Forgiving Match).", level="SUCCESS")
                return True
                
        event_bus.emit("FILE_IO", f"Diff failed: Could not locate target code in '{rel_path}'.", level="ERROR")
        return False

    def rename_file(self, old_rel_path: str, new_rel_path: str) -> bool:
        old_path = self._get_safe_path(old_rel_path)
        new_path = self._get_safe_path(new_rel_path)
        if not os.path.exists(old_path): return False
        os.makedirs(os.path.dirname(new_path), exist_ok=True)
        os.rename(old_path, new_path)
        event_bus.emit("FILE_IO", f"Renamed '{old_rel_path}' to '{new_rel_path}'", level="SUCCESS")
        return True

    def delete_file(self, rel_path: str) -> bool:
        path = self._get_safe_path(rel_path)
        if os.path.exists(path):
            if os.path.isdir(path): shutil.rmtree(path)
            else: os.remove(path)
            event_bus.emit("FILE_IO", f"Deleted '{rel_path}'", level="WARN")
            return True
        return False

    def execute_terminal(self, command: str) -> str:
        event_bus.emit("TERMINAL", f"Running: {command}", level="INFO")
        try:
            env = os.environ.copy()
            env["GIT_TERMINAL_PROMPT"] = "0" 
            res = subprocess.run(command, cwd=self.workspace, shell=True, capture_output=True, text=True, timeout=120, env=env)
            out_str, err_str = res.stdout.strip(), res.stderr.strip()
            if res.returncode == 0:
                event_bus.emit("TERMINAL", f"Command success", level="SUCCESS")
                return out_str
            else:
                combined_err = f"{err_str} {out_str}".strip()
                event_bus.emit("TERMINAL", f"Command failed: {combined_err}", level="ERROR")
                return f"ERROR: {combined_err}"
        except Exception as e: return f"ERROR: {str(e)}"
