import os
from backend.config.settings import settings

def get_repo_tree(root_dir: str = None) -> str:
    """Generates a token-efficient map of the repository."""
    root = root_dir or settings.WORKSPACE_ROOT
    tree = []
    ignore_dirs = {'.git', 'node_modules', '__pycache__', '.venv', 'dist', 'build'}
    
    for dirpath, dirnames, filenames in os.walk(root):
        # Modify dirnames in-place to ignore specific directories
        dirnames[:] = [d for d in dirnames if d not in ignore_dirs and not d.startswith('.')]
        
        level = dirpath.replace(root, '').count(os.sep)
        indent = ' ' * 4 * level
        folder_name = os.path.basename(dirpath)
        if folder_name:
            tree.append(f"{indent}{folder_name}/")
            
        subindent = ' ' * 4 * (level + 1)
        for f in filenames:
            if not f.startswith('.') and not f.endswith('.pyc'):
                tree.append(f"{subindent}{f}")
                
    # Return first 200 lines to protect LLM context window
    return "\n".join(tree[:200])
