import json
from pathlib import Path

class EnvironmentDetector:
    def __init__(self, workspace_root: str):
        self.workspace_root = Path(workspace_root).resolve()

    def detect_package_manager(self) -> str:
        """Deterministically identifies the package manager based on lockfiles."""
        if (self.workspace_root / "pnpm-lock.yaml").exists(): return "pnpm"
        if (self.workspace_root / "yarn.lock").exists(): return "yarn"
        if (self.workspace_root / "bun.lockb").exists(): return "bun"
        if (self.workspace_root / "package-lock.json").exists(): return "npm"
        if (self.workspace_root / "uv.lock").exists(): return "uv"
        if (self.workspace_root / "poetry.lock").exists(): return "poetry"
        if (self.workspace_root / "Pipfile.lock").exists(): return "pipenv"
        if (self.workspace_root / "requirements.txt").exists(): return "pip"
        return "unknown"

    def detect_frameworks(self) -> list:
        """Scans dependency files to identify key frameworks."""
        frameworks = []
        
        # Check Node.js frameworks
        pkg_json = self.workspace_root / "package.json"
        if pkg_json.exists():
            try:
                with open(pkg_json, "r") as f:
                    data = json.load(f)
                    deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
                    if "react" in deps: frameworks.append("React")
                    if "next" in deps: frameworks.append("Next.js")
                    if "vue" in deps: frameworks.append("Vue")
                    if "express" in deps: frameworks.append("Express")
            except Exception:
                pass

        # Check Python frameworks
        req_txt = self.workspace_root / "requirements.txt"
        if req_txt.exists():
            try:
                with open(req_txt, "r") as f:
                    content = f.read().lower()
                    if "fastapi" in content: frameworks.append("FastAPI")
                    if "django" in content: frameworks.append("Django")
                    if "flask" in content: frameworks.append("Flask")
            except Exception:
                pass

        return frameworks
