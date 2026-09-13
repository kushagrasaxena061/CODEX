import pytest
from unittest.mock import patch
from backend.agents.code import implement_step

@pytest.mark.asyncio
@patch('backend.agents.code.generate_json')
async def test_code_agent_implementation(mock_generate, tmp_path):
    # Mock LLM returning a valid Search/Replace block
    mock_generate.return_value = {
        "thought_process": "Updating header color to red.",
        "edits": [{
            "file_path": "header.css",
            "search_block": "color: blue;",
            "replace_block": "color: red;"
        }]
    }
    
    # Create a dummy file in the temp workspace
    workspace = tmp_path
    test_file = workspace / "header.css"
    test_file.write_text("body { color: blue; }")
    
    result = await implement_step("Make header red", {"header.css": "body { color: blue; }"}, str(workspace))
    
    assert result.status == "success"
    assert "header.css" in result.data["files_changed"]
    assert "color: red;" in test_file.read_text()
