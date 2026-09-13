import pytest
import pytest_asyncio
import os
import asyncio
from pathlib import Path
from backend.git.manager import GitManager
from backend.execution.terminal import Terminal

@pytest_asyncio.fixture
async def git_workspace(tmp_path):
    """Creates a temporary actual Git repository for testing."""
    term = Terminal(str(tmp_path))
    
    # Initialize git repo and configure it so commits don't fail in CI
    await term.execute_command("git init")
    await term.execute_command("git config user.email 'test@codex.local'")
    await term.execute_command("git config user.name 'Codex Test'")
    
    # Create an initial commit
    (tmp_path / "baseline.txt").write_text("initial commit")
    await term.execute_command("git add .")
    await term.execute_command("git commit -m 'init'")
    
    return tmp_path

@pytest.mark.asyncio
async def test_snapshot_protects_user_changes(git_workspace):
    manager = GitManager(str(git_workspace))
    
    # Simulate the user making uncommitted changes BEFORE the AI starts
    (git_workspace / "user_work.txt").write_text("user was here")
    
    # AI takes a snapshot before starting its task
    snapshot = await manager.snapshot_pre_task_state()
    
    # Verify the snapshot successfully caught the user's file
    assert "user_work.txt" in snapshot["user_modified_files"]
    assert len(snapshot["head_commit"]) >= 7

@pytest.mark.asyncio
async def test_get_diff_and_commit(git_workspace):
    manager = GitManager(str(git_workspace))
    
    # Agent makes a change
    (git_workspace / "baseline.txt").write_text("agent modified this")
    
    # Check diff
    diff = await manager.get_diff()
    assert "agent modified this" in diff
    
    # Commit changes
    success = await manager.commit_changes("feat: agent update")
    assert success is True
    
    # Verify status is clean
    status = await manager.get_status()
    assert len(status) == 0
