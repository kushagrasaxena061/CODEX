from pydantic import BaseModel
from typing import Dict, Any, Optional

class AgentMessage(BaseModel):
    """Standardized communication format between specialized agents."""
    agent_name: str
    status: str           # e.g., "success", "failed", "working"
    message: str          # Human-readable explanation
    data: Optional[Dict[str, Any]] = None  # Structured data (files edited, test results)
