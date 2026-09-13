from pathlib import Path

def count_tokens(text: str, model_name: str = "cl100k_base") -> int:
    """
    Deterministically estimates tokens.
    Uses character length approximation (~4 chars per token) to ensure 
    100% local execution without external network downloads.
    """
    return max(1, len(text) // 4)

def check_file_exists(workspace_root: Path, relative_path: str) -> bool:
    """Deterministically checks if a file exists without LLM reasoning."""
    target = (workspace_root / relative_path).resolve()
    return target.exists() and target.is_relative_to(workspace_root)
