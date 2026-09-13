import os
import logging

logger = logging.getLogger(__name__)

class FileManager:
    def __init__(self, root_dir: str):
        self.root = os.path.abspath(root_dir)

    def _safe_path(self, path: str) -> str:
        # Strip leading slashes so os.path.join doesn't jump to the OS root
        return os.path.join(self.root, path.lstrip('/\\'))

    def read_file(self, path: str) -> str:
        full_path = self._safe_path(path)
        if not os.path.exists(full_path):
            return ""
        with open(full_path, 'r', encoding='utf-8') as f:
            return f.read()

    def write_file(self, path: str, content: str):
        full_path = self._safe_path(path)
        os.makedirs(os.path.dirname(full_path) or '.', exist_ok=True)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
