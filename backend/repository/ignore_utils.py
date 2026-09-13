from pathlib import Path
import pathspec

def get_ignore_spec(workspace_root: Path) -> pathspec.PathSpec:
    """Generates a pathspec combining default safe-ignores with project .gitignore."""
    # Hardcoded safety boundaries (never send these to LLM)
    lines = [
        ".git/", "node_modules/", ".venv/", "venv/", "env/", 
        "__pycache__/", "*.pyc", "dist/", "build/", ".env",
        "*.jpg", "*.png", "*.mp4", "*.sqlite3", "*.db"
    ]
    
    gitignore_path = workspace_root / ".gitignore"
    if gitignore_path.exists():
        try:
            with open(gitignore_path, "r", encoding="utf-8") as f:
                lines.extend(f.readlines())
        except Exception:
            pass # Failsafe if gitignore is unreadable

    return pathspec.PathSpec.from_lines(pathspec.patterns.GitWildMatchPattern, lines)
