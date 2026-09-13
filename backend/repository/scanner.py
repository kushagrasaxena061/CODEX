import os
from backend.config.settings import settings

def get_repo_tree(root_dir: str = None) -> str:
    root = root_dir or settings.WORKSPACE_ROOT
    tree = []
    ignore_dirs = {'.git', 'node_modules', '__pycache__', '.venv', 'dist', 'build'}
    
    if not os.path.exists(root):
        return "(Directory does not exist yet)"
        
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in ignore_dirs and not d.startswith('.')]
        level = dirpath.replace(root, '').count(os.sep)
        indent = ' ' * 4 * level
        folder_name = os.path.basename(dirpath)
        
        # Don't print the root folder name itself
        if folder_name and folder_name != os.path.basename(root):
            tree.append(f"{indent}{folder_name}/")
            
        subindent = ' ' * 4 * (level + 1) if folder_name != os.path.basename(root) else ''
        for f in filenames:
            if not f.startswith('.') and not f.endswith('.pyc'):
                tree.append(f"{subindent}{f}")
                
    if not tree:
        return "(Empty Directory - No files present)"
        
    return "\n".join(tree[:200])
