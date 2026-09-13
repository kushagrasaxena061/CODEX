import pytest
from unittest.mock import patch
from backend.context.manager import ContextManager
from backend.prompts.schemas import OptimizedTask
from backend.prompts.optimizer import optimize_user_prompt, generate_execution_plan

def test_context_manager_truncation():
    cm = ContextManager(max_tokens=50) # Very small limit for testing
    system_inst = "System prompt."
    user_req = "Do a thing."
    
    # Create an artificially massive repo map
    huge_repo_map = "file.py\n" * 1000 
    
    result = cm.build_context(system_inst, user_req, huge_repo_map)
    
    # Ensure it truncated
    assert "[TRUNCATED FOR LENGTH]" in result
    assert len(result) < len(huge_repo_map)

@pytest.mark.asyncio
@patch('backend.prompts.optimizer.generate_json')
async def test_prompt_optimizer(mock_generate):
    # Mock the LLM JSON response
    mock_generate.return_value = {
        "clarified_intent": "Update the header component background color to red.",
        "files_likely_affected": ["src/components/Header.jsx"],
        "ambiguities": []
    }
    
    task = await optimize_user_prompt("Make header red", "src/components/Header.jsx")
    
    assert task.clarified_intent == "Update the header component background color to red."
    assert "src/components/Header.jsx" in task.files_likely_affected
    
@pytest.mark.asyncio
@patch('backend.prompts.optimizer.generate_json')
async def test_execution_planner(mock_generate):
    mock_generate.return_value = {
        "goal": "Update header",
        "implementation_steps": ["Locate Header.jsx", "Change CSS class"],
        "acceptance_criteria": ["Header background is #FF0000", "Component renders"],
        "risk_level": "low"
    }
    
    task = OptimizedTask(clarified_intent="Update header", files_likely_affected=[], ambiguities=[])
    plan = await generate_execution_plan(task)
    
    assert plan.risk_level == "low"
    assert "Component renders" in plan.acceptance_criteria
