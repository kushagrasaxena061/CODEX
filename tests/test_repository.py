import pytest
import os
from pathlib import Path
from backend.repository.scanner import RepositoryScanner
from backend.repository.file_manager import FileManager

@pytest.fixture
def temp_workspace(tmp_path):
    # Setup mock workspace
    (tmp_path / "src").mkdir()
    (tmp_path / "node_modules").mkdir()
    
    (tmp_path / "src" / "main.py").write_text("print('hello')")
    (tmp_path / "node_modules" / "junk.js").write_text("console.log('junk')")
    (tmp_path / ".gitignore").write_text("node_modules/\n")
    
    return tmp_path

def test_scanner_ignores_files(temp_workspace):
    scanner = RepositoryScanner(str(temp_workspace))
    files = scanner.scan()
    assert "src/main.py" in files
    assert "node_modules/junk.js" not in files

@pytest.mark.asyncio
async def test_file_manager_sandboxing(temp_workspace):
    fm = FileManager(str(temp_workspace))
    with pytest.raises(PermissionError):
        await fm.read_file("../../../etc/passwd")

@pytest.mark.asyncio
async def test_file_manager_conflict_detection(temp_workspace):
    fm = FileManager(str(temp_workspace))
    
    # Read file to get current hash
    read_result = await fm.read_file("src/main.py")
    orig_hash = read_result["hash"]
    
    # Simulate a user editing the file in VS Code
    (temp_workspace / "src" / "main.py").write_text("print('changed by user')")
    
    # Agent tries to write with old hash
    with pytest.raises(ValueError, match="Conflict"):
        await fm.write_file("src/main.py", "print('agent edit')", expected_hash=orig_hash)
        
    # Write without expecting a hash (forced) or with correct hash works
    new_hash = fm._get_hash("print('changed by user')")
    result = await fm.write_file("src/main.py", "print('agent edit')", expected_hash=new_hash)
    assert result["status"] == "success"
