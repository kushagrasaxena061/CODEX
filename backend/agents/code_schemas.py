from pydantic import BaseModel, Field
from typing import List

class FileEdit(BaseModel):
    file_path: str = Field(..., description="Path to the file relative to workspace root")
    search_block: str = Field(..., description="The exact existing code block to replace.")
    replace_block: str = Field(..., description="The new code block to insert")

class CodeAction(BaseModel):
    thought_process: str = Field(..., description="Implementation strategy")
    edits: List[FileEdit] = Field(default=[], description="File modifications")
    commands: List[str] = Field(default=[], description="Terminal commands to run")
