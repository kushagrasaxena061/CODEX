from pydantic import BaseModel, Field

class BugFix(BaseModel):
    root_cause_analysis: str = Field(..., description="Brief explanation of why it failed")
    file_to_modify: str = Field(..., description="Path to the file needing the fix")
    original_code: str = Field(..., description="The exact existing code to replace")
    fixed_code: str = Field(..., description="The corrected code")
