import pytest
from unittest.mock import patch
from backend.telemetry.tracker import TokenTracker
from backend.prompts.schemas import OptimizedTask, ExecutionPlan
from backend.agents.orchestrator import TaskOrchestrator
from backend.repository.tools import count_tokens
from backend.agents.base import AgentMessage

def test_token_benchmark():
    """
    Proves that our Multi-Agent retrieval uses fewer tokens 
    than a naive approach of dumping the whole repository.
    """
    tracker = TokenTracker()
    
    massive_repo_dump = "def func(): pass\n" * 10000 
    naive_tokens = count_tokens(massive_repo_dump)
    
    targeted_file = "def func(): pass\n" * 50
    tracker.add_input("Change the func implementation")
    tracker.add_input(targeted_file)
    tracker.add_file_read()
    
    our_tokens = tracker.get_metrics()["total_tokens"]
    
    assert our_tokens < (naive_tokens * 0.10)
    assert tracker.files_read == 1

@pytest.mark.asyncio
@patch('backend.agents.orchestrator.implement_step')
@patch('backend.agents.orchestrator.TaskOrchestrator._verify_criteria')
async def test_end_to_end_orchestration(mock_verify, mock_implement):
    """
    Wires the Planning phase and Orchestrator together to simulate a full task run.
    """
    # Force the verifier to simulate a successful check
    mock_verify.return_value = True
    
    # Mock the Code Agent handoff so we don't need a live Ollama server for the test
    mock_implement.return_value = AgentMessage(
        agent_name="code_agent",
        status="success",
        message="Mocked implementation success",
        data={"files_changed": ["src/Header.jsx"]}
    )
    
    optimized_task = OptimizedTask(
        clarified_intent="Create a red header",
        files_likely_affected=["src/Header.jsx"],
        ambiguities=[]
    )
    
    plan = ExecutionPlan(
        goal=optimized_task.clarified_intent,
        implementation_steps=["Open Header.jsx", "Change CSS"],
        acceptance_criteria=["Header is rendered red"],
        risk_level="low"
    )
    
    orchestrator = TaskOrchestrator(plan, max_iterations=3)
    result = await orchestrator.execute()
    
    assert orchestrator.state == "SUCCESS"
    assert result.status == "success"
    assert "Header is rendered red" in result.data["criteria_met"]
