from pydantic import BaseModel, Field
from typing import List

class TaskStep(BaseModel):
    agent_role: str = Field(..., description="The specialized agent (e.g., 'Frontend Developer', 'Backend Developer')")
    instruction: str = Field(..., description="What this specific agent needs to do")

class ExecutionPlan(BaseModel):
    goal: str
    target_files: List[str]
    implementation_steps: List[TaskStep] = Field(..., description="List of steps assigned to specialized agents")
    acceptance_criteria: List[str]
    risk_level: str = "low"
