import subprocess
import os
import logging
from backend.config.settings import settings

logger = logging.getLogger(__name__)

class GitManager:
    def __init__(self, repo_path: str = None):
        self.repo_path = repo_path or settings.WORKSPACE_ROOT
        self._init_if_needed()

    def _run(self, cmd: str) -> str:
        try:
            result = subprocess.run(cmd, cwd=self.repo_path, shell=True, capture_output=True, text=True)
            return result.stdout.strip()
        except Exception as e:
            logger.error(f"Git command failed: {e}")
            return ""

    def _init_if_needed(self):
        if not os.path.exists(os.path.join(self.repo_path, '.git')):
            self._run("git init")
            self._run("git config user.name 'Codex AI'")
            self._run("git config user.email 'codex@autonomous.local'")

    def commit(self, message: str) -> str:
        self._run("git add .")
        # Clean up message for CLI safely
        safe_msg = message.replace('"', "'")
        return self._run(f'git commit -m "{safe_msg}"')
        
    def get_log(self) -> str:
        return self._run("git log --oneline -n 3")
