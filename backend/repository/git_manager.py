import os, subprocess, logging
from backend.events.bus import event_bus

logger = logging.getLogger(__name__)

class GitManager:
    def __init__(self, workspace_root: str):
        self.workspace = os.path.abspath(workspace_root)
        os.makedirs(self.workspace, exist_ok=True)
        self.codex_root = os.path.abspath(os.getcwd())
        
        if self.workspace == self.codex_root:
            raise ValueError("SECURITY LOCK: GitManager cannot operate on root application directory.")
            
    def _run(self, cmd: list) -> bool:
        try:
            subprocess.run(cmd, cwd=self.workspace, check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError as e:
            return False

    def init_repo(self):
        git_dir = os.path.join(self.workspace, ".git")
        if not os.path.exists(git_dir):
            self._run(["git", "init"])
            self._run(["git", "checkout", "-b", "main"])
            self._run(["git", "config", "user.email", "agent@darwin.workspace"])
            self._run(["git", "config", "user.name", "Darwin AI Agent"])
            
            with open(os.path.join(self.workspace, ".gitignore"), "w") as f:
                f.write("__pycache__/\n*.pyc\n.venv/\nnode_modules/\n.DS_Store\n")
                
            self._run(["git", "add", "."])
            self._run(["git", "commit", "-m", "Initial workspace baseline"])

    def set_remote(self, repo_url: str, token: str):
        auth_url = repo_url.replace("https://", f"https://{token}@") if "https://" in repo_url else repo_url
        subprocess.run(["git", "remote", "remove", "origin"], cwd=self.workspace, capture_output=True)
        self._run(["git", "remote", "add", "origin", auth_url])
        event_bus.emit("GIT", "Session GitHub remote updated.", level="SUCCESS")

    def create_checkpoint(self, message: str):
        self._run(["git", "add", "."])
        res = subprocess.run(["git", "status", "--porcelain"], cwd=self.workspace, capture_output=True, text=True)
        if res.stdout.strip():
            self._run(["git", "commit", "-m", message])
            event_bus.emit("GIT", f"Saved Git checkpoint: '{message}'", level="SUCCESS")

    def push(self):
        event_bus.emit("GIT", "Syncing with session remote repository...", level="INFO")
        
        # THE FIX: If the user connected a repo that already has files (like a README), 
        # pull the history first so it doesn't get blocked by Git.
        self._run(["git", "pull", "origin", "main", "--allow-unrelated-histories", "-m", "Auto-merge remote"])
        
        res = subprocess.run(["git", "push", "-u", "origin", "main"], cwd=self.workspace, capture_output=True, text=True)
        
        if res.returncode == 0:
            event_bus.emit("GIT", "Successfully pushed to GitHub repository.", level="SUCCESS")
        else:
            # Absolute Fallback: AI forcefully claims the repo to ensure code is delivered
            force_res = subprocess.run(["git", "push", "-u", "origin", "main", "--force"], cwd=self.workspace, capture_output=True, text=True)
            if force_res.returncode == 0:
                event_bus.emit("GIT", "Successfully force-pushed to GitHub repository.", level="SUCCESS")
            else:
                event_bus.emit("GIT", f"GitHub Push Notice: Check branch/permissions.", level="WARN")

    def rollback(self):
        event_bus.emit("GIT", "Rolling back uncommitted workspace modifications...", level="ERROR")
        self._run(["git", "reset", "--hard", "HEAD"])
        self._run(["git", "clean", "-fd"])
        event_bus.emit("GIT", "Workspace restored to last approved checkpoint.", level="SUCCESS")
