import pytest
from unittest.mock import patch, AsyncMock
from backend.execution.browser import BrowserAgent
from backend.agents.debug import diagnose_and_fix

@pytest.mark.asyncio
@patch("backend.execution.browser.async_playwright")
async def test_browser_verification(mock_playwright, tmp_path):
    """Mock the browser to test the logic without opening an actual Chromium window."""
    # Setup mock architecture
    mock_browser = AsyncMock()
    mock_page = AsyncMock()
    mock_page.content.return_value = "<html><body><h1>Welcome to Codex</h1></body></html>"
    
    mock_browser.new_page.return_value = mock_page
    mock_context = AsyncMock()
    mock_context.chromium.launch.return_value = mock_browser
    
    # Configure context manager mock
    mock_playwright.return_value.__aenter__.return_value = mock_context

    agent = BrowserAgent(str(tmp_path))
    result = await agent.verify_page(
        url="http://127.0.0.1:3000", 
        expected_text="Welcome to Codex",
        screenshot_name="test_shot"
    )
    
    assert result["status"] == "success"
    assert result["text_found"] is True
    assert result["screenshot_path"] is not None
    assert "test_shot.png" in result["screenshot_path"]

@pytest.mark.asyncio
@patch('backend.agents.debug.generate_json')
async def test_debug_agent_fix(mock_generate):
    """Test that the Debug Agent parses the error and proposes a valid BugFix."""
    mock_generate.return_value = {
        "root_cause_analysis": "Missing colon at the end of the if statement.",
        "file_to_modify": "main.py",
        "original_code": "if x == 1\n    print(x)",
        "fixed_code": "if x == 1:\n    print(x)"
    }
    
    error_log = "SyntaxError: expected ':'"
    file_content = "if x == 1\n    print(x)"
    
    message = await diagnose_and_fix(error_log, file_content, "main.py")
    
    assert message.status == "success"
    assert message.data["fix"]["fixed_code"] == "if x == 1:\n    print(x)"
