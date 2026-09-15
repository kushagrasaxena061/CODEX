import os
from backend.config.settings import settings

def get_repo_tree(workspace_root: str = None) -> str:
    target_dir = os.path.abspath(workspace_root or settings.WORKSPACE_ROOT)
    if not os.path.exists(target_dir):
        return "Empty Directory"
    
    tree_lines = []
    for root, dirs, files in os.walk(target_dir):
        dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules', '.venv']]
        rel_path = os.path.relpath(root, target_dir)
        level = 0 if rel_path == "." else rel_path.count(os.sep) + 1
        indent = " " * 4 * level
        if rel_path != ".":
            tree_lines.append(f"{indent}{os.path.basename(root)}/")
        for f in files:
            if not f.startswith('.'):
                tree_lines.append(f"{indent}    {f}")
                
    return "\n".join(tree_lines) if tree_lines else "Empty Directory"
