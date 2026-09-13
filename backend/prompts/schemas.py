from pydantic import BaseModel, Field
from typing import List

class OptimizedTask(BaseModel):
    clarified_intent: str
    files_likely_affected: List[str]
    ambiguities: List[str]

class ExecutionPlan(BaseModel):
    goal: str = Field(..., description="The main objective of the task")
    target_files: List[str] = Field(default=[], description="Exact paths of files to read, create, or edit")
    implementation_steps: List[str] = Field(..., description="Step by step instructions for the code agent")
    acceptance_criteria: List[str] = Field(..., description="How to verify success")
    risk_level: str = Field(default="low")
