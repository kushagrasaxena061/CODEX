import pytest
from pathlib import Path
import json
from backend.repository.env_detector import EnvironmentDetector
from backend.repository.parser import PythonCodeIndexer
from backend.repository.tools import count_tokens, check_file_exists

@pytest.fixture
def intelligence_workspace(tmp_path):
    # Setup mock JS project
    (tmp_path / "package.json").write_text(json.dumps({
        "dependencies": {"react": "^18.0.0", "next": "latest"}
    }))
    (tmp_path / "pnpm-lock.yaml").write_text("")
    
    # Setup mock Python file
    py_code = """
class MyServer:
    def start(self): pass
    def stop(self): pass

def utility_function():
    pass
    """
    (tmp_path / "server.py").write_text(py_code)
    
    return tmp_path

def test_environment_detector(intelligence_workspace):
    detector = EnvironmentDetector(str(intelligence_workspace))
    assert detector.detect_package_manager() == "pnpm"
    frameworks = detector.detect_frameworks()
    assert "React" in frameworks
    assert "Next.js" in frameworks

def test_python_indexer(intelligence_workspace):
    indexer = PythonCodeIndexer(str(intelligence_workspace))
    index = indexer.index_file("server.py")
    
    assert "error" not in index
    
    classes = [c["name"] for c in index["classes"]]
    assert "MyServer" in classes
    
    # Verify methods were captured
    server_class = next(c for c in index["classes"] if c["name"] == "MyServer")
    assert "start" in server_class["methods"]
    
    assert "utility_function" in index["top_level_functions"]

def test_deterministic_tools(intelligence_workspace):
    # Token counting test
    text = "def hello(): print('world')"
    tokens = count_tokens(text)
    assert tokens > 0 and tokens < 20 # Should be around 7-10 tokens
    
    # File existence test
    assert check_file_exists(intelligence_workspace, "server.py") is True
    assert check_file_exists(intelligence_workspace, "does_not_exist.py") is False
