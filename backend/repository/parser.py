import ast
from pathlib import Path

class PythonCodeIndexer:
    def __init__(self, workspace_root: str):
        self.workspace_root = Path(workspace_root).resolve()

    def index_file(self, relative_path: str) -> dict:
        """Parses a Python file and returns a summary of classes and functions."""
        target = (self.workspace_root / relative_path).resolve()
        if not target.exists() or not target.is_file():
            return {"error": "File not found"}

        try:
            with open(target, "r", encoding="utf-8") as f:
                source = f.read()
            
            tree = ast.parse(source)
            classes = []
            functions = []

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                    classes.append({"name": node.name, "methods": methods})
                elif isinstance(node, ast.FunctionDef):
                    # Only grab top-level functions (not methods inside classes)
                    # Note: ast.walk doesn't maintain hierarchy well, but this is a fast approximation
                    functions.append(node.name)

            # Deduplicate functions that were also counted as methods
            all_methods = set(m for c in classes for m in c["methods"])
            top_level_funcs = [f for f in functions if f not in all_methods]

            return {
                "path": relative_path,
                "classes": classes,
                "top_level_functions": top_level_funcs
            }
        except SyntaxError:
            return {"error": "SyntaxError - File cannot be parsed"}
        except Exception as e:
            return {"error": str(e)}
