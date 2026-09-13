import pytest
from unittest.mock import patch
from backend.prompts.schemas import ExecutionPlan
from backend.agents.orchestrator import TaskOrchestrator
from backend.agents.base import AgentMessage

@pytest.mark.asyncio
@patch('backend.agents.orchestrator.implement_step')
async def test_orchestrator_state_machine(mock_implement):
    # Mock the Code Agent handoff
    mock_implement.return_value = AgentMessage(
        agent_name="code_agent",
        status="success",
        message="Mocked implementation success",
        data={"files_changed": ["Header.jsx"]}
    )
    
    plan = ExecutionPlan(
        goal="Change header color to red",
        implementation_steps=["Open Header.jsx", "Change CSS"],
        acceptance_criteria=["Header background is #FF0000"],
        risk_level="low"
    )
    
    orchestrator = TaskOrchestrator(plan)
    assert orchestrator.state == "PLANNED"
    
    # Run the orchestrator
    result = await orchestrator.execute()
    
    # Verify strict state transitions and No False "Done" rule
    assert orchestrator.state == "SUCCESS"
    assert result.status == "success"
    assert "criteria_met" in result.data

@pytest.mark.asyncio
@patch('backend.agents.orchestrator.implement_step')
async def test_orchestrator_no_false_done(mock_implement):
    # Mock the Code Agent handoff
    mock_implement.return_value = AgentMessage(
        agent_name="code_agent",
        status="success",
        message="Mocked implementation success",
        data={"files_changed": []}
    )
    
    # If a plan has no verifiable criteria, it must fail.
    plan = ExecutionPlan(
        goal="Do something vague",
        implementation_steps=["Guess what to do"],
        acceptance_criteria=[], # Empty criteria!
        risk_level="high"
    )
    
    orchestrator = TaskOrchestrator(plan, max_iterations=2)
    result = await orchestrator.execute()
    
    # The orchestrator should hit its max iterations trying to verify and eventually fail
    assert orchestrator.state == "FAILED"
    assert result.status == "failed"
