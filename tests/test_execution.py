import pytest
import asyncio
from backend.execution.terminal import Terminal
from backend.execution.process_manager import ProcessManager

@pytest.mark.asyncio
async def test_terminal_execute(tmp_path):
    term = Terminal(str(tmp_path))
    result = await term.execute_command("echo 'hello world'")
    assert result["exit_code"] == 0
    assert "hello world" in result["stdout"]

@pytest.mark.asyncio
async def test_terminal_timeout(tmp_path):
    term = Terminal(str(tmp_path))
    # Sleep for 3 seconds but timeout is 1 second
    result = await term.execute_command("sleep 3", timeout=1)
    assert result["exit_code"] == -1
    assert "timed out" in result["stderr"].lower()

@pytest.mark.asyncio
async def test_terminal_truncation(tmp_path):
    term = Terminal(str(tmp_path))
    # Generate ~10000 characters of output
    huge_output_command = "python3 -c \"print('A' * 10000)\""
    result = await term.execute_command(huge_output_command)
    
    # Assert the output was truncated strictly to the max length + the warning message length
    assert len(result["stdout"]) <= term.max_output_length + 100 
    assert "[OUTPUT TRUNCATED TO SAVE TOKENS]" in result["stdout"]

@pytest.mark.asyncio
async def test_process_manager(tmp_path):
    pm = ProcessManager(str(tmp_path))
    # Start a server simulation that just sleeps
    pid = await pm.start_background_process("test_server", "sleep 10")
    assert pid > 0
    
    # Stop it immediately
    stopped = pm.stop_process("test_server")
    assert stopped is True
